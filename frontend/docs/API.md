# Backend data contract

The dashboard reads customers from one endpoint. Set `apiBase` in `config.js` to turn it on.

## Request
`GET {apiBase}/api/customers`
Header: `Accept: application/json`

The first request may take up to 60 seconds while a free-tier server wakes up. After that the dashboard shows a "Try again" button.

## Response
A JSON array. Each item is one customer.

| Field | Type | Required | Rules |
|---|---|---|---|
| `previous_purchases` | number | yes | whole number, 0 to 10 |
| `engagement` | number | yes | whole number, 0 to 10 |
| `discount` | number | yes | `0` (no discount) or `1` (discount offered) |
| `purchase` | number | yes | `0` (did not buy) or `1` (bought) |
| `ite` | number | no | estimated change in purchase probability, for example `0.08` for +8 points |
| `recommended_discount` | number | no | discount in rupees chosen by the backend optimiser, `0` means none |

Example:

```json
[
  { "previous_purchases": 3, "engagement": 7, "discount": 1, "purchase": 1, "ite": 0.08, "recommended_discount": 500 },
  { "previous_purchases": 0, "engagement": 2, "discount": 0, "purchase": 0 }
]
```

## Notes
- Rows that break a rule are skipped and counted in the Data quality panel.
- At most 5,000 rows are used.
- `customer_id` is assigned by the dashboard (1, 2, 3, ...) in the order received.
- Enable CORS for the site that serves the dashboard.
- All results are descriptive. The API must not claim that a discount caused a purchase.
