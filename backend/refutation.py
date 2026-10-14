"""Causal audit: refutation tests for EconoCausal (Mid Review, Member 2).

Brief: "Prove mathematically (via Refutation Tests in DoWhy) that the model has
successfully isolated the causal effect from hidden confounders."

A refutation test does not prove a causal claim. It tries to BREAK it. If the
estimate survives several attacks that it should survive, and reacts to the
attacks it should react to, our confidence grows.

PART A  DoWhy refuters on the effect of a $10 discount vs none
          1. Placebo treatment      -> a fake (shuffled) discount should have ~0 effect
          2. Random common cause    -> adding a pure-noise confounder should not move it
          3. Data subset            -> estimating on random 80% subsets should be stable
          4. Unobserved common cause-> how fragile is the result to a hidden confounder?
PART B  The same attacks on OUR from-scratch Double ML (casual_model.DoubleML),
        plus a "drop a real confounder" experiment that SHOULD break the estimate.

Run from the repo root:  python backend/refutation.py
(needs data/customers_causal.csv: python backend/generate_causal_data.py)
"""
import logging
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from dowhy import CausalModel

from casual_model import FEATURES, DoubleML

warnings.filterwarnings("ignore")
logging.getLogger("dowhy").setLevel(logging.ERROR)

ROOT = Path(__file__).resolve().parent.parent
N_SIMS = 100       # simulations for the DoWhy refuters
N_REPS = 15        # repetitions for the Double ML refutations
SEED = 0


def load():
    return pd.read_csv(ROOT / "data" / "customers_causal.csv")


# --------------------------------------------------------------------------------
# PART A: DoWhy
# --------------------------------------------------------------------------------
def part_a(df):
    sub = df[df.discount.isin([0, 10])].copy()
    sub["treated"] = (sub.discount == 10).astype(int)   # int 0/1 (DoWhy's confounder simulation needs it)
    truth = sub.loc[sub.treated == 1, "true_ite_10"].mean()

    model = CausalModel(data=sub, treatment="treated", outcome="purchase",
                        common_causes=FEATURES)
    estimand = model.identify_effect(proceed_when_unidentifiable=True)
    estimate = model.estimate_effect(estimand, method_name="backdoor.linear_regression")
    est = float(estimate.value)

    print("=" * 78)
    print("PART A: DoWhy refuters ($10 discount vs none, linear backdoor estimator)")
    print("=" * 78)
    print(f"Estimated effect: {est:+.4f}   (true effect for treated customers: {truth:+.4f})\n")

    rows = []

    def run(name, expect, **kw):
        try:
            r = model.refute_estimate(estimand, estimate, **kw)
            new = float(r.new_effect)
            p = None
            if isinstance(getattr(r, "refutation_result", None), dict):
                p = r.refutation_result.get("p_value")
            rows.append((name, expect, est, new, p))
        except Exception as exc:  # report, do not hide
            rows.append((name, expect, est, None, f"error: {exc}"[:60]))

    run("Placebo treatment", "new effect ~ 0",
        method_name="placebo_treatment_refuter", placebo_type="permute",
        num_simulations=N_SIMS, random_seed=SEED)
    run("Random common cause", "new effect ~ original",
        method_name="random_common_cause", num_simulations=N_SIMS, random_seed=SEED)
    run("Data subset (80%)", "new effect ~ original",
        method_name="data_subset_refuter", subset_fraction=0.8,
        num_simulations=N_SIMS, random_seed=SEED)
    # A hidden confounder of growing strength. A robust estimate degrades gradually;
    # we look for the strength at which the conclusion (effect > 0) would flip.
    for s_out in (0.02, 0.1, 0.5):
        run(f"Unobserved cause (outcome strength {s_out})", "shrinks as the hidden cause gets stronger",
            method_name="add_unobserved_common_cause",
            confounders_effect_on_treatment="binary_flip",
            confounders_effect_on_outcome="linear",
            effect_strength_on_treatment=0.05, effect_strength_on_outcome=s_out)

    out = pd.DataFrame(rows, columns=["test", "what we expect", "original", "new effect", "p-value"])
    out["original"] = out["original"].map(lambda v: f"{v:+.4f}")
    out["new effect"] = out["new effect"].map(lambda v: "n/a" if v is None else f"{v:+.4f}")
    print(out.to_string(index=False))
    return out


