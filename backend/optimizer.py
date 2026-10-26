"""Prescriptive optimization for EconoCausal (Week 3, Member 2).

Brief: "Write a SciPy optimization script that maximizes total predicted revenue
subject to a strict marketing budget constraint, assigning personalized discounts."

The problem
  Each customer can get no discount, a $10 coupon or a $20 coupon. We know (from
  Double ML) how much each coupon is expected to raise each customer's purchase
  probability. The budget is fixed. Who gets which coupon?

  This is a MULTIPLE-CHOICE KNAPSACK:
      maximise   sum_i sum_d  value[i, d] * x[i, d]
      subject to sum_d x[i, d] <= 1            (at most one coupon per customer)
                 sum_i sum_d  cost[d] * x[i, d] <= budget
                 x[i, d] in {0, 1}
  with value[i, d] = estimated extra purchases from coupon d  (x average order value
  gives extra revenue) and cost[d] = the face value of the coupon. It is solved
  exactly as a mixed-integer linear programme with scipy.optimize.milp (HiGHS).

  Customers whose estimated effect is negative (Sleeping Dogs) are never chosen,
  because assigning them a coupon would lower the objective.

Steps
  1. Fit Double ML with a MULTI-VALUED treatment ($0 / $10 / $20), so the $10 and
     $20 effects are estimated separately instead of assuming a straight line.
  2. Optimise on held-out customers.
  3. Validate with the TRUE effects (known because the data is synthetic) and
     compare with simpler strategies.

Run from the repo root:  python backend/optimizer.py [--budget 5000] [--point-estimate] [--export]
"""
import argparse
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from econml.dml import LinearDML
from lightgbm import LGBMClassifier, LGBMRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import PolynomialFeatures

from optimizer_core import (AOV, DISCOUNTS, build_response, random_blanket, realised,  # noqa: F401
                            solve_allocation)

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
FEATURES = ["previous_purchases", "engagement", "price_sensitivity", "age"]


# --------------------------------------------------------------------------------
# The optimiser (reusable: the API will call this)
# --------------------------------------------------------------------------------






