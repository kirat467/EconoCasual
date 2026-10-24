/* EconoCausal: budget allocation section.
   Reads customers from script.js (window.ECONO_APP). Uses backend fields `ite` and
   `recommended_discount` when present, otherwise the in-browser model's estimate. */
(() => {
  "use strict";
  const app = window.ECONO_APP;
  if (!app) return;

  const $ = (id) => document.getElementById(id);
  const fmt = (n) => n.toLocaleString("en-IN");
  const inr = (n) => "₹" + fmt(Math.round(n));
  const one = (n) => n.toLocaleString("en-IN", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  const idLabel = (id) => "CUST-" + String(id).padStart(4, "0");
  const mean = (a) => a.reduce((x, y) => x + y, 0) / (a.length || 1);
  const NS = "http://www.w3.org/2000/svg";
  const MAX_MONEY = 1e9, PAGE = 10;
  let result = null, last = null, page = 0;

  /* ---------- Input validation ---------- */
  function parseMoney(raw, name) {
    const s = String(raw).replace(/[₹,\s]/g, "");
    if (!s) return { err: `Enter a ${name.toLowerCase()}.` };
    if (s[0] === "-") return { err: `${name} cannot be negative.` };
    if (!/^\d+(\.\d+)?$/.test(s)) return { err: "Use numbers only, for example 50000." };
    const n = Number(s);
    if (n <= 0) return { err: `${name} must be greater than 0.` };
    if (n > MAX_MONEY) return { err: `${name} is too large (maximum ${inr(MAX_MONEY)}).` };
    return { n };
  }
  function validate() {
    const b = parseMoney($("bBudget").value, "Budget"), d = parseMoney($("bDisc").value, "Discount per customer");
    let dErr = d.err;
    if (!b.err && !d.err && d.n > b.n) dErr = "Discount per customer cannot be more than the budget.";
    $("bBudgetErr").textContent = b.err || "";
    $("bDiscErr").textContent = dErr || "";
    $("bBudget").classList.toggle("bad", !!b.err);
    $("bDisc").classList.toggle("bad", !!dErr);
    $("bBudget").setAttribute("aria-invalid", String(!!b.err));
    $("bDisc").setAttribute("aria-invalid", String(!!dErr));
    return b.err || dErr ? null : { budget: b.n, disc: d.n };
  }

  /* ---------- Allocation: highest estimated effect first, while the budget lasts ---------- */
  function allocate(budget, disc) {
    const customers = app.customers(), model = app.model();
    const rows = customers.map((c) => {
      const ite = Number.isFinite(c.ite) ? c.ite
        : model.predict(c.engagement, c.previous_purchases, 1) - model.predict(c.engagement, c.previous_purchases, 0);
      const cost = Number.isFinite(c.recommended_discount) ? c.recommended_discount : disc;
      return { c, ite, cost };
    }).sort((a, b) => b.ite - a.ite || a.c.customer_id - b.c.customer_id);
    let spent = 0;
    const chosen = [];
    for (const r of rows) {
      if (r.ite <= 0) break;
      if (r.cost <= 0 || spent + r.cost > budget) continue;
      spent += r.cost;
      chosen.push({ ...r, running: spent });
    }
    const gain = chosen.reduce((a, r) => a + r.ite, 0);
    return {
      rows, chosen, spent, budget, disc, gain,
      n: rows.length,
      blanketCost: rows.reduce((a, r) => a + r.cost, 0),
      blanketGain: rows.reduce((a, r) => a + r.ite, 0),
      avgIte: mean(rows.map((r) => r.ite)),
      fromBackend: customers.some((c) => Number.isFinite(c.ite)),
    };
  }

  /* ---------- SVG helpers ---------- */
  const el = (tag, attrs, text) => {
    const e = document.createElementNS(NS, tag);
    Object.keys(attrs).forEach((k) => e.setAttribute(k, attrs[k]));
    if (text != null) e.textContent = text;
    return e;
  };
  const txt = (x, y, t, anchor) => el("text", { x, y, "text-anchor": anchor || "middle", "font-size": 12, style: "fill:var(--ink-3)" }, t);
  const line = (x1, y1, x2, y2, style) => el("line", { x1, y1, x2, y2, style });

  function drawUplift(r) {
    const svg = $("bUplift");
    svg.replaceChildren();
    const W = 600, H = 300, L = 56, R = 14, T = 16, B = 44, n = r.n;
    const pts = [[0, 0]];
    let cum = 0;
    const step = Math.max(1, Math.floor(n / 120));
    r.rows.forEach((x, i) => { cum += x.ite; if ((i + 1) % step === 0 || i === n - 1) pts.push([(i + 1) / n, cum]); });
    const ys = pts.map((p) => p[1]).concat([0, cum]);
    const lo = Math.min(...ys), hi = Math.max(...ys), span = hi - lo || 1;
    const X = (f) => L + f * (W - L - R), Y = (v) => T + (1 - (v - lo) / span) * (H - T - B);
    const grid = "stroke:var(--rule);stroke-width:1";
    [0, 0.25, 0.5, 0.75, 1].forEach((f) => {
      svg.appendChild(line(X(f), T, X(f), H - B, grid));
      svg.appendChild(txt(X(f), H - B + 18, Math.round(f * 100) + "%"));
    });
    [lo, hi].concat(lo < 0 && hi > 0 ? [0] : []).forEach((v) => {
      svg.appendChild(line(L, Y(v), W - R, Y(v), grid));
      svg.appendChild(txt(L - 6, Y(v) + 4, one(v), "end"));
    });
    svg.appendChild(txt((L + W - R) / 2, H - 6, "Share of customers targeted (highest estimated effect first)"));
    if (r.chosen.length) {
      const f = r.chosen.length / n;
      svg.appendChild(line(X(f), T, X(f), H - B, "stroke:var(--teal);stroke-width:1.5;stroke-dasharray:4 4"));
      svg.appendChild(txt(Math.min(X(f) + 4, W - 70), T + 12, "Budget limit", "start"));
    }
    svg.appendChild(line(X(0), Y(0), X(1), Y(cum), "stroke:var(--amber);stroke-width:2;stroke-dasharray:6 5"));
    svg.appendChild(el("polyline", { points: pts.map((p) => X(p[0]).toFixed(1) + "," + Y(p[1]).toFixed(1)).join(" "), style: "fill:none;stroke:var(--teal);stroke-width:2.5" }));
    svg.appendChild(el("rect", { x: L + 8, y: T + 4, width: 10, height: 10, style: "fill:var(--teal)" }));
    svg.appendChild(txt(L + 24, T + 13, "Ranked by estimated effect", "start"));
    svg.appendChild(el("rect", { x: L + 8, y: T + 22, width: 10, height: 10, style: "fill:var(--amber)" }));
    svg.appendChild(txt(L + 24, T + 31, "Random rollout", "start"));
  }

  function drawHist(r) {
    const svg = $("bHist");
    svg.replaceChildren();
    const W = 600, H = 300, L = 48, R = 14, T = 16, B = 44, BINS = 20;
    const vals = r.rows.map((x) => x.ite * 100);
    let lo = Math.min(...vals), hi = Math.max(...vals);
    if (hi - lo < 1e-9) { lo -= 0.5; hi += 0.5; }
    const w = (hi - lo) / BINS, counts = Array(BINS).fill(0);
    vals.forEach((v) => { counts[Math.min(BINS - 1, Math.floor((v - lo) / w))]++; });
    const top = Math.max(...counts, 1);
    const X = (v) => L + ((v - lo) / (hi - lo)) * (W - L - R), Y = (c) => T + (1 - c / top) * (H - T - B);
    counts.forEach((c, i) => {
      const x0 = X(lo + i * w), x1 = X(lo + (i + 1) * w), mid = lo + (i + 0.5) * w;
      svg.appendChild(el("rect", { x: x0 + 1, y: Y(c), width: Math.max(1, x1 - x0 - 2), height: H - B - Y(c), style: "fill:" + (mid > 0 ? "var(--teal)" : "var(--amber)") }));
    });
    svg.appendChild(line(L, H - B, W - R, H - B, "stroke:var(--ink-3);stroke-width:1"));
    if (lo < 0 && hi > 0) svg.appendChild(line(X(0), T, X(0), H - B, "stroke:var(--ink);stroke-width:1;stroke-dasharray:3 3"));
    [lo, (lo + hi) / 2, hi].forEach((v, i) => svg.appendChild(txt(X(v), H - B + 18, one(v), i === 0 ? "start" : i === 2 ? "end" : "middle")));
    svg.appendChild(txt(L - 6, Y(top) + 4, fmt(top), "end"));
    svg.appendChild(txt(L - 6, H - B + 4, "0", "end"));
    svg.appendChild(txt((L + W - R) / 2, H - 6, "Estimated effect on chance of buying (percentage points)"));
  }

  /* ---------- Rendering ---------- */
  function summary(r) {
    const k = r.chosen.length;
    if (!k) {
      return r.rows.every((x) => x.ite <= 0)
        ? "No customer has a positive estimated effect, so no discount is recommended."
        : `The budget of ${inr(r.budget)} is too small for even one discount of ${inr(r.disc)}.`;
    }
    const rnd = k * r.avgIte;
    let t = `Spending ${inr(r.spent)} on discounts for ${fmt(k)} customer${k === 1 ? "" : "s"} is expected to bring about ${one(r.gain)} extra purchases.`;
    if (rnd > 0) t += ` The same number of discounts given to randomly chosen customers would bring about ${one(rnd)} (the ranked list gives ${(r.gain / rnd).toFixed(1)}× as many).`;
    const saved = r.blanketCost - r.spent;
    if (saved > 0) t += ` Discounting all ${fmt(r.n)} customers would cost ${inr(r.blanketCost)}, so this strategy saves ${inr(saved)} compared to blanket targeting`;
    if (saved > 0 && r.blanketGain > 0) {
      const share = (r.gain / r.blanketGain) * 100;
      t += share > 100 ? " and gives more extra purchases, because customers with a negative effect are left out." : ` while keeping ${share < 1 ? "less than 1" : share.toFixed(0)}% of its extra purchases.`;
    } else if (saved > 0) t += ".";
    return t;
  }

  function renderTable() {
    const rows = result.chosen, pages = Math.max(1, Math.ceil(rows.length / PAGE));
    page = Math.min(page, pages - 1);
    const view = rows.slice(page * PAGE, page * PAGE + PAGE);
    $("bRows").innerHTML = view.length ? view.map((x) =>
      `<tr><td>${idLabel(x.c.customer_id)}</td><td class="num">${x.c.engagement}/10</td><td class="num">${x.c.previous_purchases}</td>` +
      `<td class="num">+${one(x.ite * 100)} pts</td><td class="num">${inr(x.cost)}</td><td class="num">${inr(x.running)}</td></tr>`).join("")
      : '<tr><td colspan="6" class="b-empty">No discounts recommended for these inputs.</td></tr>';
    $("bPageInfo").textContent = rows.length ? `${fmt(page * PAGE + 1)}–${fmt(page * PAGE + view.length)} of ${fmt(rows.length)}` : "0 selected";
    $("bPrev").disabled = page === 0;
    $("bNext").disabled = page >= pages - 1;
    $("bExport").disabled = !rows.length;
  }

  function render(r) {
    result = r;
    const k = r.chosen.length, used = r.budget ? (r.spent / r.budget) * 100 : 0;
    const card = (label, value, note) => `<div class="b-card"><span>${label}</span><strong>${value}</strong><small>${note}</small></div>`;
    $("bCards").innerHTML =
      card("Customers selected", fmt(k), `of ${fmt(r.n)} customers`) +
      card("Budget", inr(r.budget), "entered above") +
      card("Allocated", inr(r.spent), `${used.toFixed(1)}% of the budget`) +
      card("Remaining", inr(r.budget - r.spent), "not spent") +
      card("Extra purchases", k ? one(r.gain) : "0.0", "expected, from the estimates");
    $("bSummary").textContent = summary(r);
    $("bUsage").innerHTML =
      `<li class="with"><div class="row"><span>Allocated</span><b>${inr(r.spent)}</b></div><div class="track"><span class="fill" style="width:${Math.min(100, used)}%"></span></div></li>` +
      `<li class="without"><div class="row"><span>Remaining</span><b>${inr(r.budget - r.spent)}</b></div><div class="track"><span class="fill" style="width:${Math.max(0, 100 - used)}%"></span></div><small>Budget utilization: ${used.toFixed(1)}%</small></li>`;
    $("bSource").textContent = r.fromBackend
      ? "Estimated effects come from the backend model."
      : "Estimated effects come from the small in-browser model on this data (a demonstration). A backend model replaces them when connected.";
    drawUplift(r); drawHist(r); renderTable();
  }

  function run() {
    const v = validate();
    if (!v) return false;
    last = v; page = 0;
    render(allocate(v.budget, v.disc));
    return true;
  }

  /* ---------- Simple data-shift check against the built-in sample ---------- */
  function drift() {
    const box = $("bDrift"), cur = app.customers(), ref = app.sample();
    box.classList.remove("warn");
    if (!app.usingCustom()) { box.textContent = "Data check: this is the built-in reference sample, so no shift is expected."; return; }
    const stat = (rows, f) => { const m = mean(rows.map(f)); return { m, sd: Math.sqrt(mean(rows.map((c) => (f(c) - m) ** 2))) || 1 }; };
    const checks = [["engagement", (c) => c.engagement, "points"], ["past purchases", (c) => c.previous_purchases, "purchases"], ["discount share", (c) => c.discount, ""]];
    const flags = [];
    checks.forEach(([name, f, unit]) => {
      const a = stat(ref, f), b = stat(cur, f), d = b.m - a.m;
      if (Math.abs(d) / a.sd > 0.25) flags.push(name === "discount share" ? `share of customers offered a discount is ${Math.abs(d * 100).toFixed(0)} points ${d > 0 ? "higher" : "lower"}` : `average ${name} is ${Math.abs(d).toFixed(1)} ${unit} ${d > 0 ? "higher" : "lower"}`);
    });
    if (flags.length) {
      box.classList.add("warn");
      box.textContent = `Data shift: compared with the reference sample, ${flags.join("; ")}. Estimates may be less reliable for this data.`;
    } else box.textContent = "Data check: the customer profile is similar to the reference sample (simple comparison of averages).";
  }

  /* ---------- Events ---------- */
  $("bForm").addEventListener("submit", (e) => {
    e.preventDefault();
    const btn = $("bRun");
    if (btn.disabled || !validate()) return;
    btn.disabled = true; btn.textContent = "Calculating…"; btn.setAttribute("aria-busy", "true");
    setTimeout(() => {
      try { run(); } finally { btn.disabled = false; btn.textContent = "Run analysis"; btn.removeAttribute("aria-busy"); }
    }, 250);
  });
  ["bBudget", "bDisc"].forEach((id) => $(id).addEventListener("input", () => { $(id).classList.remove("bad"); $(id + "Err").textContent = ""; if (id === "bBudget") $("bDiscErr").textContent = ""; }));
  $("bPrev").addEventListener("click", () => { page = Math.max(0, page - 1); renderTable(); });
  $("bNext").addEventListener("click", () => { page += 1; renderTable(); });
  $("bExport").addEventListener("click", () => {
    if (!result || !result.chosen.length) return;
    const csv = "customer_id,estimated_effect,recommended_discount\n" +
      result.chosen.map((x) => `${x.c.customer_id},${x.ite.toFixed(4)},${x.cost}`).join("\n") + "\n";
    const url = URL.createObjectURL(new Blob(["\ufeff" + csv], { type: "text/csv;charset=utf-8" }));
    const a = document.createElement("a");
    a.href = url; a.download = "econocausal-allocation.csv";
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  // New data (upload, sample reset or API): refresh with the last valid inputs
  document.addEventListener("econo:data", () => {
    drift();
    if (last) { page = 0; render(allocate(last.budget, last.disc)); }
  });

  drift();
  run();
})();