# --------------------------------------------------------------------------------
# PART B: our Double ML
# --------------------------------------------------------------------------------
def mean_ite(train_df, features, treatment="discount", seed=0, extra=None):
    X = train_df[features].values if extra is None else np.column_stack([train_df[features].values, extra])
    m = DoubleML(final="linear", seed=seed).fit(X, train_df[treatment].values, train_df["purchase"].values)
    return m.ite(X, 10), m


def part_b(df):
    rng = np.random.default_rng(SEED)
    truth = df["true_ite_10"].values
    base_ite, _ = mean_ite(df, FEATURES)
    base = base_ite.mean()
    corr0 = np.corrcoef(base_ite, truth)[0, 1]

    print("\n" + "=" * 78)
    print("PART B: refutation of our from-scratch Double ML (all customers)")
    print("=" * 78)
    print(f"Original: mean ITE of a $10 discount = {base:+.4f}  "
          f"(true mean {truth.mean():+.4f}; correlation with truth {corr0:.3f})\n")

    results = []

    # 1. Placebo: shuffle the discount column. It no longer has any link to purchases,
    #    so the estimated effect should be centred on zero.
    placebo = []
    for i in range(N_REPS):
        shuffled = df.assign(discount=rng.permutation(df.discount.values))
        placebo.append(mean_ite(shuffled, FEATURES, seed=i)[0].mean())
    placebo = np.array(placebo)
    n_as_big = int((np.abs(placebo) >= abs(base)).sum())
    results.append(("Placebo treatment (shuffled discount)", "mean ~ 0",
                    f"{placebo.mean():+.4f} (sd {placebo.std():.4f})",
                    f"original {base:+.4f} is {abs(base) / max(placebo.std(), 1e-9):.1f} placebo-SDs from 0; "
                    f"{n_as_big} of {N_REPS} placebo runs as large",
                    abs(placebo.mean()) < 2 * max(placebo.std(), 1e-9) and abs(base) > 2 * placebo.std()))

    # 2. Random common cause: add a noise covariate unrelated to everything.
    noisy = []
    for i in range(N_REPS):
        noise = rng.normal(size=len(df))
        noisy.append(mean_ite(df, FEATURES, seed=i, extra=noise)[0].mean())
    noisy = np.array(noisy)
    results.append(("Random common cause (+ noise column)", "mean ~ original",
                    f"{noisy.mean():+.4f} (sd {noisy.std():.4f})",
                    f"shift {noisy.mean() - base:+.4f}",
                    abs(noisy.mean() - base) < 0.25 * abs(base) + 2 * noisy.std() / np.sqrt(N_REPS)))

    # 3. Data subset: refit on random 80% of customers.
    subs = []
    for i in range(N_REPS):
        part = df.sample(frac=0.8, random_state=i)
        subs.append(mean_ite(part, FEATURES, seed=i)[0].mean())
    subs = np.array(subs)
    results.append(("Data subset (random 80%)", "mean ~ original",
                    f"{subs.mean():+.4f} (sd {subs.std():.4f})",
                    f"shift {subs.mean() - base:+.4f}",
                    abs(subs.mean() - base) < 0.25 * abs(base) + 2 * subs.std() / np.sqrt(N_REPS)))

    table = pd.DataFrame(results, columns=["test", "expected", "result", "comparison", "passed"])
    table["passed"] = table["passed"].map({True: "PASS", False: "FAIL"})
    print(table.to_string(index=False, max_colwidth=100))

    # 4. Dropping a real confounder SHOULD hurt. If it does not, the test is toothless.
    print("\nSensitivity check: what if we 'forget' a real confounder? "
          "(this SHOULD make the estimate worse)")
    rows = []
    for dropped in [None, "previous_purchases", "engagement"]:
        feats = [f for f in FEATURES if f != dropped]
        ite, _ = mean_ite(df, feats)
        rows.append({"features used": "all four" if dropped is None else f"without {dropped}",
                     "mean ITE": round(ite.mean(), 4),
                     "corr with truth": round(np.corrcoef(ite, truth)[0, 1], 3),
                     "RMSE vs truth": round(float(np.sqrt(np.mean((ite - truth) ** 2))), 4)})
    print(pd.DataFrame(rows).to_string(index=False))
    return table


if __name__ == "__main__":
    df = load()
    part_a(df)
    part_b(df)
