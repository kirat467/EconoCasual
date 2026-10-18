# EconoCasual: customer intelligence dashboard (frontend prototype)

A responsive dashboard that shows who buys, how engagement relates to buying, and how discounts line up with purchases.

## Run
Open `index.html` in a browser. There are no dependencies: charts are plain DOM and SVG, and only the Google Fonts load online (the page falls back to system fonts offline).

## Files
- `index.html`: page structure
- `style.css`: layout and visual design (colour tokens at the top)
- `script.js`: seeded sample data, statistics, charts, table, CSV export

## What it shows
- A headline that rewrites itself for the selected customer group
- One square per customer (1,000 in total), grouped by discount. Filled squares bought. Choosing a group fades everyone outside it, and hovering a square shows that customer
- Purchase rate by engagement score, split by discount, with customer counts so thin data is visible. Works with the keyboard (arrow keys) and redraws at the real screen width
- Discount comparison with a 95% range, so a small gap is not mistaken for a real pattern, plus the gap within similar engagement bands
- "Try a customer": sliders for engagement, past purchases and discount give an estimated chance of purchase from a logistic regression fitted in the browser (trained on 800 records, checked on 200 unseen ones, compared with a simple guess), plus what similar real customers did
- Model check: accuracy, a simple-guess baseline and AUC, all measured on the 200 unseen records
- Shareable views: the group, outcome filter, search, sort and predictor values are stored in the page address, and "Copy link to this view" returns to the same state
- Click any customer ID in the table to load that customer into "Try a customer"
- Purchase rate by past purchases, a plain-language readout that changes with the data, a sortable and searchable table, and CSV export
- Extra table filters (engagement band, past purchases, discount). They sit in the same state as the search, so they work with paging, the shareable link and CSV export
- Data quality panel: checks every loaded record (missing and out-of-range values) and reports rows skipped when a CSV was uploaded
- "Reset view" button: puts the group, filters, sorting, predictor and discount share back to their defaults

- Dark mode: follows the system setting, with a header toggle that remembers your choice
- Upload CSV: drop a file anywhere or use the header button. Columns are checked, the first 5 rows are previewed, invalid rows are counted, and nothing leaves the browser
- Who should get a discount: pick a share of customers and see the extra purchases the model expects when discounts go to the highest estimated lift versus no ranking. The target list exports to CSV

## Data
1,000 synthetic records with the fields `customer_id`, `previous_purchases`, `engagement`, `discount`, `purchase`. The data is generated with a fixed seed, so results are the same on every load.

## Limitation
All comparisons are descriptive. Customers were not randomly assigned discounts, so the dashboard does not claim that a discount caused a purchase. The purchase estimate is a small in-browser model on synthetic data, so treat it as a demonstration; a backend model is future work.

## Roadmap
- Interaction term (engagement x discount) and adjusted-effect model
- Self-hosted fonts, unit tests for the statistics
- Calibration chart and chart export (PNG)
