# Weeks 3 and 4 Report: Optimization, Drift Detection and the API

**Author:** Member 2 (Sharath) | **Code:** `backend/optimizer.py`, `optimizer_core.py`, `drift.py`, `model_api.py`, `server.py`
Numbers below come from synthetic data where the true effects are known, so we can check the optimizer against the best possible answer.

## 1. Prescriptive optimization (Week 3)
**Problem.** Each customer can get no coupon, a $10 coupon or a $20 coupon. The budget is fixed. Who gets what? This is a multiple-choice knapsack: at most one coupon per customer, total face value within the budget, maximise the expected extra purchases. We solve it exactly with `scipy.optimize.milp` (HiGHS), not a heuristic.

**Effects fed to the optimizer.** A Double ML model with a multi-valued treatment ($0 / $10 / $20), so the $10 and $20 effects are estimated separately. The optimizer maximises the **lower 95% bound** of each effect, not the point estimate. A customer whose bound is not above zero never gets a coupon, so Sleeping Dogs are excluded automatically.

**Result at a $5,000 budget (1,500 held-out customers, true effects used for scoring):**

| Strategy | Customers | True extra purchases | Sleeping Dogs hit |
|---|---|---|---|
| **Optimizer (ours)** | 256 (12 at $10, 244 at $20) | **60.4** | 0 |
| Oracle (knows the true effects) | 272 | 63.1 | 0 |
| Rank by $10 effect, $10 each | 500 | 44.6 | 17 |
| Predictive: least likely to buy first, $10 | 500 | 26.2 | 89 |
| Blanket $10, random customers | 500 | 18.2 | n/a |
| Blanket $20, random customers | 250 | 17.8 | n/a |

The optimizer reaches **96% of the oracle**. Across budgets of $2,000, $5,000 and $10,000 it reaches 96%, 96% and 76%.

**Behaviours worth knowing**
- **It may not spend the whole budget.** Past about $6,670 no customer has a cautious effect above zero, so it stops. This is deliberate.
- **Estimates run high (optimizer's curse).** The optimizer picks customers whose estimates are high partly by luck. Its estimated total was 75.4 extra purchases against a true 60.4. The cautious figure (about 41) is the safe one to show, and the API returns both.
- **Feasibility clipping.** A purchase probability cannot go below 0 or above 1, so each effect is clipped to the possible range before optimising.
- **The $20 effect level is low.** The model's average $20 effect is +0.046 against a true +0.071 (the $10 level is right: +0.036 against +0.037). Ranking is still good.

## 2. Data drift detector (Week 4)
**Question.** Has new customer data stopped looking like the data the model learned from? If so, its estimates may be unreliable.

**Method.** For every feature we compare the training values with the new values using the Kolmogorov-Smirnov test and the Population Stability Index (PSI). A feature is flagged only when **both** agree (KS p-value below 0.01 and PSI at least 0.1). The KS test alone flags tiny differences when there are thousands of rows, and PSI alone ignores sample size.

**Checks.** On a second sample from the same population, no feature was flagged. When we shifted `engagement` by 0.8 standard deviations and scaled `previous_purchases` by 0.6, both were flagged (PSI 1.47 and 2.65) and the unchanged features were not. `POST /api/drift` runs the same check on any 50+ customers a client sends.

## 3. REST API and packaging (Week 4)
| Endpoint | What it returns |
|---|---|
| `GET /api/ite` | Individual treatment effects with 95% intervals and segments (filters: `segment`, `limit`) |
| `GET /api/uplift-curve` | Qini curve, model against random |
| `POST /api/optimize` | Coupon allocation for any budget, with a plain-English summary and cautious figures |
| `GET`/`POST /api/drift` | Stored simulated example (GET) or a live check of customers you send (POST) |
| `GET /api/customers` | All 1,000 customers as an array, the format the dashboard reads |

- `backend/server.py` runs Kirat's data routes and the model API together, without editing his `app.py`. I tested it with the real dashboard files, which showed "Live data from the API: 1,000 customers".
- `docs/api_demo.html` is a browser demo of every endpoint, and `docs/api_contract.md` is the contract for the frontend.
- **Packaging:** `gunicorn` runs the API (tested). A `Dockerfile` and `requirements-api.txt` are in the repository, but the **Docker image has not been built or tested**.

## 4. Testing and reproducibility
- 26 tests of my own pass: optimizer 5, drift 4, model API 13, combined server 4.
- **Fresh-checkout check.** I ran the pipeline on a clean copy of `main`: generate the dataset, then `causal_dag`, `baseline_model`, `casual_model`, `propensity`, `refutation`, `export_sample_json`, `optimizer --export` and `drift --export`. All eight ran without error, in 1 to 36 seconds each. Every committed JSON file regenerated **identical** (apart from timestamps), and the headline numbers matched the reports (for example the Double ML correlation of 0.912 and the optimizer's 60.4 against 63.1). This was run on one environment, so exact decimals can differ slightly with other library versions.

## 5. Limitations
- The data is synthetic and all confounders are observed, which real data would not guarantee.
- The optimizer's estimates run high, which is why the cautious figures are shown.
- The API serves results computed from a saved model, not a model retrained on live data. The drift check is live, but there is no real data feed behind it yet.
- No database layer, and the dashboard does not yet show the uplift curve, the allocation table or the drift banner.

## 6. Next
Connect those three dashboard views to the API (Member 3), show cautious figures and the summary text, and test the Docker image.
