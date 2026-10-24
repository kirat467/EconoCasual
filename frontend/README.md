# EconoCausal: customer intelligence dashboard (frontend prototype)

A responsive dashboard that shows who buys, how engagement relates to buying, and how discounts line up with purchases.

## Run
Open `index.html` in a browser. There are no dependencies: charts are plain DOM and SVG, and only the Google Fonts load online (the page falls back to system fonts offline).

## Deploy (GitHub Pages)
Push to `main`. In the repository go to Settings, then Pages, and set the source to "GitHub Actions". `.github/workflows/pages.yml` publishes the site on every push.

## Connect a backend
Set `apiBase` in `config.js`. The expected response is described in `docs/API.md`. With no `apiBase`, or if the server cannot be reached, the dashboard uses the built-in sample data.

## Files
- `config.js`: backend address (optional)
- `docs/API.md`: data contract for the backend
- `CONTRIBUTING.md`: branch and commit rules for the team
- `index.html`: page structure
- `style.css`: layout and visual design (colour tokens at the top)
- `script.js`: seeded sample data, statistics, charts, table, CSV export
- `budget.js`: budget allocation section (budget input, uplift curve, allocation table, summary, data-shift check)

## What it shows
- A headline that rewrites itself for the selected customer group
- One square per customer (1,000 in total), grouped by discount. Filled squares bought. Choosing a group fades everyone outside it, and hovering a square shows that customer
- Purchase rate by engagement score, split by discount, with customer counts so thin data is visible. Works with the keyboard (arrow keys) and redraws at the real screen width
- Discount comparison with a 95% range, so a small gap is not mistaken for a real pattern, plus the gap within similar engagement bands
- "Try a customer": sliders for engagement, past purchases and discount give an estimated chance of purchase from a logistic regression fitted in the browser (trained on 80% of the records, checked on the other 20%, compared with a simple guess), plus what similar real customers did
- Model check: accuracy, a simple-guess baseline and AUC, all measured on the 200 unseen records
- Shareable views: the group, outcome filter, search, sort and predictor values are stored in the page address, and "Copy link to this view" returns to the same state
- Click any customer ID in the table to load that customer into "Try a customer"
- Purchase rate by past purchases, a plain-language readout that changes with the data, a sortable and searchable table, and CSV export
- Extra table filters (engagement band, past purchases, discount). They sit in the same state as the search, so they work with paging, the shareable link and CSV export
- Confidence ranges use the Wilson score interval (Newcombe's method for gaps), which stays reliable for small groups
- Customer squares work with the keyboard: focus the panel, then use the arrow keys, Page Up/Down, Home and End
- Table page size (10, 25 or 50) and page number are saved in the shareable link
- "Download chart (PNG)" saves the engagement chart as an image
- CSV upload keeps your own `customer_id` when every value is a unique whole number from 1 to 9999
- With `apiBase` set, a status line shows while the server wakes up (60-second timeout, retry button)
- Data quality panel: checks every loaded record (missing and out-of-range values) and reports rows skipped when a CSV was uploaded
- "Reset view" button: puts the group, filters, sorting, predictor and discount share back to their defaults

- Visual polish: a dark "stage" panel for the customer squares with glowing buyers and a one-time scan sweep, a scroll-progress line in the header, and underline/stat-strip animations that play once when scrolled into view. All motion is turned off for people who prefer reduced motion
- Dark mode: follows the system setting, with a header toggle that remembers your choice
- Upload CSV: drop a file anywhere or use the header button. Columns are checked, the first 5 rows are previewed, invalid rows are counted, and nothing leaves the browser
- Who should get a discount: pick a share of customers and see the extra purchases the model expects when discounts go to the highest estimated lift versus no ranking. The target list exports to CSV

- Budget allocation: enter a budget and a discount per customer in rupees (empty, negative, non-numeric and too-large values show clear errors). Customers with the highest estimated effect get a discount while the budget lasts; customers with an effect of zero or below never do
- Summary cards (customers selected, budget, allocated, remaining, expected extra purchases), a budget utilization bar and a plain-language strategy summary that compares the plan with random targeting and with discounting everyone
- Uplift curve (ranked list vs random rollout, with the budget limit marked), a histogram of estimated effects, a paged allocation table and CSV export
- Data-shift check: compares the averages of an uploaded or live dataset with the built-in reference sample and warns when they differ a lot

## Optional backend fields
`GET {apiBase}/api/customers` may add two numeric fields per customer, both optional:
- `ite`: estimated individual treatment effect as a probability change, for example `0.08` for +8 points
- `recommended_discount`: discount in rupees chosen by the backend optimiser (0 means no discount)

When `ite` is present the dashboard uses it instead of its own in-browser estimate. Without these fields everything still works on the in-browser estimate.

## Data
1,000 synthetic records with the fields `customer_id`, `previous_purchases`, `engagement`, `discount`, `purchase`. The data is generated with a fixed seed, so results are the same on every load.

## Limitation
All comparisons are descriptive. Customers were not randomly assigned discounts, so the dashboard does not claim that a discount caused a purchase. The purchase estimate is a small in-browser model on synthetic data, so treat it as a demonstration; a backend model is future work.

## Roadmap
- Qini curve from real outcomes once the backend model supplies treatment effects
- Interaction term (engagement x discount) and adjusted-effect model
- Self-hosted fonts, unit tests for the statistics
- Calibration chart