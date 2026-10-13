/* EconoCasual: customer intelligence dashboard
   Synthetic sample data, descriptive statistics only (no causal claims).
   Everything is drawn with plain DOM and SVG, so the page works without any CDN. */
(() => {
  "use strict";

  /* ---------- Sample data (repeatable: fixed seed) ---------- */
  function mulberry32(seed) {
    return function () {
      seed |= 0; seed = (seed + 0x6D2B79F5) | 0;
      let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  const rand = mulberry32(20260);
  const normal = (mean, sd) => {
    const u = 1 - rand(), v = rand();
    return mean + sd * Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
  };
  const clamp = (x, lo, hi) => Math.min(hi, Math.max(lo, x));

  const customers = Array.from({ length: 1000 }, (_, i) => {
    const engagement = Math.round(clamp(normal(5.2, 2.5), 0, 10));
    const previous_purchases = Math.round(clamp(normal(3.2 + engagement * 0.15, 2.4), 0, 10));
    // Low-engagement customers were a little more likely to get an offer.
    const discount = rand() < clamp(0.66 - engagement * 0.03, 0.2, 0.8) ? 1 : 0;
    const z = -2.5 + 0.30 * engagement + 0.13 * previous_purchases + 0.5 * discount;
    const purchase = rand() < 1 / (1 + Math.exp(-z)) ? 1 : 0;
    return { customer_id: i + 1, previous_purchases, engagement, discount, purchase };
  });

  /* ---------- Helpers ---------- */
  const $ = (id) => document.getElementById(id);
  const fmt = (n) => n.toLocaleString("en-IN");
  const pct = (r, d = 0) => (r == null ? "–" : (r * 100).toFixed(d) + "%");
  const rate = (rows) => (rows.length ? rows.filter((c) => c.purchase === 1).length / rows.length : null);
  const range = (n) => Array.from({ length: n }, (_, i) => i);
  const plural = (n, word) => `${fmt(n)} ${word}${n === 1 ? "" : "s"}`;
  const idLabel = (c) => "CUST-" + String(c.customer_id).padStart(4, "0");
  const MIN_N = 5; // groups smaller than this are never turned into a rate

  /* Signed difference in percentage points, e.g. "+8.2". Never prints "-0.0". */
  const pts = (x, d = 1) => {
    const s = Math.abs(x * 100).toFixed(d);
    return (Number(s) === 0 ? "" : x > 0 ? "+" : "−") + s;
  };

  const SEGMENTS = {
    all: (c) => true,
    high: (c) => c.engagement >= 7,
    low: (c) => c.engagement <= 3,
    repeat: (c) => c.previous_purchases >= 5,
  };

  const state = { seg: "all", search: "", outcome: "all", sort: "customer_id", dir: 1, page: 1, size: 10 };
  let toastTimer;
  let currentRows = customers;

  const segmentRows = () => customers.filter(SEGMENTS[state.seg]);
  const tableRows = () => {
    const q = state.search.replace(/\D/g, "");
    const rows = segmentRows().filter(
      (c) =>
        (!q || String(c.customer_id).padStart(4, "0").includes(q)) &&
        (state.outcome === "all" || String(c.purchase) === state.outcome)
    );
    const k = state.sort;
    return rows.sort((a, b) => (a[k] - b[k] || a.customer_id - b.customer_id) * state.dir);
  };

  /* ---------- Statistics ----------
     Gaps come with a 95% range (normal approximation), so a small difference
     built on a few customers is not mistaken for a real pattern. */
  const Z = 1.96;
  const rateMin = (rows) => (rows.length >= MIN_N ? rate(rows) : null);
  const varOf = (rows) => { const p = rate(rows); return (p * (1 - p)) / rows.length; };
  const split = (rows) => [rows.filter((c) => c.discount === 1), rows.filter((c) => c.discount === 0)];
  const span = (g) => [g.est - Z * g.se, g.est + Z * g.se];

  function overallGap(rows) {
    const [d, n] = split(rows);
    if (d.length < MIN_N || n.length < MIN_N) return null;
    return { est: rate(d) - rate(n), se: Math.sqrt(varOf(d) + varOf(n)) };
  }

  /* Discount gap after comparing customers within the same engagement band */
  function adjustedGap(rows) {
    const used = [];
    [[0, 3], [4, 6], [7, 10]].forEach(([lo, hi]) => {
      const g = rows.filter((c) => c.engagement >= lo && c.engagement <= hi);
      const [d, n] = split(g);
      if (d.length >= MIN_N && n.length >= MIN_N) used.push({ g, d, n });
    });
    const total = used.reduce((a, u) => a + u.g.length, 0);
    if (!total) return null;
    let est = 0, v = 0;
    used.forEach(({ g, d, n }) => {
      const w = g.length / total;
      est += w * (rate(d) - rate(n));
      v += w * w * (varOf(d) + varOf(n));
    });
    return { est, se: Math.sqrt(v), bands: used.length };
  }
  // The band-by-band figure only adds something when more than one band was compared.
  const bandGap = (rows) => { const a = adjustedGap(rows); return a && a.bands > 1 ? a : null; };

  /* ---------- One square per customer ---------- */
  const dotEls = [];
  const GROUPS = [
    { key: 1, cls: "with", name: "Offered a discount" },
    { key: 0, cls: "without", name: "No discount" },
  ];

  function buildPeople() {
    $("peopleGroups").innerHTML = GROUPS.map((g) => {
      const list = customers
        .filter((c) => c.discount === g.key)
        .sort((a, b) => b.purchase - a.purchase || a.customer_id - b.customer_id);
      const dots = list.map((c, i) =>
        `<i class="d ${c.purchase ? "b" : "n"}" data-id="${c.customer_id}" style="--i:${i}"></i>`).join("");
      return `<div class="grp ${g.cls}" style="flex:${list.length} 1 0%">` +
        `<div class="grp-head"><h3>${g.name}</h3><span class="grp-meta" id="meta${g.key}"></span></div>` +
        `<div class="dots">${dots}</div></div>`;
    }).join("");
    $("peopleGroups").querySelectorAll(".d").forEach((el) => { dotEls[Number(el.dataset.id) - 1] = el; });
  }

  function renderPeople(rows) {
    const inView = new Set(rows.map((c) => c.customer_id));
    customers.forEach((c, i) => dotEls[i].classList.toggle("out", !inView.has(c.customer_id)));
    GROUPS.forEach((g) => {
      const list = rows.filter((c) => c.discount === g.key);
      $("meta" + g.key).textContent = list.length
        ? `${pct(rate(list))} bought, ${plural(list.length, "customer")}`
        : "nobody in this group";
    });
  }

  const dotTip = $("dotTip");
  function showDotTip(el) {
    const c = customers[Number(el.dataset.id) - 1];
    const outside = el.classList.contains("out");
    dotTip.innerHTML =
      `<b>${idLabel(c)}</b> ${c.purchase ? "bought" : "did not buy"}<br>` +
      `Engagement ${c.engagement}/10, ${plural(c.previous_purchases, "past purchase")}, ` +
      `${c.discount ? "offered a discount" : "no discount"}` +
      (outside ? "<br>Outside the selected group" : "");
    dotTip.hidden = false;
    const fig = $("people").getBoundingClientRect(), r = el.getBoundingClientRect();
    const tw = dotTip.offsetWidth, th = dotTip.offsetHeight;
    const x = r.left - fig.left + r.width / 2 - tw / 2;
    dotTip.style.left = clamp(x, 0, Math.max(0, fig.width - tw)) + "px";
    const above = r.top - fig.top - th - 8;
    dotTip.style.top = (above >= 0 ? above : r.bottom - fig.top + 8) + "px";
  }
  const hideDotTip = () => { dotTip.hidden = true; };

  /* ---------- Hero + stats ---------- */
  function renderHero(rows) {
    const n = rows.length;
    const [d, nd] = split(rows);
    const bought = rows.filter((c) => c.purchase === 1).length;

    if (!n) {
      $("headline").textContent = "No customers in this group.";
      $("subline").textContent = "Pick another group above to see results.";
      ["sTotal", "sRate", "sEng", "sDisc"].forEach((id) => ($(id).textContent = "–"));
      ["sTotalNote", "sRateNote", "sDiscNote"].forEach((id) => ($(id).textContent = "\u00a0"));
      return;
    }

    const dr = rateMin(d), nr = rateMin(nd);
    $("headline").innerHTML =
      `${fmt(bought)} of ${fmt(n)} customers bought. ` +
      (dr != null && nr != null
        ? `With a discount, <span class="with">${pct(dr)}</span> did; without, <span class="without">${pct(nr)}</span>.`
        : "There is not enough discount data to compare.");

    const og = overallGap(rows), adj = bandGap(rows);
    let sub = "";
    if (og) {
      sub = Math.abs(og.est * 100) < 0.05
        ? "Customers offered a discount bought about as often as those who were not."
        : `Customers offered a discount bought ${Math.abs(og.est * 100).toFixed(1)} points ${og.est > 0 ? "more" : "less"} often.`;
      if (adj) sub += ` Among customers with similar engagement the difference is ${pts(adj.est)} points.`;
    }
    $("subline").textContent = sub;

    $("sTotal").textContent = fmt(n);
    $("sTotalNote").textContent = state.seg === "all" ? "full sample" : `of ${fmt(customers.length)} in the sample`;
    $("sRate").textContent = pct(bought / n, 1);
    $("sRateNote").textContent = `${fmt(bought)} purchases recorded`;
    $("sEng").textContent = (rows.reduce((a, c) => a + c.engagement, 0) / n).toFixed(1);
    $("sDisc").textContent = pct(d.length / n, 1);
    $("sDiscNote").textContent = plural(d.length, "customer");
  }

  /* ---------- Trend chart (SVG, drawn at the real pixel width) ---------- */
  let trend = null;
  let drawnWidth = 0;
  let kbScore = null;

  function renderTrend(rows) {
    const svg = $("trend");
    const wrapW = Math.round($("trendWrap").clientWidth);
    drawnWidth = wrapW;
    const W = Math.max(280, wrapW || 680);
    const H = Math.round(clamp(W * 0.5, 250, 340));
    const M = { l: W < 480 ? 38 : 46, r: 12, t: 14, b: 40 };
    const IW = W - M.l - M.r, IH = H - M.t - M.b;
    const xAt = (e) => M.l + (e / 10) * IW;
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);

    const series = [
      { key: 1, cls: "with", label: "With discount" },
      { key: 0, cls: "without", label: "No discount" },
    ].map((s) => ({
      ...s,
      pts: range(11).map((e) => {
        const g = rows.filter((c) => c.engagement === e && c.discount === s.key);
        return { e, n: g.length, r: rateMin(g) };
      }),
    }));

    const counts = range(11).map((e) => rows.filter((c) => c.engagement === e).length);
    const maxN = Math.max(...counts, 1);
    const vals = series.flatMap((s) => s.pts.map((p) => p.r)).filter((v) => v != null);
    const yMax = Math.min(1, Math.ceil((Math.max(...vals, 0.2) + 0.04) * 5) / 5);
    const yAt = (r) => M.t + IH - (r / yMax) * IH;
    const thin = series.reduce((a, s) => a + s.pts.filter((p) => p.n > 0 && p.n < MIN_N).length, 0);
    trend = { series, counts, xAt, W, thin };

    let out = "";
    for (let i = 0; i <= Math.round(yMax * 5); i++) {
      const v = i / 5;
      out += `<line class="grid" x1="${M.l}" x2="${W - M.r}" y1="${yAt(v)}" y2="${yAt(v)}"/>` +
             `<text x="${M.l - 8}" y="${yAt(v) + 4}" text-anchor="end">${Math.round(v * 100)}%</text>`;
    }
    counts.forEach((n, e) => {
      const h = (n / maxN) * 38, bw = (IW / 11) * 0.55;
      out += `<rect class="count" x="${xAt(e) - bw / 2}" y="${M.t + IH - h}" width="${bw}" height="${h}" rx="2"/>`;
    });
    out += `<line class="axis" x1="${M.l}" x2="${W - M.r}" y1="${M.t + IH}" y2="${M.t + IH}"/>`;
    range(11).forEach((e) => (out += `<text x="${xAt(e)}" y="${M.t + IH + 17}" text-anchor="middle">${e}</text>`));
    out += `<text x="${M.l + IW / 2}" y="${H - 3}" text-anchor="middle">Engagement score</text>`;

    series.forEach((s) => {
      let d = "", pen = false;
      s.pts.forEach((p) => {
        if (p.r == null) { pen = false; return; }
        d += `${pen ? "L" : "M"}${xAt(p.e).toFixed(1)} ${yAt(p.r).toFixed(1)} `;
        pen = true;
      });
      out += `<path class="ln ${s.cls}" d="${d}"/>`;
      s.pts.forEach((p) => {
        if (p.r != null) out += `<circle class="dot ${s.cls}" cx="${xAt(p.e)}" cy="${yAt(p.r)}" r="3.5"/>`;
      });
    });
    out += `<line class="guide" id="guide" y1="${M.t}" y2="${M.t + IH}" visibility="hidden"/>`;
    svg.innerHTML = out;
    $("tip").hidden = true;
    kbScore = null;

    // Text alternative for screen readers
    const hi = rows.filter((c) => c.engagement >= 7), lo = rows.filter((c) => c.engagement <= 3);
    $("trendDesc").textContent =
      `Line chart of purchase rate by engagement score. Customers scoring 7 to 10 buy at ${pct(rateMin(hi))}, ` +
      `customers scoring 0 to 3 buy at ${pct(rateMin(lo))}. Points with fewer than ${MIN_N} customers are hidden. ` +
      `With the chart focused, use the left and right arrow keys to read each score.`;
  }

  function showTrendTip(e) {
    if (!trend) return;
    const g = $("guide"), tip = $("tip");
    g.setAttribute("x1", trend.xAt(e)); g.setAttribute("x2", trend.xAt(e)); g.setAttribute("visibility", "visible");

    const line = (s, cls) => {
      const p = s.pts[e];
      return `<div><span class="${cls}">${s.label}:</span> ${p.r == null ? "too few customers" : `<b>${pct(p.r)}</b>`} (${plural(p.n, "customer")})</div>`;
    };
    tip.innerHTML = `<div><b>Engagement ${e}</b>, ${plural(trend.counts[e], "customer")} in all</div>` +
      line(trend.series[0], "t-with") + line(trend.series[1], "t-without");
    tip.hidden = false;

    const wrapW = $("trendWrap").clientWidth, tw = tip.offsetWidth;
    const px = (trend.xAt(e) / trend.W) * wrapW;
    const left = px < wrapW / 2 ? px + 14 : px - tw - 14;
    tip.style.left = clamp(left, 0, Math.max(0, wrapW - tw)) + "px";
  }
  function hideTrendTip() {
    $("tip").hidden = true;
    const g = $("guide");
    if (g) g.setAttribute("visibility", "hidden");
  }
  function scoreAt(ev) {
    const box = $("trend").getBoundingClientRect();
    const M_l = trend.xAt(0), IW = trend.xAt(10) - M_l;
    const vx = ((ev.clientX - box.left) / box.width) * trend.W;
    return clamp(Math.round(((vx - M_l) / IW) * 10), 0, 10);
  }

  /* ---------- Discount comparison, past purchases, notes ---------- */
  function renderCompare(rows) {
    const [d, nd] = split(rows);
    const item = (cls, label, g) => {
      const r = rateMin(g);
      return `<li class="${cls}"><div class="row"><span>${label}</span><b>${pct(r, 1)}</b></div>` +
        `<div class="track"><span class="fill" style="width:${(r || 0) * 100}%"></span></div>` +
        `<small>${plural(g.length, "customer")}${r == null && g.length ? ", too few to compare" : ""}</small></li>`;
    };
    $("compare").innerHTML = item("with", "Offered a discount", d) + item("without", "No discount", nd);

    const og = overallGap(rows), adj = bandGap(rows);
    if (!og) { $("gapLine").innerHTML = "<p>Not enough customers in both groups to compare.</p>"; return; }

    const [lo, hi] = span(og);
    let html = `<p><strong>${pts(og.est)} points</strong> overall</p>` +
      `<p>Plausible range ${pts(lo)} to ${pts(hi)} points (95% interval).` +
      (lo <= 0 && hi >= 0 ? " The range includes zero, so this gap could be down to chance." : "") + `</p>`;
    if (adj) {
      const [alo, ahi] = span(adj);
      html += `<p><b>${pts(adj.est)} points</b> when customers are compared within low (0–3), mid (4–6) and high (7–10) engagement bands. Range ${pts(alo)} to ${pts(ahi)}.</p>`;
    }
    $("gapLine").innerHTML = html;
  }

  function renderPrev(rows) {
    const overall = rate(rows);
    const bands = [[0, 2, "0–2 past purchases"], [3, 5, "3–5 past purchases"], [6, 8, "6–8 past purchases"], [9, 10, "9–10 past purchases"]];
    $("prevBars").innerHTML = bands.map(([lo, hi, label]) => {
      const g = rows.filter((c) => c.previous_purchases >= lo && c.previous_purchases <= hi);
      const r = rateMin(g);
      return `<li><span class="k">${label}</span>` +
        `<span class="track"><span class="fill" style="width:${(r || 0) * 100}%"></span>` +
        (overall != null ? `<span class="avg" style="left:${overall * 100}%"></span>` : "") + `</span>` +
        `<span class="v">${pct(r)}</span>` +
        `<span class="n">${plural(g.length, "customer")}${r == null && g.length ? ", too few to compare" : ""}</span></li>`;
    }).join("");
  }

  function renderNotes(rows) {
    const n = rows.length;
    if (!n) { $("notes").innerHTML = "<li>No customers in this group.</li>"; return; }
    const items = [];

    // Engagement
    const hi = rows.filter((c) => c.engagement >= 7), lo = rows.filter((c) => c.engagement <= 3);
    if (hi.length >= MIN_N && lo.length >= MIN_N) {
      const diff = rate(hi) - rate(lo);
      const lead = diff > 0.05 ? "Engaged customers buy more often." : diff < -0.05 ? "Engaged customers buy less often here." : "Engagement makes little difference here.";
      items.push(`<b>${lead}</b> Customers scoring 7–10 bought at ${pct(rate(hi))}; those scoring 0–3 bought at ${pct(rate(lo))}.`);
    }

    // Repeat customers
    const buyers = rows.filter((c) => c.purchase === 1);
    const rep = rows.filter((c) => c.previous_purchases >= 5);
    if (state.seg !== "repeat" && buyers.length && rep.length >= MIN_N) {
      const shareBuyers = rep.filter((c) => c.purchase === 1).length / buyers.length;
      const shareGroup = rep.length / n;
      const lead = shareBuyers > shareGroup + 0.03 ? "Repeat customers account for more than their share of sales."
        : shareBuyers < shareGroup - 0.03 ? "Repeat customers account for less than their share of sales."
        : "Repeat customers buy in line with their numbers.";
      items.push(`<b>${lead}</b> Customers with 5 or more past purchases are ${pct(shareGroup)} of this group and ${pct(shareBuyers)} of recorded purchases.`);
    }

    // Discount
    const og = overallGap(rows);
    if (og) {
      const [lo95, hi95] = span(og);
      const unclear = lo95 <= 0 && hi95 >= 0;
      const adj = bandGap(rows);
      items.push(unclear
        ? `<b>The discount gap is too close to call.</b> It is ${pts(og.est)} points, but the plausible range runs from ${pts(lo95)} to ${pts(hi95)}.` +
          (adj ? ` Comparing similar engagement levels gives ${pts(adj.est)} points.` : "")
        : `<b>Customers offered a discount bought ${og.est > 0 ? "more" : "less"} often.</b> The gap is ${pts(og.est)} points (range ${pts(lo95)} to ${pts(hi95)}).` +
          (adj ? ` Within similar engagement levels it is ${pts(adj.est)} points, which is the fairer comparison.` : ""));
    }

    // Thin data
    if (trend && trend.thin > 0)
      items.push(`<b>Some chart points are left out.</b> ${trend.thin} score and discount combinations have fewer than ${MIN_N} customers, so no rate is drawn for them.`);

    $("notes").innerHTML = items.map((t) => `<li>${t}</li>`).join("") || "<li>Not enough data in this group for a readout.</li>";
  }

  /* ---------- Table ---------- */
  function renderTable() {
    const rows = tableRows();
    const pages = Math.max(1, Math.ceil(rows.length / state.size));
    state.page = Math.min(state.page, pages);
    const start = (state.page - 1) * state.size;
    const slice = rows.slice(start, start + state.size);

    $("rows").innerHTML = slice.map((c) =>
      `<tr><td class="id">${idLabel(c)}</td>` +
      `<td class="num">${c.previous_purchases}</td>` +
      `<td><span class="meter"><span>${c.engagement}/10</span><i style="--v:${c.engagement}"></i></span></td>` +
      `<td>${c.discount ? '<span class="tag offer">Offered</span>' : '<span class="tag no">Not offered</span>'}</td>` +
      `<td><span class="tag ${c.purchase ? "yes" : "no"}">${c.purchase ? "Purchased" : "Did not purchase"}</span></td></tr>`
    ).join("") || '<tr><td class="empty" colspan="5">No customers match. Clear the search or choose another outcome.</td></tr>';

    $("summaryText").textContent = rows.length
      ? `Showing ${start + 1}–${Math.min(start + state.size, rows.length)} of ${plural(rows.length, "customer")}`
      : "No customers found";
    $("pageText").textContent = `${state.page} / ${pages}`;
    $("prev").disabled = state.page <= 1;
    $("next").disabled = state.page >= pages;

    document.querySelectorAll("th").forEach((th) => {
      const k = th.querySelector("button").dataset.sort;
      th.setAttribute("aria-sort", k === state.sort ? (state.dir === 1 ? "ascending" : "descending") : "none");
    });
  }

  function renderAll() {
    const rows = segmentRows();
    currentRows = rows;
    renderHero(rows); renderPeople(rows); renderTrend(rows);
    renderCompare(rows); renderPrev(rows); renderNotes(rows); renderTable();
  }

  /* ---------- Actions ---------- */
  function toast(msg) {
    const t = $("toast");
    t.textContent = msg; t.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => t.classList.remove("show"), 3200);
  }

  function exportCsv() {
    const rows = tableRows();
    const cols = ["customer_id", "previous_purchases", "engagement", "discount", "purchase"];
    const csv = [cols.join(","), ...rows.map((c) => cols.map((k) => c[k]).join(","))].join("\n") + "\n";
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
    const a = document.createElement("a");
    a.href = url; a.download = "econocasual-customers.csv";
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    toast(`Exported ${plural(rows.length, "record")} from the table, with the group, search and outcome filters applied`);
  }

  /* ---------- Purchase model: logistic regression, fitted here in the browser ----------
     Fitted on 80% of the records and checked on the other 20%, so the accuracy
     shown is for customers the model has not seen. */
  const model = (() => {
    const feat = (e, p, d) => [1, e / 10, p / 10, d];
    const sig = (z) => 1 / (1 + Math.exp(-z));
    const dot = (w, x) => w.reduce((a, wi, i) => a + wi * x[i], 0);
    const train = customers.filter((c) => c.customer_id % 5 !== 0);
    const test = customers.filter((c) => c.customer_id % 5 === 0);
    const w = [0, 0, 0, 0];
    for (let it = 0; it < 4000; it++) {
      const g = [0, 0, 0, 0];
      train.forEach((c) => {
        const x = feat(c.engagement, c.previous_purchases, c.discount), err = sig(dot(w, x)) - c.purchase;
        for (let i = 0; i < 4; i++) g[i] += err * x[i];
      });
      for (let i = 0; i < 4; i++) w[i] -= 3 * (g[i] / train.length + (i ? 0.001 * w[i] : 0));
    }
    const predict = (e, p, d) => sig(dot(w, feat(e, p, d)));
    const right = test.filter((c) => (predict(c.engagement, c.previous_purchases, c.discount) >= 0.5 ? 1 : 0) === c.purchase).length;
    const bought = test.filter((c) => c.purchase === 1).length;
    return { predict, accuracy: right / test.length, baseline: Math.max(bought, test.length - bought) / test.length, tested: test.length };
  })();

  const avgRate = rate(customers);
  const els = { eng: $("pEng"), prev: $("pPrev"), disc: $("pDisc") };

  function renderPredict() {
    const e = Number(els.eng.value), p = Number(els.prev.value), d = els.disc.checked ? 1 : 0;
    $("pEngOut").textContent = e; $("pPrevOut").textContent = p;
    const prob = model.predict(e, p, d);
    $("pProb").textContent = pct(prob);
    $("pFill").style.width = prob * 100 + "%";
    $("pAvg").style.left = avgRate * 100 + "%";

    const withD = model.predict(e, p, 1), without = model.predict(e, p, 0);
    $("pDelta").textContent = `With a discount: ${pct(withD)}. Without: ${pct(without)}. The model puts the difference at ${pts(withD - without, 0)} points. The dark tick marks the sample average of ${pct(avgRate)}.`;

    let text = "Too few similar customers in the sample to compare.";
    for (const tol of [1, 2]) {
      const sim = customers.filter((c) => Math.abs(c.engagement - e) <= tol && Math.abs(c.previous_purchases - p) <= tol && c.discount === d);
      if (sim.length >= 15) {
        text = `Among ${fmt(sim.length)} real customers with engagement within ${tol} of ${e}, past purchases within ${tol} of ${p} and ${d ? "a discount" : "no discount"}, ${pct(rate(sim))} bought.`;
        break;
      }
    }
    $("pSimilar").textContent = text;
    $("pModel").textContent = `Checked on ${fmt(model.tested)} customers the model never saw, it called the outcome right ${pct(model.accuracy)} of the time. Always guessing the more common outcome would be right ${pct(model.baseline)}.`;
  }
  const clearActual = () => { $("pActual").hidden = true; };
  [els.eng, els.prev, els.disc].forEach((el) => el.addEventListener("input", () => { clearActual(); renderPredict(); }));
  $("pReset").addEventListener("click", () => {
    els.eng.value = Math.round(customers.reduce((a, c) => a + c.engagement, 0) / customers.length);
    els.prev.value = Math.round(customers.reduce((a, c) => a + c.previous_purchases, 0) / customers.length);
    els.disc.checked = false; clearActual(); renderPredict();
  });
  $("pLoad").addEventListener("click", () => {
    const c = customers[Math.floor(Math.random() * customers.length)];
    els.eng.value = c.engagement; els.prev.value = c.previous_purchases; els.disc.checked = c.discount === 1;
    renderPredict();
    $("pActual").hidden = false;
    $("pActual").textContent = `${idLabel(c)} is a real record: this customer ${c.purchase ? "bought" : "did not buy"}. The model said ${pct(model.predict(c.engagement, c.previous_purchases, c.discount))}.`;
  });
  renderPredict();

  /* ---------- Wiring ---------- */
  buildPeople();
  document.querySelectorAll(".seg").forEach((b) => {
    b.querySelector(".seg-n").textContent = fmt(customers.filter(SEGMENTS[b.dataset.seg]).length);
    b.addEventListener("click", () => {
      state.seg = b.dataset.seg; state.page = 1;
      document.querySelectorAll(".seg").forEach((s) => {
        const on = s === b; s.classList.toggle("is-on", on); s.setAttribute("aria-pressed", String(on));
      });
      hideDotTip();
      renderAll();
    });
  });

  $("search").addEventListener("input", (e) => { state.search = e.target.value; state.page = 1; renderTable(); });
  $("purchaseFilter").addEventListener("change", (e) => { state.outcome = e.target.value; state.page = 1; renderTable(); });
  $("prev").addEventListener("click", () => { state.page--; renderTable(); });
  $("next").addEventListener("click", () => { state.page++; renderTable(); });
  $("export").addEventListener("click", exportCsv);
  document.querySelectorAll("th button").forEach((b) =>
    b.addEventListener("click", () => {
      const k = b.dataset.sort;
      state.dir = state.sort === k ? -state.dir : 1; state.sort = k; state.page = 1;
      renderTable();
    })
  );

  // Customer squares: one delegated listener
  const grid = $("peopleGroups");
  grid.addEventListener("pointerover", (ev) => { const el = ev.target.closest(".d"); if (el) showDotTip(el); });
  grid.addEventListener("pointerleave", (ev) => { if (ev.pointerType === "mouse") hideDotTip(); });
  document.addEventListener("pointerdown", (ev) => { if (!ev.target.closest(".people")) hideDotTip(); });

  // Trend chart: pointer, touch and keyboard
  const svg = $("trend");
  const onPoint = (ev) => { if (trend) { kbScore = scoreAt(ev); showTrendTip(kbScore); } };
  svg.addEventListener("pointermove", onPoint);
  svg.addEventListener("pointerdown", onPoint);
  svg.addEventListener("pointerleave", (ev) => { if (ev.pointerType === "mouse") hideTrendTip(); });
  svg.addEventListener("blur", hideTrendTip);
  document.addEventListener("pointerdown", (ev) => { if (!ev.target.closest("#trendWrap")) hideTrendTip(); });
  svg.addEventListener("keydown", (ev) => {
    const keys = { ArrowRight: 1, ArrowLeft: -1, Home: 0, End: 0 };
    if (ev.key === "Escape") { hideTrendTip(); return; }
    if (!(ev.key in keys)) return;
    ev.preventDefault();
    kbScore = ev.key === "Home" ? 0 : ev.key === "End" ? 10
      : clamp((kbScore == null ? (ev.key === "ArrowRight" ? -1 : 11) : kbScore) + keys[ev.key], 0, 10);
    showTrendTip(kbScore);
  });

  // Redraw the chart when its container changes width (rotation, window resize)
  if ("ResizeObserver" in window) {
    new ResizeObserver(() => {
      if (Math.abs($("trendWrap").clientWidth - drawnWidth) >= 1) renderTrend(currentRows);
    }).observe($("trendWrap"));
  }

  // Highlight the nav link for the section in view
  const links = [...document.querySelectorAll(".nav a")];
  if ("IntersectionObserver" in window) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((en) => {
        if (en.isIntersecting) links.forEach((a) => a.classList.toggle("active", a.getAttribute("href") === "#" + en.target.id));
      });
    }, { rootMargin: "-40% 0px -55% 0px" });
    ["summary", "drivers", "predict", "customers"].forEach((id) => io.observe($(id)));
  }

  renderAll();

  // One-time reveal: the squares fill in when the page loads
  $("people").classList.add("intro");
  setTimeout(() => $("people").classList.remove("intro"), 2000);
})();
