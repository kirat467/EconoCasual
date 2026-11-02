# Prescriptive Optimization Notes (Week 3)

**Author:** Member 2 (Sharath) | **Script:** `backend/optimizer.py` | **Sample output:** `docs/sample_optimize.json`
**Data:** `data/customers_causal.csv` (synthetic, so the true effects are known and we can validate)

## The problem
Each customer can get no coupon, a $10 coupon or a $20 coupon. Double ML estimates how much each coupon raises each customer's purchase probability. The budget is fixed (default $5,000). Who gets which coupon?

## The method
This is a **multiple-choice knapsack problem**:

- maximise the sum of `value[i, d] * x[i, d]` (estimated extra purchases)
- subject to at most one coupon per customer: sum over `d` of `x[i, d] <= 1`
- subject to the budget: sum of `d * x[i, d] <= budget`
- with `x[i, d]` equal to 0 or 1

It is solved **exactly** as a mixed-integer linear programme with `scipy.optimize.milp` (HiGHS solver). It finishes in about a second for 1,500 customers.

Two details matter:
1. **Separate $10 and $20 effects.** The model is Double ML with a *multi-valued* treatment (EconML `LinearDML`, `discrete_treatment=True`), so the two coupons are estimated separately instead of assuming a straight line in dollars.
2. **Cautious objective (default).** The optimizer maximises the *lower 95% confidence bound* of each effect (floored at 0), not the point estimate. Use `--point-estimate` to switch.

## Results (1,500 held-out customers, $5,000 budget)
Extra purchases measured with the TRUE effects:

| Strategy | Customers | True extra purchases | Sleeping Dogs hit |
|---|---|---|---|
| Oracle (knows the true effects) | 272 | 63.1 | 0 |
| **Optimizer (ours, cautious)** | 256 | **60.4** (96% of oracle) | **0** |
| Rank by estimated $10 effect, $10 each | 500 | 44.6 | 17 |
| Predictive: least likely to buy first, $10 | 500 | 26.2 | 89 |
| Blanket $10, random customers | 500 | 18.2 | n/a |
| Blanket $20, random customers | 250 | 17.8 | n/a |

The optimizer gives 12 customers $10 and 244 customers $20. Against a random blanket coupon with the same budget it earns about **3.3x** as many extra purchases (60.4 vs 18.2). The "predictive" strategy of discounting the customers least likely to buy is the classic non-causal approach, and it performs barely better than random while hitting 89 Sleeping Dogs.

## Cautious vs point estimate, across budgets
| Budget | Objective | Spend | True extra purchases | % of oracle | Estimated / true |
|---|---|---|---|---|---|
| $2,000 | point estimate | $2,000 | 28.9 | 90% | 1.69 |
| $2,000 | **cautious** | $2,000 | 30.7 | **96%** | 1.38 |
| $5,000 | point estimate | $5,000 | 56.1 | 89% | 1.50 |
| $5,000 | **cautious** | $5,000 | 60.4 | **96%** | 1.25 |
| $10,000 | point estimate | $10,000 | 85.1 | 88% | 1.35 |
| $10,000 | cautious | $6,670 | 73.7 | 76% | 1.19 |

The cautious objective is better when the budget is tight, because it avoids customers whose estimated effect is probably noise. When the budget is generous it is *too* cautious: it leaves $3,330 unspent and loses ground. A sensible rule is cautious by default, and point estimates only when the budget is loose.

## Limitations (say these in the viva)
- **Estimates run high.** Even the cautious version estimates 1.25x the true gain at $5,000. This is the "optimizer's curse": choosing the best-looking customers selects those whose estimates are inflated by noise.
- **Tail overshoot.** The polynomial final stage over-extrapolates for the strongest responders. For customers the model rates above 0.4, the average estimate was 0.50 while the true average was 0.34. We clip effects to the feasible range `[-p0, 1 - p0]`, but that does not remove the overshoot. A causal forest or a regularised final stage could help.
- **Level of the $20 effect.** The mean estimated $20 effect is +0.046 vs a true +0.071, about 35% low. The $10 effect is on target (+0.036 vs +0.037).
- **Value model.** We maximise extra purchases, with revenue shown as purchases times an assumed $40 average order value. The budget counts the face value of coupons issued, not expected redemptions, and we ignore the margin lost on customers who would have bought anyway.
- **Synthetic data.** Real campaigns have unmeasured confounders (see the refutation notes), so real-world gains would be lower.

## Viva answers in one line each
- **Why an exact solver?** The problem is a knapsack, so a MILP solver returns the true optimum instead of a heuristic.
- **Why never discount some customers?** Their estimated effect is negative (Sleeping Dogs), so a coupon lowers the objective.
- **Why the lower confidence bound?** It guards against acting on noisy estimates, which matters most when the budget is tight.
- **Why separate $10 and $20 effects?** The dose-response is not a straight line, and the optimizer needs to compare the two options per customer.
