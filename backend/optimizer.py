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
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import csr_matrix, vstack
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import PolynomialFeatures

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
FEATURES = ["previous_purchases", "engagement", "price_sensitivity", "age"]
DISCOUNTS = [10, 20]
AOV = 40.0     # assumed average order value in dollars, used only to express revenue


# --------------------------------------------------------------------------------
# The optimiser (reusable: the API will call this)
# --------------------------------------------------------------------------------
def solve_allocation(values, discounts, budget, time_limit=60):
    """Exact multiple-choice knapsack.

    values    : (n_customers, n_options) value of giving option j to customer i
    discounts : list of coupon face values (the cost of each option)
    returns   : array of length n_customers with the chosen discount (0 = none)
    """
    n, k = values.shape
    costs = np.tile(np.asarray(discounts, float), n)          # cost of variable (i, j)

    # at most one coupon per customer: row i has ones in columns i*k .. i*k+k-1
    rows = np.repeat(np.arange(n), k)
    assign = csr_matrix((np.ones(n * k), (rows, np.arange(n * k))), shape=(n, n * k))
    budget_row = csr_matrix(costs.reshape(1, -1))

    constraints = LinearConstraint(
        vstack([assign, budget_row]),
        lb=-np.inf,
        ub=np.concatenate([np.ones(n), [budget]]),
    )
    res = milp(c=-values.ravel(), constraints=constraints,
               integrality=np.ones(n * k), bounds=Bounds(0, 1),
               options={"time_limit": time_limit, "mip_rel_gap": 1e-6})
    if res.x is None:
        raise RuntimeError(f"optimiser failed: {res.message}")
    chosen = np.round(res.x).reshape(n, k)
    choice = np.zeros(n)
    for j, d in enumerate(discounts):
        choice[chosen[:, j] == 1] = d
    return choice


def realised(choice, tau_by_discount):
    """Sum of effects actually obtained by an allocation. tau_by_discount: {d: array}."""
    total = 0.0
    for d, tau in tau_by_discount.items():
        total += tau[choice == d].sum()
    return total


def random_blanket(order_rng, n, discount, budget, tau_by_discount, reps=300):
    """Give everyone the SAME coupon, in random order, until the budget runs out."""
    k = int(budget // discount)
    out = []
    for _ in range(reps):
        pick = order_rng.permutation(n)[:k]
        out.append(tau_by_discount[discount][pick].sum())
    return float(np.mean(out)), min(k, n)


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
        est_total = realised(choice, tau)
        cautious_total = realised(choice, {d: np.maximum(lo[d], 0) for d in DISCOUNTS})
        blanket_est, _ = random_blanket(np.random.default_rng(0), n, 10, args.budget, tau)
        per_dollar_blanket = tau[10].mean() / 10          # expected extra purchases per $ if random
        blanket_cost = est_total / per_dollar_blanket if per_dollar_blanket > 0 else float("inf")
        reachable = blanket_cost <= n * 10
        cautious = np.array([max(lo[int(choice[i])][i], 0.0) if choice[i] > 0 else 0.0
                             for i in range(n)])
        allocation = [
            {"customer_id": int(test.customer_id[i]), "discount": int(choice[i]),
             "expected_uplift": round(float(tau[int(choice[i])][i]), 4),
             "cautious_uplift": round(float(cautious[i]), 4),   # lower 95% bound: safer to display
             "cost": int(choice[i])}
            for i in np.argsort(-cautious) if choice[i] > 0
        ]
        out = {
            "budget": args.budget, "total_cost": float(spend),
            "expected_incremental_purchases": round(float(est_total), 2),
            "cautious_incremental_purchases": round(float(cautious_total), 2),
            "expected_incremental_revenue": round(float(est_total * AOV), 2),
            "average_order_value_assumed": AOV,
            "blanket_expected_incremental_purchases": round(float(blanket_est), 2),
            "lift_vs_blanket": round(float(est_total / blanket_est), 2) if blanket_est > 0 else None,
            "blanket_cost_for_same_result": round(float(blanket_cost), 2) if reachable else None,
            "savings_vs_blanket": round(float(blanket_cost - spend), 2) if reachable else None,
            "objective": "lower_confidence_bound" if conservative else "point_estimate",
            "customers_per_discount": {"10": n10, "20": n20},
            "allocation": allocation,
        }
        (ROOT / "docs").mkdir(exist_ok=True)
        (ROOT / "docs" / "sample_optimize.json").write_text(json.dumps(out, indent=2))
        print(f"\nWrote docs/sample_optimize.json ({len(allocation)} customers). "
              f"Blanket coupons would need about ${blanket_cost:,.0f} for the same estimated result"
              f"{'' if reachable else ' (more than $10 to every customer, so not reachable)'}.")


if __name__ == "__main__":
    main()
