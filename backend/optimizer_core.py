"""Lightweight optimizer core (no model training): used by optimizer.py and the API.

Keeping this separate means the API can solve an allocation for any budget quickly,
without importing or refitting the causal model. The effects come from
docs/optimizer_effects.json, written by `python backend/optimizer.py --export`.
"""
import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import csr_matrix, vstack

DISCOUNTS = [10, 20]
AOV = 40.0     # assumed average order value in dollars, used only to express revenue


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


def build_response(budget, customer_ids, tau, lo, conservative=True):
    """Solve the allocation for one budget and return the /api/optimize payload.

    tau, lo : {discount: array} point estimate and lower 95% bound of each customer's effect
    """
    n = len(customer_ids)
    basis = {d: np.maximum(lo[d], 0) if conservative else tau[d] for d in DISCOUNTS}
    values = np.column_stack([basis[d] for d in DISCOUNTS])
    choice = solve_allocation(values, DISCOUNTS, budget)
    spend = float(choice.sum())

    est_total = realised(choice, tau)
    cautious_total = realised(choice, {d: np.maximum(lo[d], 0) for d in DISCOUNTS})
    blanket_est, _ = random_blanket(np.random.default_rng(0), n, 10, budget, tau)
    per_dollar_blanket = tau[10].mean() / 10          # expected extra purchases per $ if random
    blanket_cost = est_total / per_dollar_blanket if per_dollar_blanket > 0 else float("inf")
    reachable = blanket_cost <= n * 10
    cautious = np.array([max(lo[int(choice[i])][i], 0.0) if choice[i] > 0 else 0.0
                         for i in range(n)])
    allocation = [
        {"customer_id": int(customer_ids[i]), "discount": int(choice[i]),
         "expected_uplift": round(float(tau[int(choice[i])][i]), 4),
         "cautious_uplift": round(float(cautious[i]), 4),   # lower 95% bound: safer to display
         "cost": int(choice[i])}
        for i in np.argsort(-cautious) if choice[i] > 0
    ]
    n10, n20 = int((choice == 10).sum()), int((choice == 20).sum())
    lift = round(float(est_total / blanket_est), 2) if blanket_est > 0 else None
    savings = round(float(blanket_cost - spend), 2) if reachable else None

    summary = (f"With a ${budget:,.0f} budget the optimizer gives {n10 + n20} customers a coupon "
               f"({n10} at $10, {n20} at $20) and expects at least about "
               f"{cautious_total:.0f} extra purchases (cautious estimate).")
    if savings is not None:
        summary += f" Matching that with blanket $10 coupons would cost about ${blanket_cost:,.0f}."
    elif lift is not None:
        summary += (f" By the model's own estimates, which run high, that is about {lift:.1f}x the "
                    f"extra purchases of random $10 coupons at the same budget.")

    return {
        "budget": float(budget), "total_cost": spend,
        "expected_incremental_purchases": round(float(est_total), 2),
        "cautious_incremental_purchases": round(float(cautious_total), 2),
        "expected_incremental_revenue": round(float(est_total * AOV), 2),
        "average_order_value_assumed": AOV,
        "blanket_expected_incremental_purchases": round(float(blanket_est), 2),
        "lift_vs_blanket": lift,
        "blanket_cost_for_same_result": round(float(blanket_cost), 2) if reachable else None,
        "savings_vs_blanket": savings,
        "objective": "lower_confidence_bound" if conservative else "point_estimate",
        "customers_per_discount": {"10": n10, "20": n20},
        "summary": summary,
        "allocation": allocation,
    }
