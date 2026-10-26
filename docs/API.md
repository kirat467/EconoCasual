# Backend data contract

The dashboard works on its own with built-in sample data. To use live data, set `apiBase` in `config.js`, for example:

```js
window.ECONO_CONFIG = { apiBase: "https://econocausal-api.onrender.com" };
```

## Endpoint

`GET {apiBase}/api/customers`

Headers sent: `Accept: application/json`

The server must allow cross-origin requests (CORS) from the site that hosts the dashboard.

## Response

A JSON array. One object per customer:

```json
[
  {
    "engagement": 7,
    "previous_purchases": 3,
    "discount": 1,
    "purchase": 1,
    "ite": 0.08,
    "recommended_discount": 500
  }
]
```

| Field | Required | Type | Rule |
|---|---|---|---|
| `engagement` | yes | integer | 0 to 10 |
| `previous_purchases` | yes | number | 0 to 10 (rounded to a whole number) |
| `discount` | yes | 0 or 1 | 1 means a discount was offered |
| `purchase` | yes | 0 or 1 | 1 means the customer bought |
| `ite` | no | number | Estimated individual treatment effect as a probability change. `0.08` means +8 points |
| `recommended_discount` | no | number | Discount in rupees chosen by the backend optimiser. `0` means no discount |

## Behaviour

- Rows that fail the rules above are skipped and counted in the Data quality panel.
- If no row is valid, the dashboard keeps the sample data.
- At most 5,000 valid rows are used. `customer_id` is assigned by the dashboard (1, 2, 3, ...).
- `null`, missing or empty values are never treated as 0.
- If `ite` is present, budget allocation uses it. Otherwise it uses the in-browser model.
- If `recommended_discount` is present, it is used as that customer's cost. Otherwise the discount entered in the form is used.
- The first request can be slow on free hosting. The dashboard waits up to 60 seconds and then shows a retry button.
