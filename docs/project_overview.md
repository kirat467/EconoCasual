# EconoCausal: Project Overview (Member 2)

Written for the Mid Review viva. Read it, then retell it in your own words.

## 1. What are we building?
A system that decides **which customers should get a discount, and how big**, so a marketing budget causes as many extra purchases as possible.

Most "purchase prediction" asks: *who is likely to buy?* That is the wrong question for discounts, because:
- some customers **buy anyway** (Sure Things), so a coupon is wasted;
- some **never buy** (Lost Causes), so a coupon is wasted;
- a few are **put off by a discount** (Sleeping Dogs);
- only **Persuadables** buy because of the coupon.

So we estimate the **causal effect** of a discount on each customer, then spend the budget where that effect is largest. In the Infotact brief this is project 1: *Dynamic Pricing via Double Machine Learning*.

## 2. How the pieces fit
```
data  ->  causal model (Double ML)  ->  optimizer  ->  API  ->  dashboard
          effect per customer          who gets which   JSON    what the user sees
                                       coupon, in budget
                    drift detector: warns if new data stops looking like training data
```
1. **Data** (Member 1): customer records, with whether they got a discount and whether they bought.
2. **Causal model** (Member 2): estimates each customer's Individual Treatment Effect (ITE), the change in purchase probability caused by the discount.
3. **Optimizer** (Member 2): chooses $0, $10 or $20 per customer to maximise extra purchases within a budget.
4. **API** (Members 1 and 2): serves the results as JSON.
5. **Dashboard** (Member 3): shows the customers, the charts and the allocation table.

## 3. Why ordinary analysis fails here: confounding
In our data discounts were given mostly to customers with few previous purchases and high engagement, so the groups differ before any discount. A naive comparison of discounted and non-discounted customers gave **-0.005** on our synthetic data, while the true average effect of a $10 discount is **+0.037**. Confounding hid the real effect. On the team's original data, the naive effect was +0.052 and the adjusted effect +0.109. Causal methods adjust for the confounders (`previous_purchases`, `engagement`) to get the fair comparison.

## 4. The team
| Member | Role | What they did (from the repository) |
|---|---|---|
| **Kirat** (Member 1) | Data analysis and coordination | The dataset (`customers.csv`, 1,000 customers); data-quality and purchase-rate analysis (`data_analysis.py`, `analysis_report.md`); correlation and customer-insight validation; a Flask backend (`app.py`) with `/customers` and `/purchase-summary`; automated API tests (`test_app.py`); merging PRs and coordinating |
| **Sharath** (Member 2, me) | Machine learning / causal modelling | Everything in section 5 |
| **Kailash** (Member 3) | Frontend | A responsive customer-intelligence dashboard (`frontend/`): customer grid, purchase rate by engagement and by previous purchases, discount comparison with confidence range, an in-browser purchase model, data-quality panel, CSV upload and export, dark mode, GitHub Pages deployment |

The README says roles may rotate weekly. Check with the team if that applies to the review.

## 5. What I built
**Week 1: causal foundation**
- `causal_dag.py`: the causal graph in DoWhy (confounders, treatment, outcome) and the backdoor estimand; naive +0.052 vs adjusted +0.109.
- `baseline_model.py`: a predictive model (AUC 0.683) as the thing to beat.
- `docs/week1_findings.md`.

**Week 2: effect estimation and validation**
- `generate_causal_data.py`: a richer synthetic dataset (5,000 customers, $0/$10/$20 discounts, four covariates, effects that differ by customer, **including negative ones**) that also stores the true effect, so we can check ourselves. Real data never lets you do this.
- `casual_model.py`: Double ML written from scratch (cross-fitted nuisance models, residual-on-residual final stage), compared with EconML's `LinearDML` and `CausalForestDML`.
- `propensity.py`: propensity-score matching and IPW, with covariate-balance checks.
- `refutation.py` (+ notes): DoWhy refutation tests (placebo, random common cause, data subset, unobserved common cause).
- `export_sample_json.py`: ITE per customer with 95% intervals and segments, plus the uplift (Qini) curve, as JSON for the dashboard.
- Reports: `week2_double_ml_report.md`, `week2_propensity_report.md`.

**Week 3 and 4 work done early**
- `optimizer.py`: exact budget optimisation (multiple-choice knapsack, SciPy MILP). It maximises the **lower confidence bound** of each effect, so it is cautious.
- `drift.py`: data drift detector (KS test and PSI); flags a feature only if both agree.
- `model_api.py`: Flask API with `/api/ite`, `/api/uplift-curve`, `/api/optimize`, `/api/drift`, `/api/health`.
- Tests: `test_optimizer.py`, `test_model_api.py`, `test_drift.py`.
- Docs: `api_contract.md`, `optimizer_notes.md`, `how_to_run.md`, `viva_prep.md`, `requirements.txt`.

## 6. Key results (synthetic data, so we know the truth)
| What | Result |
|---|---|
| Naive vs true effect of $10 | -0.005 vs +0.037 |
| Correlation of estimated and true effect | Double ML 0.91, predictive baseline 0.70 |
| Extra purchases from targeting the top 40% | Random 22.1, baseline 46.1, Double ML 52.7, best possible 54.3 |
| Propensity matching | All four covariates balanced; `previous_purchases` SMD -0.398 to 0.012 |
| Refutation | Placebo, random cause and subset tests passed; a strong hidden confounder could flip the sign |
| Optimizer, $5,000 budget | About 60 extra purchases (true), best possible 63 (96%), blanket $10 coupons about 18, no Sleeping Dogs treated |
| Drift detector | No false alarms on same-population data; flags the shifted features |

## 7. Honest limitations (say these yourself in the viva)
- **The data is synthetic.** All confounders are measured because we built it that way. Real data would have hidden ones.
- **Average effect level.** The continuous-dollar Double ML model underestimates the average effect (about +0.02 vs +0.037). It **ranks** customers well, but treat absolute levels with care.
- **Optimizer's curse.** The optimizer picks customers whose estimates are high partly by luck, so its expected gain runs high (75 estimated vs 60 true). That is why we display the cautious figure.
- **Refutation tests cannot prove there is no hidden confounder.**
- **The API serves stored results**, not live predictions. `/api/optimize` only supports a $5,000 budget for now, and `/api/drift` returns a simulated example.
- **The dashboard is not connected to the model API yet**, and there is no database layer.

## 8. What is next
- Connect the dashboard to `/api/ite`, `/api/uplift-curve`, `/api/optimize` and `/api/drift`.
- Plug `model_api` into Kirat's `app.py`.
- Live optimisation for any budget, and a live drift check on incoming data.
- A natural-language summary on the dashboard (for example "about 3x more extra purchases than blanket coupons for the same budget").

## 9. Your pitch
**30 seconds:** "Normal ML predicts who will buy, but for discounts we need who will buy *because of* the discount. We use Double ML to estimate each customer's causal effect, then an optimizer spends a fixed budget on the customers where it matters, and never on those the discount would hurt. On synthetic data where we know the truth, it gets 96% of the best possible result."

**2 minutes:** add the confounding example (-0.005 vs +0.037), how Double ML removes it (residualise outcome and treatment, then regress), the validation (propensity balance, refutation tests, uplift curve), your pieces (model, optimizer, drift, API), and your honest limits from section 7.
