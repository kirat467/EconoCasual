# Frontend Integration Guide: show the causal model results on the dashboard

**For:** Kailash (Member 3) | **From:** Sharath (Member 2)

Your dashboard already runs on its own. This guide adds one new section, **"Causal model results"**, with the **uplift curve**, the **budget optimizer** (the allocation table), a table of every customer's **individual effect** (with a segment filter and sorting) and a **data-drift warning**, all read from the model API. Nothing in your existing code changes. You add one HTML block, one new file, one CSS block and one script line, and you commit them yourself on your `Member-3` branch.

I tested these exact snippets on a copy of your current `frontend/` files, against the running API. The section loaded with no console errors, in both light and dark mode.

## 1. Start the API (once, to try it)
From the repository root:
```bash
pip install -r backend/requirements-api.txt
python backend/server.py
```
It serves everything on `http://localhost:8000`. Open `http://localhost:8000/api/health` and check it says `"status": "ok"`.

## 2. Point the dashboard at it
In `frontend/config.js`:
```js
window.ECONO_CONFIG = { apiBase: "http://localhost:8000" };
```
Your dashboard then shows "Live data from the API: 1,000 customers". Leave `apiBase` empty when you deploy without a backend. The new section will just show a note.

## 3. Add the HTML
In `frontend/index.html`, paste this block **just above** the line `<section class="wrap records" id="customers" ...>`:
```html
  <section class="wrap predict" id="causal" aria-labelledby="causal-title">
    <div class="sec-head">
      <h2 id="causal-title">Causal model results</h2>
      <p>Who a discount actually changes, from the Double ML model. Needs the model API: set <code>apiBase</code> in <code>config.js</code>.</p>
    </div>
    <div id="causalDrift"></div>
    <div class="causal-grid">
      <div class="causal-card">
        <h3>Uplift curve</h3>
        <div id="causalQini"></div>
        <p class="source" id="causalQiniNote"></p>
      </div>
      <div class="causal-card">
        <h3>Budget optimizer</h3>
        <div class="causal-row">
          <label>Budget ($) <input id="causalBudget" type="number" min="1" step="500" value="5000"></label>
          <button type="button" id="causalGo">Optimize</button>
        </div>
        <p id="causalSummary" class="source"></p>
        <table class="causal-table"><thead><tr><th>Customer</th><th>Coupon</th><th>Cautious uplift</th></tr></thead><tbody id="causalRows"></tbody></table>
      </div>
    </div>
  </section>
```
Then add one line next to your other scripts, after `budget.js`:
```html
<script src="model-views.js"></script>
```

