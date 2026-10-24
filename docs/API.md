<<<<<<< HEAD
## Optional fields (budget allocation)

Each customer object in `GET /api/customers` may also include:

| Field | Type | Meaning |
|---|---|---|
| `ite` | number | Estimated individual treatment effect as a change in purchase probability, e.g. `0.08` = +8 points. If present, the dashboard uses it instead of its own in-browser estimate. |
| `recommended_discount` | number (rupees, >= 0) | Discount chosen by the backend optimiser. `0` means no discount. If absent, the "Discount per customer" value entered on the page is used. |

Both fields are optional. Rows are still validated on `engagement`, `previous_purchases`, `discount` and `purchase`.
=======
# Backend contract (what the frontend expects)

The frontend works without a backend (sample data). To connect one, set `apiBase` in `config.js`.

## GET /api/customers
Returns a JSON array. Each item:

| Field | Type | Rule |
|---|---|---|
| `customer_id` | any | ignored; the frontend numbers rows 1..n |
| `previous_purchases` | integer | 0 or more |
| `engagement` | integer | 0 to 10 |
| `discount` | 0 or 1 | 1 = offered a discount |
| `purchase` | 0 or 1 | 1 = bought |

```json
[{ "customer_id": 1, "previous_purchases": 3, "engagement": 7, "discount": 1, "purchase": 1 }]
```
Invalid rows are skipped and counted in the Data quality panel.

## CORS
The server must allow the frontend's origin (`Access-Control-Allow-Origin`), otherwise the browser blocks the request and the dashboard falls back to sample data.

## Planned endpoints (not used yet)
- `POST /api/predict` with `{engagement, previous_purchases, discount}` returning `{probability}`, to move the model server-side.
>>>>>>> origin/Member-3