# --------------------------------------------------------------------------------
def fit_effects(train, test):
    """Multi-treatment Double ML: effect (and 95% interval) of $10 and $20 vs none."""
    nuisance = dict(n_estimators=200, learning_rate=0.05, num_leaves=8,
                    min_child_samples=30, random_state=0, verbose=-1)
    model = LinearDML(
        model_y=LGBMRegressor(**nuisance),
        model_t=LGBMClassifier(**nuisance),
        discrete_treatment=True,
        featurizer=PolynomialFeatures(2, include_bias=False),
        cv=5, random_state=0,
    )
    model.fit(train.purchase.values, train.discount.values, X=train[FEATURES].values)
    X = test[FEATURES].values
    tau, lo = {}, {}
    for d in DISCOUNTS:
        tau[d] = model.effect(X, T0=0, T1=d)
        lo[d] = model.effect_interval(X, T0=0, T1=d, alpha=0.05)[0]
    return tau, lo


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=float, default=5000)
    ap.add_argument("--point-estimate", action="store_true",
                    help="optimise the point estimate instead of the (default) lower confidence "
                         "bound. The default is more cautious: it avoids customers whose estimated "
                         "effect is probably noise, and is better when the budget is tight")
    ap.add_argument("--export", action="store_true", help="write docs/sample_optimize.json")
    args = ap.parse_args()

    df = pd.read_csv(ROOT / "data" / "customers_causal.csv")
    train, test = train_test_split(df, test_size=0.3, random_state=0)
    test = test.reset_index(drop=True)
    n = len(test)
    true = {10: test.true_ite_10.values, 20: test.true_ite_20.values}

    tau, lo = fit_effects(train, test)
    for d in DISCOUNTS:
        print(f"${d} effect: correlation with truth {np.corrcoef(tau[d], true[d])[0, 1]:.3f} | "
              f"mean estimate {tau[d].mean():+.4f} vs true {true[d].mean():+.4f}")

    # Feasibility: a purchase probability cannot fall below 0 or rise above 1, so an
    # effect must lie in [-p0, 1 - p0]. The polynomial model can extrapolate past that
    # at the extremes of the data, so clip to the possible range.
    ctrl = train[train.discount == 0]
    base_clf = LGBMClassifier(n_estimators=150, learning_rate=0.05, verbose=-1,
                              random_state=0).fit(ctrl[FEATURES], ctrl.purchase)
    p0 = base_clf.predict_proba(test[FEATURES])[:, 1]
    for d in DISCOUNTS:
        tau[d] = np.clip(tau[d], -p0, 1 - p0)
        lo[d] = np.clip(lo[d], -p0, 1 - p0)

    # what the optimiser maximises: point estimate, or the cautious lower bound
    conservative = not args.point_estimate
    basis = {d: np.maximum(lo[d], 0) if conservative else tau[d] for d in DISCOUNTS}
    values = np.column_stack([basis[d] for d in DISCOUNTS])

    choice = solve_allocation(values, DISCOUNTS, args.budget)
    spend = choice.sum()
    assert spend <= args.budget + 1e-6, "budget violated"

    # oracle: the best possible allocation if the true effects were known
    oracle_choice = solve_allocation(np.column_stack([true[d] for d in DISCOUNTS]),
                                     DISCOUNTS, args.budget)

    # simpler strategies for comparison, all with the same budget
    rng = np.random.default_rng(0)

    def top_k(score, discount):
        k = int(args.budget // discount)
        c = np.zeros(n)
        c[np.argsort(-score)[:k]] = discount
        return c

    strategies = {
        "OPTIMIZER (ours)": choice,
        "Oracle (knows true effects)": oracle_choice,
        "Rank by $10 effect, $10 each": top_k(tau[10], 10),
        "Predictive: least likely to buy first, $10": top_k(-p0, 10),
    }
    rows = []
    for name, c in strategies.items():
        rows.append({"strategy": name, "customers": int((c > 0).sum()), "spend": int(c.sum()),
                     "est. extra purchases": round(realised(c, tau), 1),
                     "TRUE extra purchases": round(realised(c, true), 1),
                     "sleeping dogs hit": int(((c > 0) & (true[10] < -0.01)).sum())})
    for d in DISCOUNTS:
        gain, k = random_blanket(rng, n, d, args.budget, true)
        est_gain, _ = random_blanket(rng, n, d, args.budget, tau)
        rows.append({"strategy": f"Blanket ${d}, random customers", "customers": k,
                     "spend": int(k * d), "est. extra purchases": round(est_gain, 1),
                     "TRUE extra purchases": round(gain, 1), "sleeping dogs hit": "n/a"})
    table = pd.DataFrame(rows).set_index("strategy")

    print(f"\nBudget ${args.budget:,.0f}, {n} held-out customers, "
          f"{'conservative (lower-bound)' if conservative else 'point-estimate'} objective\n")
    print(table.to_string())
    n10, n20 = int((choice == 10).sum()), int((choice == 20).sum())
    print(f"\nOptimizer gives {n10} customers $10 and {n20} customers $20 "
          f"(spend ${spend:,.0f} of ${args.budget:,.0f}).")
    true_opt = realised(choice, true)
    print(f"It captures {100 * true_opt / realised(oracle_choice, true):.0f}% of the oracle's true extra "
          f"purchases (about ${true_opt * AOV:,.0f} of extra revenue at ${AOV:.0f} per order).")

    if args.export:
        out = build_response(args.budget, test.customer_id.values, tau, lo, conservative)
        (ROOT / "docs").mkdir(exist_ok=True)
        (ROOT / "docs" / "sample_optimize.json").write_text(json.dumps(out, indent=2))
        # effects for the API, so it can solve ANY budget without refitting the model
        cache = {"discounts": DISCOUNTS, "customer_id": [int(c) for c in test.customer_id],
                 **{f"tau_{d}": [round(float(v), 6) for v in tau[d]] for d in DISCOUNTS},
                 **{f"lo_{d}": [round(float(v), 6) for v in lo[d]] for d in DISCOUNTS}}
        (ROOT / "docs" / "optimizer_effects.json").write_text(json.dumps(cache))
        print(f"\nWrote docs/sample_optimize.json ({len(out['allocation'])} customers) and "
              f"docs/optimizer_effects.json (effects for the API).")
        print(out["summary"])


if __name__ == "__main__":
    main()
