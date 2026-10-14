# EconoCausal API Contract (Member 2 to Member 3)

**Status:** draft for Kailash to review. Reply with anything you need changed and we will update this file together.
**Base URL (Week 4):** `http://localhost:8000`

Until the API exists, build against the sample files in this folder. Their shape is exactly what the endpoint will return.

| Endpoint | Status | Sample file |
|---|---|---|
| `GET /api/ite` | Real model output (Double ML) | `docs/sample_ite.json` |
| `GET /api/uplift-curve` | Real model output (Double ML) | `docs/sample_uplift_curve.json` |
| `POST /api/optimize` | **Proposed shape only.** The optimizer is built in Week 3, so the numbers below are illustrative | none yet |
| `GET /api/drift` | **Proposed shape only.** The drift detector is built in Week 4, so the numbers below are illustrative | none yet |

---

## How to read the numbers

- **`ite`** is the Individual Treatment Effect: the estimated change in that customer's purchase probability if they get a $10 discount. `0.05` means +5 percentage points; a negative value means the discount makes a purchase less likely.
- **`ci_lower` / `ci_upper`** is a 95% confidence interval for the ITE.
- **`baseline_prob`** is the estimated purchase probability with no discount.
- **`segment`** is derived from the interval and the baseline:

| Segment | Rule | Meaning |
|---|---|---|
| `persuadable` | `ci_lower > 0` | The discount genuinely raises purchase probability. Spend budget here. |
| `sleeping_dog` | `ci_upper < 0` | The discount lowers purchase probability. Never discount. |
| `sure_thing` | interval includes 0 and `baseline_prob >= 0.5` | Probably buys anyway. A discount is wasted. |
| `lost_cause` | interval includes 0 and `baseline_prob < 0.5` | Probably does not buy either way. |

**Caveat on the absolute level.** On our synthetic data the model *ranks* customers very well (correlation about 0.91 with the true effect) but its *average* effect comes out lower than the truth (about +0.02 vs +0.037). Use the numbers for ranking and relative comparison, and avoid presenting the average ITE as a precise business figure.

---

## `GET /api/ite`

Query: `discount` (optional, default `10`; only `10` is supported for now).

```json
{
  "discount": 10,
  "model": "LinearDML (EconML), LightGBM nuisance models",
  "n_customers": 1500,
  "segment_counts": {"sure_thing": 663, "lost_cause": 393, "persuadable": 360, "sleeping_dog": 84},
  "customers": [
    {
      "customer_id": 4837,
      "baseline_prob": 0.2444,
      "ite": 0.0968,
      "ci_lower": 0.0065,
      "ci_upper": 0.1871,
      "segment": "persuadable"
    }
  ]
}
```

`docs/sample_ite.json` holds all 1,500 held-out customers, so you can test filtering, sorting and charting with thousands of rows (the brief's Mid Review "Data Load" check).

## `GET /api/uplift-curve`

A Qini curve: cumulative extra purchases caused, when customers are targeted best-ranked first. Computed on held-out customers from observed outcomes only.

```json
{
  "discount": 10,
  "x_label": "fraction of customers targeted (best-ranked first)",
  "y_label": "cumulative extra purchases caused",
  "model":  {"x": [0.0, 0.049, 0.1], "qini": [0.0, 0.53, 4.22]},
  "random": {"x": [0.0, 0.049, 0.1], "qini": [0.0, 0.31, 0.62]},
  "qini_coefficient": 5.748
}
```

Plot `model` and `random` as two lines on one chart. The further the model line sits above the random line, the better the targeting. `qini_coefficient` is the area between them. (The real file has 21 points; the example above shows the first three.)

Heads-up: the model curve rises, peaks around 80% of customers, then falls back to the random line at 100%. That is expected, because the last customers it ranks are the ones the discount hurts.

## `POST /api/optimize`  (proposed, Week 3)

Request:
```json
{ "budget": 5000, "discount_options": [10, 20] }
```

Response (**illustrative values only**):
```json
{
  "budget": 5000,
  "total_cost": 4990,
  "expected_incremental_purchases": 187.4,
  "savings_vs_blanket": 4200,
  "allocation": [
    {"customer_id": 4837, "discount": 20, "expected_uplift": 0.093, "cost": 20}
  ]
}
```
`savings_vs_blanket` feeds the natural-language summary ("This strategy saves $X compared to blanket targeting"). The exact fields may change when the optimizer is built, and we will update this file when they do.

## `GET /api/drift`  (proposed, Week 4)

Response (**illustrative values only**):
```json
{
  "drift_detected": false,
  "checked_at": "2026-11-01T10:00:00Z",
  "features": [
    {"name": "engagement", "ks_statistic": 0.04, "p_value": 0.62, "drift": false}
  ]
}
```
Show a warning banner when `drift_detected` is `true`.

---

## Open questions for Kailash
1. Do you need more fields per customer (e.g. `age`, `previous_purchases`) for filtering in the Allocation Matrix?
2. Pagination: should the API paginate, or return everything at once?
3. Do you want a separate `/api/summary` endpoint with the headline numbers, or will you compute them from the responses above?

## Regenerating the sample files
```bash
python backend/generate_causal_data.py    # creates data/customers_causal.csv
python backend/export_sample_json.py      # writes docs/sample_ite.json and docs/sample_uplift_curve.json
```