## 4. Add the new file `frontend/model-views.js`
```js
/* Causal model results: reads the model API and fills the #causal section.
   Needs window.ECONO_CONFIG.apiBase (see config.js). With no apiBase it shows a note and stops. */
(function () {
  const $ = (id) => document.getElementById(id);
  if (!$("causal")) return;
  const base = ((window.ECONO_CONFIG || {}).apiBase || "").replace(/\/$/, "");
  if (!base) { $("causalSummary").textContent = "Set apiBase in config.js to load the causal model results."; return; }

  async function get(path, options) {
    const res = await fetch(base + path, options);
    const body = await res.json();
    if (!res.ok) throw new Error(body.error || res.statusText);
    return body;
  }
  const pts = (v) => (v * 100).toFixed(1) + " pts";

  function drawQini(d) {
    const W = 560, H = 260, L = 40, R = 24, T = 10, B = 28;
    const all = d.model.qini.concat(d.random.qini), top = Math.max(...all) * 1.08, low = Math.min(0, ...all);
    const x = (v) => L + v * (W - L - R), y = (v) => T + (1 - (v - low) / (top - low)) * (H - T - B);
    const line = (s, cls) => `<polyline class="${cls}" fill="none" stroke-width="2.5" points="${s.x.map((v, i) => x(v) + "," + y(s.qini[i])).join(" ")}"/>`;
    let grid = "";
    for (let i = 0; i <= 4; i++) { const v = low + (top - low) * i / 4;
      grid += `<line x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}" class="cq-grid"/><text x="${L - 6}" y="${y(v) + 4}" text-anchor="end" class="cq-text">${v.toFixed(0)}</text>`;
      grid += `<text x="${x(i / 4)}" y="${H - 8}" text-anchor="middle" class="cq-text">${i * 25}%</text>`; }
    $("causalQini").innerHTML = `<svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="Uplift curve: model against random targeting">${grid}${line(d.random, "cq-random")}${line(d.model, "cq-model")}</svg>`
      + `<p class="cq-legend"><span class="cq-key cq-model-key"></span>Model <span class="cq-key cq-random-key"></span>Random</p>`;
    $("causalQiniNote").textContent = `Customers targeted, best-ranked first (x), against extra purchases caused (y). The further the model line is above random, the better the targeting. Qini coefficient ${d.qini_coefficient}.`;
  }

  async function optimize() {
    try {
      const r = await get("/api/optimize", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ budget: Number($("causalBudget").value) }) });
      $("causalSummary").textContent = r.summary;
      $("causalRows").innerHTML = r.allocation.slice(0, 10).map((a) => `<tr><td>${a.customer_id}</td><td>$${a.discount}</td><td>${pts(a.cautious_uplift)}</td></tr>`).join("");
    } catch (e) { $("causalSummary").textContent = "Could not optimize: " + e.message; }
  }


  /* ---- Individual treatment effects: all customers, with a segment filter and sorting ---- */
  let ite = [], sortKey = "ite", sortDir = -1;
  function mountIteCard() {
    const grid = document.querySelector("#causal .causal-grid");
    const card = document.createElement("div");
    card.className = "causal-card causal-wide";
    card.innerHTML = `<h3>Individual effects (ITE)</h3>
      <p class="source">The estimated change in each customer's purchase chance from a $10 discount, with a 95% range.</p>
      <div class="causal-row">
        <label>Segment <select id="iteSeg"><option value="">All</option><option value="persuadable">Persuadable</option><option value="sure_thing">Sure thing</option><option value="lost_cause">Lost cause</option><option value="sleeping_dog">Sleeping dog</option></select></label>
        <span class="source" id="iteCount"></span>
      </div>
      <div class="causal-kpis" id="iteKpis"></div>
      <table class="causal-table"><thead><tr>
        <th data-k="customer_id">Customer</th><th data-k="baseline_prob">Buys anyway</th><th data-k="ite">Effect</th><th data-k="ci_lower">Low</th><th data-k="ci_upper">High</th><th data-k="segment">Segment</th>
      </tr></thead><tbody id="iteRows"></tbody></table>
      <p class="source">Click a column title to sort. Showing the first 15 matching customers.</p>`;
    grid.appendChild(card);
    $("iteSeg").addEventListener("change", renderIte);
    card.querySelectorAll("th[data-k]").forEach((th) => th.addEventListener("click", () => {
      sortDir = th.dataset.k === sortKey ? -sortDir : -1; sortKey = th.dataset.k; renderIte(); }));
  }
  function renderIte() {
    const seg = $("iteSeg").value;
    const rows = ite.filter((c) => !seg || c.segment === seg).sort((a, b) => (a[sortKey] > b[sortKey] ? 1 : -1) * sortDir);
    $("iteCount").textContent = `${rows.length.toLocaleString()} of ${ite.length.toLocaleString()} customers`;
    $("iteRows").innerHTML = rows.slice(0, 15).map((c) => `<tr><td>${c.customer_id}</td><td>${(c.baseline_prob * 100).toFixed(1)}%</td><td>${pts(c.ite)}</td><td>${pts(c.ci_lower)}</td><td>${pts(c.ci_upper)}</td><td>${c.segment.replace("_", " ")}</td></tr>`).join("");
  }

  async function load() {
    try {
      const [curve, drift, all] = await Promise.all([get("/api/uplift-curve"), get("/api/drift"), get("/api/ite")]);
      drawQini(curve);
      ite = all.customers;
      $("iteKpis").innerHTML = Object.entries(all.segment_counts).map(([k, v]) => `<span class="causal-kpi"><strong>${v}</strong> ${k.replace("_", " ")}</span>`).join("");
      renderIte();
      const bad = drift.features.filter((f) => f.drift).map((f) => f.name);
      $("causalDrift").innerHTML = drift.drift_detected
        ? `<p class="causal-warn"><strong>Data drift detected</strong> in ${bad.join(", ")}. The model's estimates may no longer be reliable. <em>(Example result: until there is a live data feed, the API returns a simulated shift.)</em></p>` : "";
      await optimize();
    } catch (e) { $("causalSummary").textContent = "Could not reach the model API: " + e.message; }
  }
  mountIteCard();
  $("causalGo").addEventListener("click", optimize);
  load();
})();
```

## 5. Add the CSS
Paste at the **end** of `frontend/style.css`. It uses your own colour tokens (`--teal`, `--amber`, `--surface` and so on), so dark mode follows automatically:
```css
/* Causal model results (uses the page's own colour tokens, so dark mode follows) */
.causal-grid { display: grid; grid-template-columns: 1.2fr 1fr; gap: 20px; margin-top: 18px; }
@media (max-width: 820px) { .causal-grid { grid-template-columns: 1fr; } }
.causal-card { background: var(--surface); border: 1px solid var(--rule); border-radius: 18px; padding: 22px; }
.causal-card h3 { margin: 0 0 10px; font-size: 18px; }
.causal-row { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; margin-bottom: 8px; }
.causal-row input { width: 110px; padding: 6px 10px; border: 1px solid var(--rule); border-radius: 8px; background: var(--paper); }
.causal-row button { padding: 7px 16px; border: 0; border-radius: 8px; background: var(--teal); color: #fff; }
.causal-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.causal-table th, .causal-table td { text-align: right; padding: 5px 8px; border-bottom: 1px solid var(--rule-soft); }
.causal-table th:first-child, .causal-table td:first-child { text-align: left; }
.causal-warn { background: var(--amber-soft); color: var(--amber-ink); border: 1px solid var(--amber); border-radius: 12px; padding: 10px 14px; margin: 14px 0 0; }
.cq-grid { stroke: var(--rule); }
.cq-text { fill: var(--ink-3); font-size: 11px; }
.cq-model { stroke: var(--teal); }
.cq-random { stroke: var(--ink-3); }
.cq-legend { font-size: 13px; color: var(--ink-3); margin: 4px 0 0; }
.cq-key { display: inline-block; width: 18px; height: 3px; margin: 0 5px 3px 10px; vertical-align: middle; }
.cq-model-key { background: var(--teal); } .cq-random-key { background: var(--ink-3); }

.causal-wide { grid-column: 1 / -1; }
.causal-card select { padding: 6px 10px; border: 1px solid var(--rule); border-radius: 8px; background: var(--paper); }
.causal-kpis { display: flex; gap: 10px; flex-wrap: wrap; margin: 6px 0 10px; }
.causal-kpi { border: 1px solid var(--rule); border-radius: 10px; padding: 4px 12px; font-size: 14px; color: var(--ink-2); }
.causal-table th[data-k] { cursor: pointer; }
.causal-table td:last-child, .causal-table th:last-child { text-align: left; }
.causal-grid > * { min-width: 0; }
.causal-card { overflow-x: auto; }
.causal-card .causal-table { min-width: 420px; }
```

## 6. Check it works
- With the API running, reload the dashboard. You should see the uplift curve with the model line above the random line, the optimizer table and the individual-effects table. Change the budget and press **Optimize**, pick a segment, and click a column title to sort.
- Stop the API and reload. The section should show a message, and the rest of the dashboard should still work.

## Things to know
- **Show the cautious figure.** The table uses `cautious_uplift` (the lower 95% bound). The point estimates run high, so don't show those as the headline.
- **The optimizer may spend less than the budget.** Past about $6,670 no customer has a cautious effect above zero, so it stops. Show `total_cost` if you display how much was used.
- **The drift banner is an example.** `GET /api/drift` returns a stored simulated shift, so it will always show. The banner says so. A real check needs the model's four features (`previous_purchases`, `engagement`, `price_sensitivity`, `age`), and your dashboard data only has two of them.
- **More endpoints** (`/api/ite` with segment filters, the full contract) are in `docs/api_contract.md`, and `docs/api_demo.html` shows a table of all 1,500 customers with filtering and sorting. That is the "Data Load" check in the brief, if you want to build it into the dashboard too.

Questions or something not working? Message me and we'll sort it out.
