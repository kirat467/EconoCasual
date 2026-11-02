# Week 2 Report: Double Machine Learning for Discount Effects

**Author:** Member 2 (Sharath) | **Code:** `backend/casual_model.py`, `backend/generate_causal_data.py`
**Data:** `data/customers_causal.csv`, 5,000 synthetic customers (the true effect of each discount is stored, for validation only)

## Why we needed richer data
The team's `data/customers.csv` has two covariates, a yes/no discount and one uniform effect, so there is nothing for a model of *individual* effects to find. `generate_causal_data.py` keeps the same story (discounts go to low-history, high-engagement customers, so assignment is confounded) and adds:
- a discount **level** of $0, $10 or $20;
- two more covariates, `price_sensitivity` and `age`;
- **heterogeneous effects**, including negative ones: about 18% of customers are "Sleeping Dogs" for whom a $10 discount lowers purchase probability;
- the true individual effect (`true_ite_10`, `true_ite_20`), which real data never has.

In this data the naive comparison (discounted vs not) gives **-0.005** while the true average effect of a $10 discount is **+0.037**. Confounding completely hides the effect.

## The method
Double ML estimates the effect of a treatment `T` (discount dollars) on an outcome `Y` (purchase) after removing the influence of covariates `X`:

1. **Cross-fit** two nuisance models with 5 folds, so each customer's prediction comes from a model that never saw them: `E[Y | X]` (how likely they are to buy anyway) and `E[T | X]` (how likely they were to get a discount).
2. **Residualise:** `Y_res = Y - E[Y|X]` and `T_res = T - E[T|X]`. `T_res` is the part of the discount that the covariates do not explain, which behaves as if it were randomised.
3. **Final stage:** learn how `Y_res` depends on `T_res`, allowing the slope to vary with `X`. That slope is the individual treatment effect (ITE).

We implemented this from scratch (LightGBM nuisance models, polynomial-linear and GBM final stages) and compared it with EconML's `LinearDML` and `CausalForestDML`.

## Results (1,500 held-out customers, effect of a $10 discount)
"Extra purchases" = purchases we would really cause by discounting the 40% of customers the model ranks highest, measured with the true effects. The best possible is 54.3.

| Model | Correlation with true effect | RMSE | Extra purchases | Sleeping Dogs treated |
|---|---|---|---|---|
| Random targeting | n/a | n/a | 22.1 | 18.2% |
| Baseline (predictive model) | 0.701 | 0.076 | 46.1 | 4.7% |
| Double ML (ours, polynomial-linear) | **0.912** | 0.043 | 52.7 | 0.7% |
| Double ML (ours, GBM final stage) | 0.793 | 0.060 | 50.8 | 2.8% |
| EconML `LinearDML` | 0.911 | 0.042 | 52.7 | 0.8% |
| EconML `CausalForestDML` | 0.898 | 0.033 | 53.4 | 0.0% |

Our implementation matches EconML's `LinearDML` almost exactly, and all the causal models clearly beat the predictive baseline at ranking customers by who the discount actually changes.

## Known issue: the average effect was underestimated
Every continuous-dollar Double ML model put the average effect at about +0.02, against a true +0.037. What we checked:
- With the **true** nuisance functions the average rose to +0.030, with the same ranking quality. So part of the gap comes from the final stage and part from error in the learned nuisance models.
- Changing the size and settings of the nuisance models only moved it from 0.019 to 0.022.
- Later, treating the discount as a **multi-valued category** ($0 / $10 / $20) brought the $10 effect to +0.036 against a true +0.037. This suggests that modelling dollars as one continuous number is the weak point, although we have not proven that cause.

The ranking is reliable. Treat the average level with care unless the multi-valued model is used.

## Limitations
- The data is synthetic, and all confounders are observed because we built it that way. Real data would have hidden ones (see `refutation_notes.md`).
- The polynomial final stage can over-extrapolate for customers at the extremes of the data.

## Next
Propensity score matching and balance checks (`week2_propensity_report.md`), refutation tests, then the budget optimizer in Week 3.
