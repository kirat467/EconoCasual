# Week 1 Findings: Confounding in the Discount Data

**Author:** Member 2 (Sharath) | **Branch:** `Member-2` | **Date:** 2026-10-11
**Scripts:** `backend/causal_dag.py`, `backend/baseline_model.py` | **Data:** `data/customers.csv` (1,000 customers)

## Summary
Customers who received a discount look only slightly more likely to buy (+5.2 percentage points), but the discount was not handed out at random. After adjusting for the confounders, the estimated effect of a discount roughly doubles to **+10.9 percentage points**. A naive comparison therefore understates the discount's true effect, which is the reason for using causal methods in this project.

## Causal graph (DoWhy)
- **Treatment:** `discount` (0/1)
- **Outcome:** `purchase` (0/1)
- **Confounders** (affect both who gets a discount and who buys): `previous_purchases`, `engagement`

DoWhy identified the **backdoor** estimand: the effect of `discount` on `purchase` is identified by adjusting for `previous_purchases` and `engagement`. The IV and front-door estimands are not available with this data.

## Evidence of confounding
| Group | Customers with discount | Customers without discount |
|---|---|---|
| Mean `previous_purchases` | 3.94 | 5.18 |
| Mean `engagement` | 5.64 | 5.23 |
| Purchase rate | 59.5% | 54.2% |

Standardized mean differences (treated minus untreated):
- `previous_purchases`: **-0.435**
- `engagement`: **+0.139**

A common rule of thumb is that an absolute value above about 0.1 signals meaningful imbalance, so both covariates are imbalanced. Discounts went disproportionately to customers with **fewer previous purchases**, who are less likely to buy anyway. That drags the naive treated group's purchase rate down and hides part of the discount's effect.

## Effect estimates
| Method | Estimated effect of a discount |
|---|---|
| Naive difference in purchase rates | +0.052 |
| Adjusted for confounders (linear regression, backdoor) | **+0.109** |

The adjusted estimate is a linear-probability model, so it is a first-pass estimate and not the final method. Week 2 replaces it with Double ML.

## Baseline purchase-prediction model
- Gradient boosting classifier on `previous_purchases`, `engagement`, `discount`.
- Test AUC: **0.683**.
- Average uplift read from the model (predict with discount=1 minus discount=0): **+0.104**.

On this dataset the baseline's average uplift is close to the adjusted estimate, because the data has a simple, uniform effect. A predictive model is not designed to estimate causal effects, and its individual-level uplift is not validated. Double ML will estimate effects per customer, and this baseline is the benchmark to compare against.

## Limitations
- The data is synthetic, with only 2 covariates and a binary discount.
- Real campaigns use several discount levels ($10 / $20), which the brief calls for, so the data needs a discount-amount column.
- There is no ground-truth individual effect in this file, so we cannot yet measure how well the model recovers per-customer ITE.
- The linear adjustment assumes a constant effect, whereas Double ML can capture heterogeneity.

## Next steps (Week 2)
1. Agree with Member 1 on richer data: a discount level (0/10/20), more covariates and heterogeneous effects.
2. Implement cross-fitted Double ML in `backend/casual_model.py` and compare with EconML (`LinearDML`, `CausalForestDML`).
3. Add propensity score matching and covariate balance checks.
4. Agree the API JSON format with Member 3.
5. Mid Review prep: DoWhy refutation tests (placebo treatment, random common cause, data subset).
