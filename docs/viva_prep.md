# Viva Preparation: EconoCausal (Member 2)

**Use this to practise.** Re-write each answer in your own words and add examples from your own work. The evaluators check that you understand what you built.

## 1. The big picture
**What does EconoCausal do?**
It estimates how much a discount changes *each customer's* chance of buying, not just who is likely to buy, and then spends a fixed budget on the customers where the discount makes the biggest difference.

**Why can't ordinary ML do this?**
A predictive model learns correlations. A customer with a 90% churn probability may leave anyway, so a $20 coupon is wasted. The question is causal: "would this customer buy if and only if we gave the discount?" Also, in our data discounts went to low-history customers, who buy less anyway, so the naive comparison even gets the sign wrong (-0.005 vs a true +0.037).

**The four customer types?**
- Persuadable: buys only with the discount, so spend here.
- Sure Thing: buys anyway, so it is wasted.
- Lost Cause: does not buy either way, so it is wasted.
- Sleeping Dog: the discount makes them *less* likely to buy, so never discount.

## 2. Causal concepts
**Treatment, outcome, confounder?**
Treatment = discount, outcome = purchase. A confounder influences both who gets the treatment and the outcome, here `previous_purchases` and `engagement`.

**ITE vs ATE vs ATT?**
ITE is the effect for one customer, ATE is the average over everyone, and ATT is the average over those who actually got the treatment.

**What is the DAG and what did DoWhy do with it?**
A graph of cause-and-effect arrows. We told DoWhy the confounders point into both treatment and outcome, and it identified the **backdoor** estimand: adjusting for those confounders recovers the effect.

**What assumptions does this rely on?**
Unconfoundedness (we measured all the confounders) and overlap (every kind of customer could have got or not got a discount). Unconfoundedness cannot be tested from the data.

## 3. Double ML
**Explain Double ML in four sentences.**
Fit one model that predicts the outcome from the covariates and another that predicts the treatment from the covariates. Subtract their predictions to get residuals: the part of the outcome and of the discount that the covariates cannot explain. Regress the outcome residual on the discount residual, letting the slope vary with the covariates. That slope is each customer's treatment effect.

**Why cross-fitting?**
If a model predicts the same data it was trained on, it overfits, and the residuals become too small and biased. Cross-fitting predicts every customer with a model that never saw them.

**Why "orthogonal"?**
The estimator is built so that small errors in the two nuisance models only have a second-order effect on the answer. That is why we can use flexible ML models (LightGBM) for the nuisance parts.

**What did you implement yourself, and how did you check it?**
The cross-fitted residualisation and two final stages. It matched EconML's `LinearDML` (correlation 0.912 vs 0.911 with the true effect).

**How well does it work?**
On held-out customers the correlation with the true effect was 0.91, versus 0.70 for a predictive baseline. Discounting the top 40% by estimated effect caused 52.7 extra purchases versus 46.1 for the baseline and 22.1 for random, out of a possible 54.3.

**What is a weakness?**
The average effect was underestimated (about +0.02 vs a true +0.037) with the continuous-dollar model. Ranking is reliable, but absolute levels need care.

## 4. Propensity scores
**What is a propensity score?**
The probability of receiving the treatment given the covariates. Customers with similar scores are comparable.

**What did matching achieve?**
It balanced the covariates: the standardized difference in `previous_purchases` went from -0.398 to 0.012. All four covariates ended below the 0.1 rule of thumb.

**Why did matching and IPW give different effect estimates?**
Both are noisy with this much data. The matched estimate was +0.016 and IPW +0.037 against a true +0.035, but the matched interval is wide, so the difference is within noise.

## 5. Refutation tests
**What is a refutation test?**
An attempt to break the estimate. Passing does not prove causality, it shows the estimate behaves like a real effect.

**Which ones did you run, and what happened?**
- Placebo treatment (shuffled discount): the effect fell to about zero. Pass.
- Random common cause (added a noise variable): the effect did not change. Pass.
- Data subset (80% of customers): the effect stayed stable. Pass.
- Unobserved common cause: a moderately strong hidden confounder cut the effect by about 60%, and a strong one flipped its sign.

**What can't these tests tell you?**
They cannot show there is no hidden confounder. In our synthetic data we know there isn't, because we built it. In real data that assumption cannot be tested.

**What happens if you leave out a real confounder?**
Dropping `previous_purchases` flipped the mean effect from +0.028 to -0.023 and doubled the error, so the adjustment matters. The ranking stayed good (correlation 0.937).

## 6. Evaluation
**What is a Qini curve?**
It shows cumulative extra purchases caused as you target customers in order of predicted effect. A model that finds the right customers rises above the straight line you'd get from random targeting.

## 7. Week 3 preview (optimizer)
**How does the optimizer choose who gets a coupon?**
It is a multiple-choice knapsack problem: each customer gets at most one of $0, $10 or $20, total coupon value must stay within the budget, and the objective is the estimated extra purchases. It is solved exactly with `scipy.optimize.milp`. Customers with a negative effect are never chosen.

## 8. Questions about your own contribution
- Which files did you write, and what does each do?
- What was the hardest bug or decision? (For example: the average effect being underestimated, or the unobserved-confounder test crashing on a boolean column.)
- What would you do next with more time? (A causal forest for the final stage, real data with a hidden-confounder sensitivity analysis.)
- How did you work with Member 1 (data, DAG) and Member 3 (API contract)?

## Numbers worth memorising
| Item | Value |
|---|---|
| Naive effect | -0.005 |
| True average effect of $10 | +0.037 |
| Correlation with truth: baseline / Double ML | 0.70 / 0.91 |
| Extra purchases (top 40%): random / baseline / Double ML / best possible | 22.1 / 46.1 / 52.7 / 54.3 |
| `previous_purchases` SMD before / after matching | -0.398 / 0.012 |
