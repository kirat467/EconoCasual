"""
propensity.py - Propensity score matching (PSM) + IPW with balance checks.

EconoCausal, Week 1/2 deliverable: balance historical observational data so it
behaves like a randomized A/B test, before / alongside Double ML.

Treatment : discount > 0 (binary, configurable)
Outcome   : purchase (0/1)
Covariates: previous_purchases, engagement (add more in COVARIATES)

Usage
-----
    python propensity.py                      # synthetic data (known true effect)
    python propensity.py --data ../data/customers.csv
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

COVARIATES = ["previous_purchases", "engagement"]
TREATMENT = "discount"
OUTCOME = "purchase"
SMD_THRESHOLD = 0.1  # |standardized mean difference| < 0.1 = well balanced


# --------------------------------------------------------------------------- #
# Data
# --------------------------------------------------------------------------- #
def make_synthetic(n: int = 5000, true_effect: float = 0.15, seed: int = 0) -> pd.DataFrame:
    """Confounded synthetic data: engaged / loyal customers are MORE likely to be
    offered a discount AND more likely to buy, so a naive comparison is biased."""
    rng = np.random.default_rng(seed)
    prev = rng.poisson(3, n).astype(float)
    eng = rng.normal(0, 1, n)
    p_treat = 1 / (1 + np.exp(-(0.6 * eng + 0.25 * (prev - 3))))
    t = rng.binomial(1, p_treat)
    base = 1 / (1 + np.exp(-(-0.3 + 0.9 * eng + 0.2 * (prev - 3))))
    # heterogeneous effect: low-engagement customers respond most to a discount
    effect = true_effect * (1 - 0.8 * np.tanh(eng))
    p_buy = np.clip(base + effect * t, 0, 1)
    y = rng.binomial(1, p_buy)
    df = pd.DataFrame(
        {
            "customer_id": np.arange(1, n + 1),
            "previous_purchases": prev,
            "engagement": eng,
            "discount": t * 10.0,
            "purchase": y,
        }
    )
    df.attrs["true_effect"] = float(effect.mean())  # average true ITE
    return df


def load_data(path: str | None) -> pd.DataFrame:
    if path is None:
        return make_synthetic()
    df = pd.read_csv(path)
    missing = {TREATMENT, OUTCOME, *COVARIATES} - set(df.columns)
    if missing:
        raise ValueError(f"CSV is missing columns: {sorted(missing)}")
    return df


# --------------------------------------------------------------------------- #
# Propensity model
# --------------------------------------------------------------------------- #
def fit_propensity(df: pd.DataFrame, covariates=COVARIATES) -> np.ndarray:
    """Return clipped P(treated | X) for every row."""
    X = StandardScaler().fit_transform(df[covariates].to_numpy(float))
    t = (df[TREATMENT] > 0).astype(int).to_numpy()
    model = LogisticRegression(max_iter=1000).fit(X, t)
    return np.clip(model.predict_proba(X)[:, 1], 1e-3, 1 - 1e-3)


def _logit(p):
    return np.log(p / (1 - p))


# --------------------------------------------------------------------------- #
# Balance diagnostics
# --------------------------------------------------------------------------- #
def smd(x: np.ndarray, t: np.ndarray, w: np.ndarray | None = None) -> float:
    """Standardized mean difference (weighted if w given)."""
    w = np.ones_like(x, dtype=float) if w is None else w
    m1 = np.average(x[t == 1], weights=w[t == 1])
    m0 = np.average(x[t == 0], weights=w[t == 0])
    v1 = np.average((x[t == 1] - m1) ** 2, weights=w[t == 1])
    v0 = np.average((x[t == 0] - m0) ** 2, weights=w[t == 0])
    pooled = np.sqrt((v1 + v0) / 2)
    return float((m1 - m0) / pooled) if pooled > 0 else 0.0


def balance_table(df, t, w_match=None, w_ipw=None, covariates=COVARIATES) -> pd.DataFrame:
    rows = []
    for c in covariates:
        x = df[c].to_numpy(float)
        row = {"covariate": c, "smd_raw": smd(x, t)}
        if w_match is not None:
            row["smd_matched"] = smd(x, t, w_match)
        if w_ipw is not None:
            row["smd_ipw"] = smd(x, t, w_ipw)
        rows.append(row)
    out = pd.DataFrame(rows)
    for col in [c for c in out.columns if c.startswith("smd_")]:
        out[col.replace("smd_", "ok_")] = out[col].abs() < SMD_THRESHOLD
    return out


# --------------------------------------------------------------------------- #
# Matching (1:1 nearest neighbour on logit PS, caliper, with replacement) -> ATT
# --------------------------------------------------------------------------- #
@dataclass
class MatchResult:
    att: float
    n_treated: int
    n_matched: int
    caliper: float
    weights: np.ndarray  # frequency weights of each row in the matched sample


def match_att(df: pd.DataFrame, ps: np.ndarray, caliper_sd: float = 0.2) -> MatchResult:
    t = (df[TREATMENT] > 0).to_numpy()
    y = df[OUTCOME].to_numpy(float)
    lp = _logit(ps)
    caliper = caliper_sd * lp.std()

    treated_idx = np.where(t)[0]
    control_idx = np.where(~t)[0]
    order = np.argsort(lp[control_idx])
    c_sorted_lp = lp[control_idx][order]
    c_sorted_idx = control_idx[order]

    weights = np.zeros(len(df))
    diffs = []
    for i in treated_idx:
        pos = np.searchsorted(c_sorted_lp, lp[i])
        cands = [p for p in (pos - 1, pos) if 0 <= p < len(c_sorted_lp)]
        best = min(cands, key=lambda p: abs(c_sorted_lp[p] - lp[i]))
        if abs(c_sorted_lp[best] - lp[i]) <= caliper:
            j = c_sorted_idx[best]
            diffs.append(y[i] - y[j])
            weights[i] += 1
            weights[j] += 1
    att = float(np.mean(diffs)) if diffs else float("nan")
    return MatchResult(att, len(treated_idx), len(diffs), float(caliper), weights)


# --------------------------------------------------------------------------- #
# IPW (stabilized, trimmed) -> ATE
# --------------------------------------------------------------------------- #
def ipw_ate(df: pd.DataFrame, ps: np.ndarray, trim=(0.02, 0.98)):
    t = (df[TREATMENT] > 0).to_numpy().astype(int)
    y = df[OUTCOME].to_numpy(float)
    keep = (ps > trim[0]) & (ps < trim[1])
    w = np.where(t == 1, t.mean() / ps, (1 - t.mean()) / (1 - ps)) * keep
    mu1 = np.sum(w[t == 1] * y[t == 1]) / np.sum(w[t == 1])
    mu0 = np.sum(w[t == 0] * y[t == 0]) / np.sum(w[t == 0])
    return float(mu1 - mu0), w


# --------------------------------------------------------------------------- #
# Full-pipeline bootstrap (re-fits the PS model inside every resample)
# --------------------------------------------------------------------------- #
def bootstrap(df: pd.DataFrame, n_boot: int = 200, seed: int = 0):
    rng = np.random.default_rng(seed)
    att, ate = [], []
    for _ in range(n_boot):
        s = df.iloc[rng.integers(0, len(df), len(df))].reset_index(drop=True)
        ps = fit_propensity(s)
        att.append(match_att(s, ps).att)
        ate.append(ipw_ate(s, ps)[0])
    ci = lambda a: [float(np.nanpercentile(a, 2.5)), float(np.nanpercentile(a, 97.5))]
    return {"att_ci95": ci(att), "ipw_ate_ci95": ci(ate)}


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def run(df: pd.DataFrame, n_boot: int = 200) -> dict:
    t = (df[TREATMENT] > 0).to_numpy().astype(int)
    y = df[OUTCOME].to_numpy(float)
    naive = float(y[t == 1].mean() - y[t == 0].mean())

    ps = fit_propensity(df)
    m = match_att(df, ps)
    ate, w_ipw = ipw_ate(df, ps)
    bal = balance_table(df, t, w_match=m.weights, w_ipw=w_ipw)
    ci = bootstrap(df, n_boot=n_boot)

    result = {
        "n": int(len(df)),
        "n_treated": int(t.sum()),
        "naive_difference": naive,
        "matching_att": m.att,
        "matching_att_ci95": ci["att_ci95"],
        "matched_treated": m.n_matched,
        "caliper_logit": m.caliper,
        "ipw_ate": ate,
        "ipw_ate_ci95": ci["ipw_ate_ci95"],
        "balance": bal.round(4).to_dict(orient="records"),
        "balanced_after_matching": bool(bal["ok_matched"].all()),
        "balanced_after_ipw": bool(bal["ok_ipw"].all()),
    }
    if "true_effect" in df.attrs:
        result["true_effect"] = df.attrs["true_effect"]
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=None, help="CSV path; omit for synthetic data")
    ap.add_argument("--boot", type=int, default=200)
    ap.add_argument("--out", default=None, help="optional JSON output path")
    a = ap.parse_args()

    res = run(load_data(a.data), n_boot=a.boot)
    print(json.dumps(res, indent=2))
    if a.out:
        Path(a.out).write_text(json.dumps(res, indent=2))
