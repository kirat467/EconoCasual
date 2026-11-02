"""Propensity score matching for EconoCausal (Week 2, Member 2).

Goal (from the brief): "balance historical observational data, simulating a
randomized A/B test without actually running one."

Idea
  Discounts were not random, so discounted and non-discounted customers differ.
  The PROPENSITY SCORE e(X) = P(discount | X) summarises how likely each customer
  was to be discounted. Customers with similar e(X) but different treatment are
  comparable "as if" randomised, so we match each discounted customer to a
  non-discounted lookalike and compare outcomes.

Pipeline
  1. Fit a propensity model (logistic regression on polynomial features).
  2. Check OVERLAP (common support) and trim customers with no comparable partner.
  3. Match 1:1 on the logit of the score, with replacement, inside a CALIPER
     (0.2 x SD of the logit, Austin 2011).
  4. Check BALANCE with standardized mean differences (SMD) before vs after.
     |SMD| < 0.1 is the usual "balanced" threshold.
  5. Estimate the effect on the treated (ATT) and compare it with the truth,
     which we know because the data is synthetic.

We compare the $10 discount against no discount (rows with a $20 discount are
left out so that the treatment is binary). Run from the repo root:
    python backend/propensity.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import NearestNeighbors
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler

ROOT = Path(__file__).resolve().parent.parent
COVARIATES = ["previous_purchases", "engagement", "price_sensitivity", "age"]


def smd(df, col, treated, weights=None, ref_sd=None):
    """Standardized mean difference (treated minus control).

    `ref_sd` lets us use the same denominator before and after matching, so the
    two numbers are comparable.
    """
    w = np.ones(len(df)) if weights is None else np.asarray(weights, float)
    t = np.asarray(treated, bool)
    x = df[col].values.astype(float)
    mean_t = np.average(x[t], weights=w[t])
    mean_c = np.average(x[~t], weights=w[~t])
    if ref_sd is None:
        ref_sd = np.sqrt((x[t].var(ddof=1) + x[~t].var(ddof=1)) / 2)
    return (mean_t - mean_c) / ref_sd


def fit_propensity(df, treated):
    model = make_pipeline(
        StandardScaler(),
        PolynomialFeatures(2, include_bias=False),
        StandardScaler(),
        LogisticRegression(C=1.0, max_iter=2000),
    )
    model.fit(df[COVARIATES], treated)
    return np.clip(model.predict_proba(df[COVARIATES])[:, 1], 1e-4, 1 - 1e-4)


def match(logit_ps, treated, caliper):
    """1:1 nearest-neighbour matching with replacement inside a caliper."""
    t_idx = np.where(treated)[0]
    c_idx = np.where(~treated)[0]
    nn = NearestNeighbors(n_neighbors=1).fit(logit_ps[c_idx].reshape(-1, 1))
    dist, pos = nn.kneighbors(logit_ps[t_idx].reshape(-1, 1))
    keep = dist[:, 0] <= caliper
    return t_idx[keep], c_idx[pos[keep, 0]]


def main():
    full = pd.read_csv(ROOT / "data" / "customers_causal.csv")
    df = full[full.discount.isin([0, 10])].reset_index(drop=True)
    treated = (df.discount == 10).values
    y = df.purchase.values.astype(float)
    print(f"Comparing $10 discount vs none: {treated.sum()} treated, {(~treated).sum()} controls\n")

    # 1-2. propensity score and overlap
    ps = fit_propensity(df, treated)
    logit_ps = np.log(ps / (1 - ps))
    print("Propensity score range:  treated "
          f"[{ps[treated].min():.2f}, {ps[treated].max():.2f}]  |  controls "
          f"[{ps[~treated].min():.2f}, {ps[~treated].max():.2f}]")

    # 3. matching
    caliper = 0.2 * logit_ps.std()
    t_idx, c_idx = match(logit_ps, treated, caliper)
    dropped = treated.sum() - len(t_idx)
    print(f"Matched {len(t_idx)} of {treated.sum()} treated customers "
          f"(dropped {dropped} outside the caliper); "
          f"{len(np.unique(c_idx))} distinct controls used\n")

    # 4. balance, measured with the SAME reference SD before and after
    weights = np.zeros(len(df))
    np.add.at(weights, c_idx, 1.0)       # controls: how many times each was used
    weights[t_idx] = 1.0                 # matched treated units
    in_sample = weights > 0
    rows = []
    for col in COVARIATES:
        ref_sd = np.sqrt((df.loc[treated, col].var(ddof=1) + df.loc[~treated, col].var(ddof=1)) / 2)
        before = smd(df, col, treated, ref_sd=ref_sd)
        after = smd(df[in_sample], col, treated[in_sample], weights[in_sample], ref_sd=ref_sd)
        rows.append({"covariate": col, "SMD before": before, "SMD after": after})
    balance = pd.DataFrame(rows).set_index("covariate").round(3)
    balance["balanced (<0.1)?"] = np.where(balance["SMD after"].abs() < 0.1, "yes", "NO")
    print("Covariate balance (standardized mean difference, treated - control):")
    print(balance.to_string(), "\n")

    # 5. effect on the treated (ATT)
    pair_diff = y[t_idx] - y[c_idx]
    att = pair_diff.mean()
    rng = np.random.default_rng(0)
    boots = [rng.choice(pair_diff, len(pair_diff)).mean() for _ in range(1000)]
    lo, hi = np.percentile(boots, [2.5, 97.5])
    naive = y[treated].mean() - y[~treated].mean()
    true_att = df.loc[t_idx, "true_ite_10"].mean()
    true_att_all = df.loc[treated, "true_ite_10"].mean()

    # IPW (ATT weights) as a cross-check: controls weighted by e/(1-e)
    ipw_w = np.where(treated, 1.0, ps / (1 - ps))
    ipw_att = np.average(y[treated]) - np.average(y[~treated], weights=ipw_w[~treated])

    result = pd.DataFrame({
        "estimate": [naive, att, ipw_att, true_att],
    }, index=["Naive difference", "Matched ATT", "IPW ATT (cross-check)",
              "TRUE ATT (matched treated)"]).round(3)
    print("Effect of a $10 discount on purchase probability, for discounted customers:")
    print(result.to_string())
    print(f"\nPair-bootstrap interval for matched ATT: [{lo:+.3f}, {hi:+.3f}]  "
          "(ignores uncertainty from fitting the propensity model)")
    print(f"True ATT over ALL treated customers: {true_att_all:+.3f}")

    # Honest uncertainty: bootstrap the WHOLE pipeline (refit propensity, rematch,
    # reweight) on resampled customers.
    def pipeline(sample):
        t = (sample.discount == 10).values
        yy = sample.purchase.values.astype(float)
        e = fit_propensity(sample, t)
        lg = np.log(e / (1 - e))
        ti, ci = match(lg, t, 0.2 * lg.std())
        w = np.where(t, 1.0, e / (1 - e))
        return (yy[ti] - yy[ci]).mean(), yy[t].mean() - np.average(yy[~t], weights=w[~t])

    n_boot = 200
    brng = np.random.default_rng(1)
    boot = np.array([pipeline(df.iloc[brng.integers(0, len(df), len(df))]) for _ in range(n_boot)])
    print(f"\nFull-pipeline bootstrap ({n_boot} resamples):")
    for name, col in [("Matched ATT", 0), ("IPW ATT", 1)]:
        l, h = np.percentile(boot[:, col], [2.5, 97.5])
        print(f"  {name:12s} SE = {boot[:, col].std():.3f}   95% interval [{l:+.3f}, {h:+.3f}]   "
              f"covers true ATT ({true_att_all:+.3f}): {l <= true_att_all <= h}")

    # Figures for the report / viva (skipped quietly if matplotlib is missing)
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig_dir = ROOT / "backend" / "figures"
        fig_dir.mkdir(exist_ok=True)

        fig, ax = plt.subplots(figsize=(6, 3.5))
        ax.hist(ps[treated], bins=30, alpha=0.6, label="discounted ($10)", density=True)
        ax.hist(ps[~treated], bins=30, alpha=0.6, label="no discount", density=True)
        ax.set_xlabel("propensity score"); ax.set_ylabel("density")
        ax.set_title("Overlap of propensity scores"); ax.legend()
        fig.tight_layout(); fig.savefig(fig_dir / "propensity_overlap.png", dpi=150); plt.close(fig)

        fig, ax = plt.subplots(figsize=(6, 3.2))
        y_pos = np.arange(len(balance))
        ax.scatter(balance["SMD before"], y_pos, label="before matching", marker="o")
        ax.scatter(balance["SMD after"], y_pos, label="after matching", marker="s")
        ax.axvline(0, color="grey", lw=0.8)
        for v in (-0.1, 0.1):
            ax.axvline(v, color="red", ls="--", lw=0.8)
        ax.set_yticks(y_pos); ax.set_yticklabels(balance.index)
        ax.set_xlabel("standardized mean difference"); ax.set_title("Covariate balance")
        ax.legend(); fig.tight_layout()
        fig.savefig(fig_dir / "balance_love_plot.png", dpi=150); plt.close(fig)
        print("\nSaved figures to backend/figures/")
    except Exception as exc:
        print("\nFigures skipped:", exc)


if __name__ == "__main__":
    main()
