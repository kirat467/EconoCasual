# EconoCausal API Contract (Member 2 to Member 3)

**Status:** draft for Kailash to review. Reply with anything you need changed and we will update this file together.
**Base URL (Week 4):** `http://localhost:8000`

Until the API exists, build against the sample files in this folder. Their shape is exactly what the endpoint will return.

| Endpoint | Status | Sample file |
|---|---|---|
| `GET /api/ite` | Real model output (Double ML) | `docs/sample_ite.json` |
| `GET /api/uplift-curve` | Real model output (Double ML) | `docs/sample_uplift_curve.json` |
| `POST /api/optimize` | Real optimizer output (Week 3, `backend/optimizer.py`) | `docs/sample_optimize.json` |
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

## `POST /api/optimize`

Request:
```json
{ "budget": 5000, "discount_options": [10, 20] }
```

Response (real values from `docs/sample_optimize.json`, abbreviated):
```json
{
  "budget": 5000.0,
  "total_cost": 5000.0,
  "expected_incremental_purchases": 75.36,
  "cautious_incremental_purchases": 40.54,
  "expected_incremental_revenue": 3014.24,
  "average_order_value_assumed": 40.0,
  "blanket_expected_incremental_purchases": 17.87,
  "lift_vs_blanket": 4.22,
  "blanket_cost_for_same_result": null,
  "savings_vs_blanket": null,
  "objective": "lower_confidence_bound",
  "customers_per_discount": {"10": 12, "20": 244},
  "allocation": [
    {"customer_id": 4019, "discount": 20, "expected_uplift": 0.682,
     "cautious_uplift": 0.5649, "cost": 20}
  ]
}
```

How to use the fields:
- `allocation` is the "Prescription" table for the Allocation Matrix. It is sorted by `cautious_uplift`, highest first. Customers who get no coupon are not listed.
- **Show `cautious_uplift`, not `expected_uplift`.** Validation on our synthetic data showed the point estimates run high at the top end (some reach 0.8, when the true maximum effect is about 0.5). `cautious_uplift` is the lower 95% bound and is safer to display.
- **Headline numbers:** use `cautious_incremental_purchases` ("at least about 40 extra purchases") rather than `expected_incremental_purchases`. In validation the true figure was 60.4 against an estimate of 75.4, so the point estimate runs about 25% high.
- `lift_vs_blanket` compares the optimizer with random $10 coupons at the same budget. It is 4.2x by the model's own estimates, and about 3.3x when checked against the true effects, so say "about 3x" rather than "4.2x".
- `savings_vs_blanket` is `null` whenever matching the optimizer's result with blanket $10 coupons would cost more than giving every customer a coupon. That is the case here (it would need about $21,000), so for the natural-language summary use `lift_vs_blanket` instead ("4x more extra purchases than blanket coupons for the same budget"), and show the savings sentence only when the field is not null.
- Constraints you can rely on: `total_cost <= budget`, and every listed customer has `cautious_uplift > 0`, so Sleeping Dogs never appear.

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
