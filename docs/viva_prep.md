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

## 7. Weeks 3-4: optimizer, drift and the API

**How does the optimizer choose who gets a coupon?**
It is a multiple-choice knapsack problem: each customer gets at most one of $0, $10 or $20, total coupon value must stay within the budget, and the objective is the extra purchases we expect. It is solved exactly with `scipy.optimize.milp` (HiGHS) and answers any budget in about 0.05 s. Customers with a negative effect are never chosen.

**Why does it use the "cautious" (lower-bound) effect?**
Picking the customers with the highest estimates also picks the ones whose estimates happen to be too high by luck (the optimizer's curse). In validation the model said 75.4 extra purchases at a $5,000 budget and the truth was 60.4. Using the lower 95% bound is safer and was never wildly wrong.

**Why does the optimizer sometimes spend less than the budget?**
It only gives coupons to customers whose cautious effect is above zero. Beyond about $6,670 nobody else qualifies, so it stops. Spending the rest would waste money.

**How good is the optimizer?**
At $5,000 it gets about 96% of the best possible result (60.4 vs 63.1 true extra purchases) and about 3x what random $10 coupons would. It gave no coupons to Sleeping Dogs.

**What is data drift and how do you detect it?**
Drift means new customers no longer look like the ones the model was trained on, so its answers get less trustworthy. For each feature we run a KS test and compute PSI, and we flag a feature only when both agree (KS p < 0.01 and PSI >= 0.1). On data from the same population nothing was flagged; on a simulated shift it flagged exactly the two shifted features.

**What does the API do?**
`/api/ite` and `/api/uplift-curve` serve the Double ML results, `/api/optimize` solves any budget, `/api/drift` checks for drift, and `/api/predict` scores a customer the model has never seen. Member 3's dashboard reads it.

**How does `/api/predict` work without retraining?**
The last stage of our Double ML model is linear in the (polynomial) features, so the whole causal model is just a few numbers per coupon (15 coefficients and a 15x15 covariance matrix). The API multiplies them with the customer's features. I checked it against EconML and the difference was about 1e-16. The baseline chance of buying comes from a small LightGBM model.

**How do you know the numbers can be trusted?**
The data is synthetic, so the true effect of each customer is known and I could check against it: correlation 0.91, optimizer at 96% of the best possible. I also ran refutation tests (a random fake cause gets about zero effect, removing a confounder changes the answer) and propensity-score checks.

**What are the weaknesses? (say these first)**
- The data is synthetic. On real data I would need a sensitivity analysis for hidden confounders.
- The estimates run high at the top end, so we show the cautious figure.
- The average effect of the $20 coupon is underestimated (+0.046 vs +0.071 true), although the ranking is good.
- The drift banner on the dashboard is a stored simulated example.
- The Docker image was written but I could not build it in my environment.
- There is no database; the API serves saved model files.

**Live demo order (about 3 minutes)**
1. Start `python backend/server.py` and open `/api/health` (all files true).
2. Dashboard: show the uplift curve (model above random), explain the peak at about 80%.
3. Change the budget and press Optimize; point out the cautious figure and the summary sentence.
4. Individual effects table: filter to Sleeping Dogs, explain why they get no coupon.
5. `/api/predict`: send one customer with curl or the demo page, read out the segment and suggested coupon.
6. Close with the limits above.

## 8. Questions about your own contribution
- Which files did you write, and what does each do?
- What was the hardest bug or decision? (For example: the average effect being underestimated, or the unobserved-confounder test crashing on a boolean column.)
- What would you do next with more time? (A causal forest for the final stage, real data with a hidden-confounder sensitivity analysis.)
- How did you work with Member 1 (data, DAG) and Member 3 (API contract, dashboard)? (I wrote the API contract and a frontend integration guide; Member 3's dashboard reads the API.)
- What was your biggest lesson in Weeks 3-4? (Point estimates that look best are the ones most likely to be wrong, so an optimizer must use cautious numbers.)

## Numbers worth memorising
| Item | Value |
|---|---|
| Naive effect | -0.005 |
| True average effect of $10 | +0.037 |
| Correlation with truth: baseline / Double ML | 0.70 / 0.91 |
| Extra purchases (top 40%): random / baseline / Double ML / best possible | 22.1 / 46.1 / 52.7 / 54.3 |
| `previous_purchases` SMD before / after matching | -0.398 / 0.012 |
| Optimizer at $5,000: true extra purchases / best possible / blanket $10 | 60.4 / 63.1 / about 18 |
| Optimizer estimate vs truth at $5,000 | 75.4 vs 60.4 (runs about 25% high) |
| Budget where the optimizer stops spending | about $6,670 |
| Drift rule | KS p < 0.01 and PSI >= 0.1 |
| `/api/predict` formula vs EconML | max difference about 1e-16 |
