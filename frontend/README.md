# EconoCasual — Customer Intelligence Dashboard (frontend prototype)

A responsive dashboard that shows who buys, how engagement relates to buying, and how discounts line up with purchases.

## Run
Open `index.html` in a browser. There are no dependencies: charts are inline SVG, and only the Google Fonts are loaded online (the page falls back to system fonts offline).

## Files
- `index.html` — page structure
- `style.css` — layout and visual design (tokens at the top of the file)
- `script.js` — seeded sample data, calculations, SVG charts, table, CSV export

## What it shows
- A live headline that rewrites itself for the selected customer group
- Purchase rate by engagement score, split by discount, with customer counts so thin data is visible
- Discount comparison, including the gap among customers with similar engagement
- Purchase rate by past purchases, plain-language readout, sortable and searchable customer table, CSV export

## Data
1,000 synthetic records with the fields `customer_id`, `previous_purchases`, `engagement`, `discount`, `purchase`. The data is generated with a fixed seed, so results are the same on every load.

## Limitation
All comparisons are descriptive. Customers were not randomly assigned discounts, so the dashboard does not claim that a discount caused a purchase. No prediction model is connected yet; backend integration is future work.
