## Optional fields (budget allocation)

Each customer object in `GET /api/customers` may also include:

| Field | Type | Meaning |
|---|---|---|
| `ite` | number | Estimated individual treatment effect as a change in purchase probability, e.g. `0.08` = +8 points. If present, the dashboard uses it instead of its own in-browser estimate. |
| `recommended_discount` | number (rupees, >= 0) | Discount chosen by the backend optimiser. `0` means no discount. If absent, the "Discount per customer" value entered on the page is used. |

Both fields are optional. Rows are still validated on `engagement`, `previous_purchases`, `discount` and `purchase`.