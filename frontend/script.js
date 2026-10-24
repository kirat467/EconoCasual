/* EconoCausal: customer intelligence dashboard
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

  const makeSample = () => Array.from({ length: 1000 }, (_, i) => {
    const engagement = Math.round(clamp(normal(5.2, 2.5), 0, 10));
    const previous_purchases = Math.round(clamp(normal(3.2 + engagement * 0.15, 2.4), 0, 10));
    // Low-engagement customers were a little more likely to get an offer.
    const discount = rand() < clamp(0.66 - engagement * 0.03, 0.2, 0.8) ? 1 : 0;
    const z = -2.5 + 0.30 * engagement + 0.13 * previous_purchases + 0.5 * discount;
    const purchase = rand() < 1 / (1 + Math.exp(-z)) ? 1 : 0;
    return { customer_id: i + 1, previous_purchases, engagement, discount, purchase };
  });
  const sampleData = makeSample();
  let customers = sampleData;
  let byId = new Map(sampleData.map((c) => [c.customer_id, c]));
  let usingCustom = false;
  const SAMPLE_LABEL = "Sample data: 1,000 generated customers";

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

  const state = { seg: "all", search: "", outcome: "all", eng: "all", hist: "all", disc: "all", sort: "customer_id", dir: 1, page: 1, size: 10 };
  let loadInfo = { skipped: 0 }; // rows dropped when a CSV was uploaded
  let toastTimer;
  let currentRows = customers;

  const segmentRows = () => customers.filter(SEGMENTS[state.seg]);
  const ENG_FILTERS = { all: () => true, high: (c) => c.engagement >= 7, medium: (c) => c.engagement >= 4 && c.engagement <= 6, low: (c) => c.engagement <= 3 };
  const HIST_FILTERS = { all: () => true, repeat: (c) => c.previous_purchases >= 5, few: (c) => c.previous_purchases <= 4 };
  const DISC_FILTERS = { all: () => true, 1: (c) => c.discount === 1, 0: (c) => c.discount === 0 };
  const tableRows = () => {
    const q = state.search.replace(/\D/g, "");
    const rows = segmentRows().filter(
      (c) =>
        (!q || String(c.customer_id).padStart(4, "0").includes(q)) &&
        (state.outcome === "all" || String(c.purchase) === state.outcome) &&
        ENG_FILTERS[state.eng](c) && HIST_FILTERS[state.hist](c) && DISC_FILTERS[state.disc](c)
    );
    const k = state.sort;
    return rows.sort((a, b) => (a[k] - b[k] || a.customer_id - b.customer_id) * state.dir);
  };

  /* ---------- Statistics ----------
     Gaps come with a 95% range (Wilson / Newcombe intervals), so a small difference
     built on a few customers is not mistaken for a real pattern. */
  const Z = 1.96;
  const rateMin = (rows) => (rows.length >= MIN_N ? rate(rows) : null);
  const split = (rows) => [rows.filter((c) => c.discount === 1), rows.filter((c) => c.discount === 0)];
  const span = (g) => [g.lo, g.hi];

  /* Wilson score interval: stays sensible for small groups, unlike the plain normal formula */
  function wilson(rows) {
    const n = rows.length, p = rate(rows), z2 = Z * Z, den = 1 + z2 / n;
    const mid = (p + z2 / (2 * n)) / den;
    const half = (Z * Math.sqrt((p * (1 - p)) / n + z2 / (4 * n * n))) / den;
    return { p, lo: mid - half, hi: mid + half };
  }
  /* Newcombe's method: interval for the difference of two proportions */
  function diffCI(a, b) {
    const A = wilson(a), B = wilson(b), est = A.p - B.p;
    return {
      est,
      lo: est - Math.hypot(A.p - A.lo, B.hi - B.p),
      hi: est + Math.hypot(A.hi - A.p, B.p - B.lo),
    };
  }

  function overallGap(rows) {
    const [d, n] = split(rows);
    if (d.length < MIN_N || n.length < MIN_N) return null;
    return diffCI(d, n);
  }

  /* Discount gap after comparing customers within the same engagement band */
  function adjustedGap(rows) {
    const used = [];
    [[0, 3], [4, 6], [7, 10]].forEach(([lo, hi]) => {
      const g = rows.filter((c) => c.engagement >= lo && c.engagement <= hi);
      const [d, n] = split(g);
      if (d.length >= MIN_N && n.length >= MIN_N) used.push({ g, d, n });
    });
    const total = used.reduce((x, u) => x + u.g.length, 0);
    if (!total) return null;
    let est = 0, dl = 0, dh = 0;
    used.forEach(({ g, d, n }) => {
      const w = g.length / total, c = diffCI(d, n);
      est += w * c.est;
      dl += w * w * (c.est - c.lo) ** 2;
      dh += w * w * (c.hi - c.est) ** 2;
    });
    return { est, lo: est - Math.sqrt(dl), hi: est + Math.sqrt(dh), bands: used.length };
  }
  // The band-by-band figure only adds something when more than one band was compared.
  const bandGap = (rows) => { const a = adjustedGap(rows); return a && a.bands > 1 ? a : null; };

  /* ---------- One square per customer ---------- */
  let dotEls = new Map();
  const GROUPS = [
    { key: 1, cls: "with", name: "Offered a discount" },
    { key: 0, cls: "without", name: "No discount" },
  ];

  function buildPeople() {
    dotEls = new Map();
    $("peopleGroups").setAttribute("aria-label", `One square for each of the ${fmt(customers.length)} customers, grouped by whether they were offered a discount. Filled squares bought. The same numbers appear in the headline and the figures below.`);
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
    $("peopleGroups").querySelectorAll(".d").forEach((el) => { dotEls.set(Number(el.dataset.id), el); });
  }

  function renderPeople(rows) {
    const inView = new Set(rows.map((c) => c.customer_id));
    customers.forEach((c) => dotEls.get(c.customer_id).classList.toggle("out", !inView.has(c.customer_id)));
    GROUPS.forEach((g) => {
      const list = rows.filter((c) => c.discount === g.key);
      $("meta" + g.key).textContent = list.length
        ? `${pct(rate(list))} bought, ${plural(list.length, "customer")}`
        : "nobody in this group";
    });
  }

  const dotTip = $("dotTip");
  function showDotTip(el) {
    const c = byId.get(Number(el.dataset.id));
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
  /* ---------- Motion helpers ---------- */
  const calm = window.matchMedia("(prefers-reduced-motion: reduce)");
  function countTo(id, to, format) {
    const el = $(id), from = el._v == null ? 0 : el._v;
    el._v = to;
    cancelAnimationFrame(el._raf);
    if (calm.matches || from === to) { el.textContent = format(to); return; }
    const t0 = performance.now(), ms = 650;
    const step = (now) => {
      const k = Math.min(1, (now - t0) / ms), e = 1 - Math.pow(1 - k, 3);
      el.textContent = format(from + (to - from) * e);
      if (k < 1) el._raf = requestAnimationFrame(step);
    };
    el._raf = requestAnimationFrame(step);
  }
  function swapIn(el) {
    el.classList.remove("swap"); void el.offsetWidth; el.classList.add("swap");
  }

  function renderHero(rows) {
    const n = rows.length;
    const [d, nd] = split(rows);
    const bought = rows.filter((c) => c.purchase === 1).length;

    if (!n) {
      $("headline").textContent = "No customers in this group.";
      $("subline").textContent = "Pick another group above to see results.";
      ["sTotal", "sRate", "sEng", "sDisc"].forEach((id) => { const el = $(id); cancelAnimationFrame(el._raf); el._v = null; el.textContent = "–"; });
      ["sTotalNote", "sRateNote", "sDiscNote"].forEach((id) => ($(id).textContent = "\u00a0"));
      return;
    }

    const dr = rateMin(d), nr = rateMin(nd);
    const prevHead = $("headline").textContent;
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
    if ($("headline").textContent !== prevHead && prevHead !== "Loading customer sample…") swapIn($("headline"));

    countTo("sTotal", n, (v) => fmt(Math.round(v)));
    $("sTotalNote").textContent = state.seg === "all" ? "full sample" : `of ${fmt(customers.length)} in the sample`;
    countTo("sRate", bought / n, (v) => pct(v, 1));
    $("sRateNote").textContent = `${fmt(bought)} purchases recorded`;
    countTo("sEng", rows.reduce((a, c) => a + c.engagement, 0) / n, (v) => v.toFixed(1));
    countTo("sDisc", d.length / n, (v) => pct(v, 1));
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
      out += `<path class="ln ${s.cls}" pathLength="1" d="${d}"/>`;
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
      `<tr><td class="id"><button type="button" class="row-load" data-id="${c.customer_id}" title="Try this customer in the predictor">${idLabel(c)}</button></td>` +
      `<td class="num">${c.previous_purchases}</td>` +
      `<td><span class="meter"><span>${c.engagement}/10</span><i style="--v:${c.engagement}"></i></span></td>` +
      `<td>${c.discount ? '<span class="tag offer">Offered</span>' : '<span class="tag no">Not offered</span>'}</td>` +
      `<td><span class="tag ${c.purchase ? "yes" : "no"}">${c.purchase ? "Purchased" : "Did not purchase"}</span></td></tr>`
    ).join("") || '<tr><td class="empty" colspan="5">No customers match. Clear the search or choose another outcome.</td></tr>';

    $("summaryText").textContent = rows.length
      ? `Showing ${start + 1}–${Math.min(start + state.size, rows.length)} of ${plural(rows.length, "customer")}`
      : "No customers found";
    $("pageText").textContent = `${state.page} / ${pages}`;
    syncUrl();
    $("prev").disabled = state.page <= 1;
    $("next").disabled = state.page >= pages;

    document.querySelectorAll("#customers th").forEach((th) => {
      const k = th.querySelector("button").dataset.sort;
      th.setAttribute("aria-sort", k === state.sort ? (state.dir === 1 ? "ascending" : "descending") : "none");
    });
  }

  /* ---------- Data quality: checks every loaded record ---------- */
  function renderQuality() {
    const num = (v) => typeof v === "number" && Number.isFinite(v);
    let missing = 0, invalid = 0;
    customers.forEach((c) => {
      ["previous_purchases", "engagement", "discount", "purchase"].forEach((k) => { if (!num(c[k])) missing++; });
      if (num(c.engagement) && (c.engagement < 0 || c.engagement > 10)) invalid++;
      if (num(c.previous_purchases) && (c.previous_purchases < 0 || c.previous_purchases > 10 || !Number.isInteger(c.previous_purchases))) invalid++;
      if (num(c.discount) && c.discount !== 0 && c.discount !== 1) invalid++;
      if (num(c.purchase) && c.purchase !== 0 && c.purchase !== 1) invalid++;
    });
    const skipped = loadInfo.skipped;
    const problems = missing + invalid + skipped;
    $("quality-visible").textContent = fmt(customers.length);
    $("quality-missing").textContent = fmt(missing);
    $("quality-invalid").textContent = fmt(invalid + skipped);
    $("quality-status").textContent = problems === 0 ? "Basic checks passed" : "Review suggested";
    $("quality-note").textContent =
      `Checked all ${fmt(customers.length)} records: ${plural(missing, "missing value")}, ${plural(invalid, "out-of-range value")}` +
      (skipped ? `, and ${plural(skipped, "row")} skipped during upload because of invalid values.` : ".") +
      (usingCustom ? "" : " This is generated sample data, so it is clean by design.");
  }

  function renderAll() {
    const rows = segmentRows();
    currentRows = rows;
    const tr = $("trend"); tr.classList.add("draw"); clearTimeout(tr._t); tr._t = setTimeout(() => tr.classList.remove("draw"), 1300);
    renderHero(rows); renderPeople(rows); renderTrend(rows);
    renderCompare(rows); renderPrev(rows); renderNotes(rows); renderTarget(rows); renderTable();
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
    a.href = url; a.download = "econocausal-customers.csv";
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    toast(`Exported ${plural(rows.length, "record")} from the table, with the group, search and all filters applied`);
  }

  /* ---------- Purchase model: logistic regression, fitted here in the browser ----------
     Fitted on 80% of the records and checked on the other 20%, so the accuracy
     shown is for customers the model has not seen. */
  const buildModel = () => {
    const feat = (e, p, d) => [1, e / 10, p / 10, d];
    const sig = (z) => 1 / (1 + Math.exp(-z));
    const dot = (w, x) => w.reduce((a, wi, i) => a + wi * x[i], 0);
    // Split by position, not by customer_id, so uploaded IDs can never leave a set empty
    const train = customers.filter((c, i) => i % 5 !== 0);
    const test = customers.filter((c, i) => i % 5 === 0);
    const solve = (A, b) => {
      const n = b.length, M = A.map((r, i) => [...r, b[i]]);
      for (let i = 0; i < n; i++) {
        let m = i;
        for (let r = i + 1; r < n; r++) if (Math.abs(M[r][i]) > Math.abs(M[m][i])) m = r;
        [M[i], M[m]] = [M[m], M[i]];
        for (let r = i + 1; r < n; r++) { const f = M[r][i] / M[i][i]; for (let c = i; c <= n; c++) M[r][c] -= f * M[i][c]; }
      }
      const x = Array(n).fill(0);
      for (let i = n - 1; i >= 0; i--) { let t = M[i][n]; for (let c = i + 1; c < n; c++) t -= M[i][c] * x[c]; x[i] = t / M[i][i]; }
      return x;
    };
    // Newton's method (IRLS) converges in a handful of steps, so uploads do not freeze the page
    const w = [0, 0, 0, 0], lam = 0.001 * train.length;
    for (let it = 0; it < 25; it++) {
      const g = [0, 0, 0, 0], H = Array.from({ length: 4 }, () => [0, 0, 0, 0]);
      train.forEach((c) => {
        const x = feat(c.engagement, c.previous_purchases, c.discount), p = sig(dot(w, x)), sv = p * (1 - p) + 1e-6;
        for (let i = 0; i < 4; i++) { g[i] += (p - c.purchase) * x[i]; for (let j = 0; j < 4; j++) H[i][j] += sv * x[i] * x[j]; }
      });
      for (let i = 1; i < 4; i++) { g[i] += lam * w[i]; H[i][i] += lam; }
      const step = solve(H, g);
      let big = 0;
      for (let i = 0; i < 4; i++) { w[i] -= step[i]; big = Math.max(big, Math.abs(step[i])); }
      if (big < 1e-6) break;
    }
    const predict = (e, p, d) => sig(dot(w, feat(e, p, d)));
    const right = test.filter((c) => (predict(c.engagement, c.previous_purchases, c.discount) >= 0.5 ? 1 : 0) === c.purchase).length;
    const bought = test.filter((c) => c.purchase === 1).length;
    // AUC: chance that a random buyer is scored above a random non-buyer (0.5 = coin flip)
    const sc = (c) => predict(c.engagement, c.previous_purchases, c.discount);
    const pos = test.filter((c) => c.purchase === 1).map(sc), neg = test.filter((c) => c.purchase === 0).map(sc);
    let wins = 0;
    pos.forEach((a) => neg.forEach((b) => { wins += a > b ? 1 : a === b ? 0.5 : 0; }));
    const auc = pos.length && neg.length ? wins / (pos.length * neg.length) : null;
    return {
      predict, auc,
      accuracy: test.length ? right / test.length : null,
      baseline: test.length ? Math.max(bought, test.length - bought) / test.length : null,
      tested: test.length,
    };
  };
  let model = buildModel();

  let avgRate = rate(customers);
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
    $("pModel").textContent = model.tested < 10
      ? "Too few records to check the model on unseen customers."
      : `Checked on ${fmt(model.tested)} customers the model never saw, it called the outcome right ${pct(model.accuracy)} of the time. Always guessing the more common outcome would be right ${pct(model.baseline)}.` +
        (model.auc == null ? "" : ` Its AUC is ${model.auc.toFixed(2)} (0.50 is a coin flip, 1.00 is perfect).`);
    syncUrl();
  }
  const clearActual = () => { $("pActual").hidden = true; };
  [els.eng, els.prev, els.disc].forEach((el) => el.addEventListener("input", () => { clearActual(); renderPredict(); }));
  $("pReset").addEventListener("click", () => {
    els.eng.value = Math.round(customers.reduce((a, c) => a + c.engagement, 0) / customers.length);
    els.prev.value = Math.round(customers.reduce((a, c) => a + c.previous_purchases, 0) / customers.length);
    els.disc.checked = false; clearActual(); renderPredict();
  });
  function loadCustomer(c) {
    els.eng.value = c.engagement; els.prev.value = c.previous_purchases; els.disc.checked = c.discount === 1;
    renderPredict();
    $("pActual").hidden = false;
    $("pActual").textContent = `${idLabel(c)} is a real record: this customer ${c.purchase ? "bought" : "did not buy"}. The model said ${pct(model.predict(c.engagement, c.previous_purchases, c.discount))}.`;
  }
  $("pLoad").addEventListener("click", () => loadCustomer(customers[Math.floor(Math.random() * customers.length)]));


  /* ---------- Who should get a discount? ----------
     Lift = model chance with a discount minus chance without, per customer.
     Targeting the highest lifts is compared with giving the same number of
     discounts to customers picked without any ranking. */
  const tPct = $("tPct");
  let targetRows = [];
  const gainFmt = (g) => "+" + (g >= 10 ? fmt(Math.round(g)) : g.toFixed(1));
  const mean = (a) => a.reduce((x, y) => x + y, 0) / (a.length || 1);

  function renderTarget(rows) {
    const n = rows.length;
    const share = Number(tPct.value);
    $("tPctOut").textContent = share + "%";
    if (n < MIN_N) {
      targetRows = [];
      $("tBig").textContent = "–";
      $("tSummary").textContent = "Pick a group with more customers to plan discounts.";
      ["tCompare", "tTop"].forEach((id) => ($(id).innerHTML = ""));
      $("tProfile").textContent = "";
      return;
    }
    const scored = rows.map((c) => {
      const base = model.predict(c.engagement, c.previous_purchases, 0);
      return { c, base, lift: model.predict(c.engagement, c.previous_purchases, 1) - base };
    }).sort((a, b) => b.lift - a.lift || a.c.customer_id - b.c.customer_id);

    const k = Math.round((n * share) / 100);
    const chosen = scored.slice(0, k);
    targetRows = chosen;
    const targeted = chosen.reduce((a, s) => a + s.lift, 0);
    const even = k * mean(scored.map((s) => s.lift));
    const top = Math.max(targeted, even, 1e-9);

    $("tBig").textContent = gainFmt(targeted);
    $("tSummary").textContent = k
      ? `Offering a discount to ${plural(k, "customer")} (${share}% of ${fmt(n)}). With no discounts the model expects about ${fmt(Math.round(scored.reduce((a, s) => a + s.base, 0)))} purchases from this group.`
      : "Move the slider to choose how many customers get a discount.";

    const bar = (cls, label, g, note) =>
      `<li class="${cls}"><div class="row"><span>${label}</span><b>${gainFmt(g)}</b></div>` +
      `<div class="track"><span class="fill" style="width:${(g / top) * 100}%"></span></div><small>${note}</small></li>`;
    $("tCompare").innerHTML = k
      ? bar("with", "Targeted by the model", targeted, "Customers with the largest estimated lift") +
        bar("cmp-even", "Spread evenly", even, even > 0 && targeted > 0 ? `Targeting gives ${(targeted / even).toFixed(1)}× as many extra purchases as picking without a ranking` : "Same number of discounts, no ranking")
      : "";

    $("tProfile").textContent = k
      ? `Targeted customers average engagement ${mean(chosen.map((s) => s.c.engagement)).toFixed(1)} and ${mean(chosen.map((s) => s.c.previous_purchases)).toFixed(1)} past purchases, against ${mean(rows.map((c) => c.engagement)).toFixed(1)} and ${mean(rows.map((c) => c.previous_purchases)).toFixed(1)} for the whole group.`
      : "";
    $("tTop").innerHTML = chosen.slice(0, 5).map((s) =>
      `<li><button type="button" class="row-load" data-id="${s.c.customer_id}">${idLabel(s.c)}</button>: engagement ${s.c.engagement}/10, ${plural(s.c.previous_purchases, "past purchase")}. Chance of buying ${pct(s.base)} without a discount, ${pct(s.base + s.lift)} with one.</li>`
    ).join("");
  }

  const saveCsv = (name, csv) => {
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
    const a = document.createElement("a");
    a.href = url; a.download = name;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  tPct.addEventListener("input", () => renderTarget(currentRows));
  $("tExport").addEventListener("click", () => {
    if (!targetRows.length) { toast("Choose a share above 0% first."); return; }
    const head = "customer_id,engagement,previous_purchases,offered_discount,chance_without,chance_with,estimated_lift\n";
    const body = targetRows.map((s) => [s.c.customer_id, s.c.engagement, s.c.previous_purchases, s.c.discount, s.base.toFixed(4), (s.base + s.lift).toFixed(4), s.lift.toFixed(4)].join(",")).join("\n");
    saveCsv("econocausal-discount-targets.csv", head + body + "\n");
    toast(`Exported ${plural(targetRows.length, "customer")} ranked by estimated lift`);
  });
  $("tTop").addEventListener("click", (ev) => {
    const b = ev.target.closest(".row-load");
    if (!b) return;
    loadCustomer(byId.get(Number(b.dataset.id)));
    $("predict").scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
  });

  /* ---------- Your own data: CSV upload with checks ---------- */
  const REQUIRED = ["previous_purchases", "engagement", "discount", "purchase"];
  const ALIASES = { customerid: "customer_id", id: "customer_id", previouspurchases: "previous_purchases", past_purchases: "previous_purchases", pastpurchases: "previous_purchases", engagement_score: "engagement", discount_offered: "discount", offered_discount: "discount", purchased: "purchase", bought: "purchase" };
  const MAX_ROWS = 5000, MIN_ROWS = 50;
  const esc = (s) => String(s).replace(/[&<>"']/g, (m) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[m]));
  const normHead = (h) => { const s = h.replace(/^\ufeff/, "").trim().toLowerCase().replace(/[\s-]+/g, "_"); return ALIASES[s] || s; };
  const toBit = (v) => { const s = String(v).trim().toLowerCase(); return ["1", "yes", "y", "true", "t"].includes(s) ? 1 : ["0", "no", "n", "false", "f"].includes(s) ? 0 : null; };

  function parseCsv(text) {
    text = text.replace(/^\ufeff/, "");
    const first = text.split(/\r?\n/, 1)[0];
    const delim = [",", ";", "\t"].map((d) => [d, first.split(d).length]).sort((a, b) => b[1] - a[1])[0][0];
    const out = []; let row = [], cell = "", q = false;
    const push = () => { row.push(cell); cell = ""; if (row.some((x) => x.trim() !== "")) out.push(row); row = []; };
    for (let i = 0; i < text.length; i++) {
      const ch = text[i];
      if (q) { if (ch === '"') { if (text[i + 1] === '"') { cell += '"'; i++; } else q = false; } else cell += ch; }
      else if (ch === '"') q = true;
      else if (ch === delim) { row.push(cell); cell = ""; }
      else if (ch === "\n" || ch === "\r") { if (ch === "\r" && text[i + 1] === "\n") i++; push(); }
      else cell += ch;
    }
    push();
    return out;
  }

  function validateCsv(text) {
    const table = parseCsv(text);
    if (table.length < 2) return { error: "The file has a header but no data rows, or is empty." };
    const heads = table[0].map(normHead);
    const missing = REQUIRED.filter((c) => !heads.includes(c));
    if (missing.length)
      return { error: `Missing ${missing.length === 1 ? "column" : "columns"}: ${missing.join(", ")}. Columns found: ${heads.join(", ")}. Needed: ${REQUIRED.join(", ")} (customer_id is optional).` };
    const at = Object.fromEntries(REQUIRED.map((c) => [c, heads.indexOf(c)]));
    const idAt = heads.indexOf("customer_id");
    const rows = [], issues = [], why = {};
    const bad = (line, reason) => { why[reason] = (why[reason] || 0) + 1; if (issues.length < 3) issues.push(`Row ${line}: ${reason}`); };
    for (let i = 1; i < table.length; i++) {
      const r = table[i];
      const e = Number(r[at.engagement]), p = Number(r[at.previous_purchases]);
      const d = toBit(r[at.discount]), b = toBit(r[at.purchase]);
      if (r[at.engagement] === undefined || r[at.engagement].trim() === "" || !Number.isFinite(e) || e < 0 || e > 10) { bad(i + 1, "engagement must be a number from 0 to 10"); continue; }
      if (r[at.previous_purchases] === undefined || r[at.previous_purchases].trim() === "" || !Number.isFinite(p) || p < 0 || p > 10) { bad(i + 1, "previous_purchases must be a number from 0 to 10"); continue; }
      if (d === null) { bad(i + 1, "discount must be 0/1 or yes/no"); continue; }
      if (b === null) { bad(i + 1, "purchase must be 0/1 or yes/no"); continue; }
      if (rows.length < MAX_ROWS) rows.push({ customer_id: 0, _id: idAt >= 0 ? Number(String(r[idAt] == null ? "" : r[idAt]).trim()) : NaN, previous_purchases: Math.round(p), engagement: Math.round(e), discount: d, purchase: b });
    }
    const skipped = Object.values(why).reduce((a, x) => a + x, 0);
    if (rows.length < MIN_ROWS) return { error: `Only ${rows.length} usable ${rows.length === 1 ? "row" : "rows"} found. At least ${MIN_ROWS} are needed for the statistics and the model to mean anything.`, issues };
    const warnings = [];
    const ids = rows.map((c) => c._id);
    const keepIds = idAt >= 0 && ids.every((v) => Number.isInteger(v) && v >= 1 && v <= 9999) && new Set(ids).size === ids.length;
    rows.forEach((c, i) => { c.customer_id = keepIds ? c._id : i + 1; delete c._id; });
    if (idAt >= 0 && !keepIds) warnings.push("customer_id values were missing, repeated or outside 1–9999, so customers are numbered 1, 2, 3… instead.");
    if (new Set(rows.map((c) => c.discount)).size < 2) warnings.push("Every customer has the same discount value, so discount comparisons will be empty.");
    if (new Set(rows.map((c) => c.purchase)).size < 2) warnings.push("Every customer has the same purchase outcome, so the model has nothing to learn from.");
    if (table.length - 1 - skipped > MAX_ROWS) warnings.push(`Only the first ${fmt(MAX_ROWS)} valid rows are used.`);
    return { rows, skipped, issues, warnings };
  }

  const dlg = $("uploadDlg"), fileIn = $("fileIn");
  let pending = null;
  const openDlg = () => { if (dlg.showModal) { if (!dlg.open) dlg.showModal(); } else dlg.setAttribute("open", ""); };
  const closeDlg = () => { if (dlg.close) dlg.close(); else dlg.removeAttribute("open"); };

  function showUpload(res, name) {
    pending = res.rows ? { rows: res.rows, name, skipped: res.skipped || 0 } : null;
    $("uTitle").textContent = res.rows ? "Check your file" : "This file can't be used yet";
    let html = `<p class="u-file">${esc(name)}</p>`;
    if (res.error) html += `<p class="u-err">${esc(res.error)}</p>`;
    if (res.rows) {
      html += `<p><b>${plural(res.rows.length, "customer")}</b> ready to load.` + (res.skipped ? ` ${plural(res.skipped, "row")} skipped because of invalid values.` : "") + ` Your customer_id is kept when valid; otherwise customers are numbered CUST-0001 onwards in file order.</p>`;
      html += `<div class="table-scroll u-prev"><table><thead><tr><th>Customer</th><th class="num">Past purchases</th><th>Engagement</th><th>Discount</th><th>Purchase</th></tr></thead><tbody>` +
        res.rows.slice(0, 5).map((c) => `<tr><td>${idLabel(c)}</td><td class="num">${c.previous_purchases}</td><td>${c.engagement}/10</td><td>${c.discount ? "Offered" : "Not offered"}</td><td>${c.purchase ? "Purchased" : "Did not purchase"}</td></tr>`).join("") +
        `</tbody></table></div><p class="u-note">First 5 rows as the dashboard will read them.</p>`;
    }
    const notes = [...(res.warnings || []), ...(res.issues || [])];
    if (notes.length) html += `<ul class="u-list">${notes.map((t) => `<li>${esc(t)}</li>`).join("")}</ul>`;
    $("uBody").innerHTML = html;
    $("uUse").hidden = !res.rows;
    openDlg();
  }

  function openFile(file) {
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) { showUpload({ error: "The file is larger than 5 MB. Remove unused columns or split it." }, file.name); return; }
    const r = new FileReader();
    r.onload = () => showUpload(validateCsv(String(r.result)), file.name);
    r.onerror = () => showUpload({ error: "The browser could not read this file." }, file.name);
    r.readAsText(file);
  }

  function syncFilterControls() {
    $("search").value = state.search;
    $("purchaseFilter").value = state.outcome;
    $("engagementFilter").value = state.eng;
    $("historyFilter").value = state.hist;
    $("discountFilter").value = state.disc;
    $("pageSize").value = String(state.size);
  }

  function updateSegCounts() {
    document.querySelectorAll(".seg").forEach((b) => { b.querySelector(".seg-n").textContent = fmt(customers.filter(SEGMENTS[b.dataset.seg]).length); });
  }

  function setData(rows, label, skipped = 0, keepView = false) {
    customers = rows; usingCustom = rows !== sampleData;
    byId = new Map(rows.map((c) => [c.customer_id, c]));
    // keepView = true keeps the group, filters and predictor restored from a shared link
    if (!keepView) Object.assign(state, { seg: "all", search: "", outcome: "all", eng: "all", hist: "all", disc: "all", page: 1 });
    loadInfo = { skipped };
    syncFilterControls();
    document.querySelectorAll(".seg").forEach((s) => {
      const on = s.dataset.seg === state.seg;
      s.classList.toggle("is-on", on); s.setAttribute("aria-pressed", String(on));
    });
    model = buildModel(); avgRate = rate(customers);
    buildPeople(); updateSegCounts(); hideDotTip(); hideTrendTip();
    $("sourceText").textContent = label; $("useSample").hidden = !usingCustom;
    if (keepView) renderPredict(); else $("pReset").click();
    renderAll(); renderQuality(); syncUrl();
    document.dispatchEvent(new CustomEvent("econo:data"));
  }

  $("upload").addEventListener("click", () => fileIn.click());
  fileIn.addEventListener("change", () => { openFile(fileIn.files[0]); fileIn.value = ""; });
  $("uUse").addEventListener("click", () => {
    if (!pending) return;
    setData(pending.rows, `${pending.name}: ${fmt(pending.rows.length)} customers`, pending.skipped);
    closeDlg(); toast(`Loaded ${plural(pending.rows.length, "customer")} from ${pending.name}. Nothing leaves your browser.`);
  });
  $("uCancel").addEventListener("click", closeDlg);
  $("uAgain").addEventListener("click", () => { closeDlg(); fileIn.click(); });
  $("uTemplate").addEventListener("click", () => saveCsv("econocausal-template.csv", "customer_id,previous_purchases,engagement,discount,purchase\n1,3,6,1,1\n2,0,2,0,0\n3,7,8,0,1\n4,2,4,1,0\n5,5,5,0,1\n"));
  $("useSample").addEventListener("click", () => { setData(sampleData, SAMPLE_LABEL); toast("Back to the sample data."); });

  // Drag a file anywhere on the page
  let dragDepth = 0;
  const hasFiles = (ev) => ev.dataTransfer && [...ev.dataTransfer.types].includes("Files");
  window.addEventListener("dragenter", (ev) => { if (hasFiles(ev)) { dragDepth++; document.body.classList.add("dropping"); } });
  window.addEventListener("dragleave", (ev) => { if (hasFiles(ev) && --dragDepth <= 0) { dragDepth = 0; document.body.classList.remove("dropping"); } });
  window.addEventListener("dragover", (ev) => { if (hasFiles(ev)) ev.preventDefault(); });
  window.addEventListener("drop", (ev) => {
    if (!hasFiles(ev)) return;
    ev.preventDefault(); dragDepth = 0; document.body.classList.remove("dropping");
    openFile(ev.dataTransfer.files[0]);
  });

  /* ---------- Light / dark theme ---------- */
  const themeBtn = $("theme"), darkQuery = matchMedia("(prefers-color-scheme: dark)");
  const isDark = () => (document.documentElement.dataset.theme ? document.documentElement.dataset.theme === "dark" : darkQuery.matches);
  function paintTheme() {
    const d = isDark();
    themeBtn.setAttribute("aria-pressed", String(d));
    document.querySelector('meta[name="theme-color"]').setAttribute("content", d ? "#0f1714" : "#0a6b5f");
  }
  themeBtn.addEventListener("click", () => {
    const next = isDark() ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem("ec-theme", next); } catch (e) { /* storage may be blocked */ }
    paintTheme();
  });
  if (darkQuery.addEventListener) darkQuery.addEventListener("change", paintTheme);

  /* ---------- Shareable view: state lives in the query string ---------- */
  const DEFAULTS = { eng: 5, prev: 3 };
  function syncUrl() {
    const q = new URLSearchParams();
    if (state.seg !== "all") q.set("seg", state.seg);
    if (state.outcome !== "all") q.set("out", state.outcome);
    if (state.search) q.set("q", state.search);
    if (state.eng !== "all") q.set("fe", state.eng);
    if (state.hist !== "all") q.set("fh", state.hist);
    if (state.disc !== "all") q.set("fd", state.disc);
    if (state.sort !== "customer_id" || state.dir !== 1) { q.set("sort", state.sort); q.set("dir", state.dir === 1 ? "asc" : "desc"); }
    if (state.size !== 10) q.set("ps", state.size);
    if (state.page > 1) q.set("pg", state.page);
    if (Number(els.eng.value) !== DEFAULTS.eng) q.set("e", els.eng.value);
    if (Number(els.prev.value) !== DEFAULTS.prev) q.set("p", els.prev.value);
    if (els.disc.checked) q.set("d", "1");
    const qs = q.toString();
    try { history.replaceState(null, "", location.pathname + (qs ? "?" + qs : "") + location.hash); } catch (e) { /* file:// may block this */ }
  }
  (function readUrl() {
    const q = new URLSearchParams(location.search);
    const int = (k, lo, hi) => { const v = Number(q.get(k)); return q.has(k) && Number.isInteger(v) && v >= lo && v <= hi ? v : null; };
    if (Object.prototype.hasOwnProperty.call(SEGMENTS, q.get("seg"))) state.seg = q.get("seg");
    if (["0", "1"].includes(q.get("out"))) state.outcome = q.get("out");
    if (q.get("q")) state.search = q.get("q").replace(/\D/g, "").slice(0, 4);
    if (Object.prototype.hasOwnProperty.call(ENG_FILTERS, q.get("fe"))) state.eng = q.get("fe");
    if (Object.prototype.hasOwnProperty.call(HIST_FILTERS, q.get("fh"))) state.hist = q.get("fh");
    if (["0", "1"].includes(q.get("fd"))) state.disc = q.get("fd");
    if (["customer_id", "previous_purchases", "engagement", "discount", "purchase"].includes(q.get("sort"))) {
      state.sort = q.get("sort"); state.dir = q.get("dir") === "desc" ? -1 : 1;
    }
    const e = int("e", 0, 10), p = int("p", 0, 10);
    if ([10, 25, 50].includes(Number(q.get("ps")))) state.size = Number(q.get("ps"));
    const pg = int("pg", 1, 9999); if (pg !== null) state.page = pg;
    if (e !== null) els.eng.value = e;
    if (p !== null) els.prev.value = p;
    els.disc.checked = q.get("d") === "1";
    document.querySelectorAll(".seg").forEach((s) => {
      const on = s.dataset.seg === state.seg; s.classList.toggle("is-on", on); s.setAttribute("aria-pressed", String(on));
    });
    syncFilterControls();
  })();
  renderPredict();

  /* ---------- Wiring ---------- */
  buildPeople();
  document.querySelectorAll(".seg").forEach((b) => {
    b.addEventListener("click", () => {
      state.seg = b.dataset.seg; state.page = 1;
      document.querySelectorAll(".seg").forEach((s) => {
        const on = s === b; s.classList.toggle("is-on", on); s.setAttribute("aria-pressed", String(on));
      });
      hideDotTip();
      renderAll();
      syncUrl();
    });
  });

  $("search").addEventListener("input", (e) => {
    const clean = e.target.value.replace(/\D/g, "").slice(0, 4);
    if (e.target.value !== clean) e.target.value = clean;
    state.search = clean; state.page = 1; renderTable();
  });
  $("purchaseFilter").addEventListener("change", (e) => { state.outcome = e.target.value; state.page = 1; renderTable(); });
  $("pageSize").addEventListener("change", (e) => { state.size = Number(e.target.value); state.page = 1; renderTable(); });
  $("prev").addEventListener("click", () => { state.page--; renderTable(); });
  $("next").addEventListener("click", () => { state.page++; renderTable(); });
  [["engagementFilter", "eng"], ["historyFilter", "hist"], ["discountFilter", "disc"]].forEach(([id, key]) =>
    $(id).addEventListener("change", (e) => { state[key] = e.target.value; state.page = 1; renderTable(); })
  );
  $("clearAdvancedFilters").addEventListener("click", () => {
    Object.assign(state, { eng: "all", hist: "all", disc: "all", page: 1 });
    syncFilterControls(); renderTable();
  });
  $("resetDashboard").addEventListener("click", () => {
    Object.assign(state, { seg: "all", search: "", outcome: "all", eng: "all", hist: "all", disc: "all", sort: "customer_id", dir: 1, page: 1, size: 10 });
    document.querySelectorAll(".seg").forEach((s) => { const on = s.dataset.seg === "all"; s.classList.toggle("is-on", on); s.setAttribute("aria-pressed", String(on)); });
    syncFilterControls();
    $("pReset").click();
    tPct.value = 20;
    hideDotTip(); hideTrendTip();
    renderAll(); syncUrl();
    const calm = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
    $("summary").scrollIntoView({ behavior: calm ? "auto" : "smooth" });
    toast("View reset: group, filters, sorting, predictor and discount share are back to their defaults.");
  });
  $("export").addEventListener("click", exportCsv);
  $("chartPng").addEventListener("click", () => {
    const svgEl = $("trend");
    svgEl.classList.remove("draw");
    const clone = svgEl.cloneNode(true);
    const from = svgEl.querySelectorAll("*"), to = clone.querySelectorAll("*");
    const props = ["fill", "stroke", "stroke-width", "stroke-dasharray", "stroke-dashoffset", "opacity", "font-size", "font-family", "font-weight", "stroke-linecap", "stroke-linejoin", "visibility"];
    from.forEach((el, i) => { const cs = getComputedStyle(el); props.forEach((p) => to[i].style.setProperty(p, cs.getPropertyValue(p))); });
    const W = svgEl.viewBox.baseVal.width, H = svgEl.viewBox.baseVal.height;
    clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
    clone.setAttribute("width", W); clone.setAttribute("height", H);
    const bg = getComputedStyle(document.body).backgroundColor;
    const url = URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(clone)], { type: "image/svg+xml;charset=utf-8" }));
    const img = new Image();
    img.onload = () => {
      const k = 2, cv = document.createElement("canvas");
      cv.width = W * k; cv.height = H * k;
      const ctx = cv.getContext("2d");
      ctx.fillStyle = bg; ctx.fillRect(0, 0, cv.width, cv.height);
      ctx.scale(k, k); ctx.drawImage(img, 0, 0, W, H);
      URL.revokeObjectURL(url);
      cv.toBlob((blob) => {
        const u = URL.createObjectURL(blob), a = document.createElement("a");
        a.href = u; a.download = "econocausal-trend.png";
        document.body.appendChild(a); a.click(); a.remove();
        setTimeout(() => URL.revokeObjectURL(u), 1000);
        toast("Chart saved as PNG");
      });
    };
    img.onerror = () => toast("Could not create the PNG in this browser.");
    img.src = url;
  });
  $("rows").addEventListener("click", (ev) => {
    const b = ev.target.closest(".row-load");
    if (!b) return;
    loadCustomer(byId.get(Number(b.dataset.id)));
    const calm = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
    $("predict").scrollIntoView({ behavior: calm ? "auto" : "smooth" });
  });
  $("share").addEventListener("click", async () => {
    syncUrl();
    try { await navigator.clipboard.writeText(location.href); toast(usingCustom ? "Link copied. Uploaded data stays in your browser, so the link opens with the sample data." : "Link copied. It opens this same view."); }
    catch (e) { toast("Copy this address from the browser bar to share the view."); }
  });
  document.querySelectorAll("th button").forEach((b) =>
    b.addEventListener("click", () => {
      const k = b.dataset.sort;
      state.dir = state.sort === k ? -state.dir : 1; state.sort = k; state.page = 1;
      renderTable();
    })
  );

  // Customer squares: one delegated listener
  const grid = $("peopleGroups");
  grid.setAttribute("tabindex", "0");
  grid.setAttribute("aria-keyshortcuts", "ArrowLeft ArrowRight ArrowUp ArrowDown PageUp PageDown Home End Escape");
  dotTip.setAttribute("aria-live", "polite");
  let kbDot = -1;
  const clearKb = () => grid.querySelectorAll(".d.kb").forEach((el) => el.classList.remove("kb"));
  grid.addEventListener("keydown", (ev) => {
    const jump = { ArrowRight: 1, ArrowLeft: -1, ArrowDown: 20, ArrowUp: -20, PageDown: 100, PageUp: -100 };
    if (ev.key === "Escape") { clearKb(); hideDotTip(); return; }
    if (!(ev.key in jump) && ev.key !== "Home" && ev.key !== "End") return;
    ev.preventDefault();
    const all = grid.querySelectorAll(".d");
    if (!all.length) return;
    kbDot = ev.key === "Home" ? 0 : ev.key === "End" ? all.length - 1 : clamp((kbDot < 0 ? 0 : kbDot) + (ev.key in jump ? jump[ev.key] : 0), 0, all.length - 1);
    clearKb();
    const el = all[kbDot];
    el.classList.add("kb");
    el.scrollIntoView({ block: "nearest" });
    showDotTip(el);
  });
  grid.addEventListener("blur", () => { clearKb(); hideDotTip(); });
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
        if (en.isIntersecting) links.forEach((a) => {
          const on = a.getAttribute("href") === "#" + en.target.id;
          a.classList.toggle("active", on);
          if (on) a.setAttribute("aria-current", "true"); else a.removeAttribute("aria-current");
        });
      });
    }, { rootMargin: "-40% 0px -55% 0px" });
    ["summary", "drivers", "predict", "target", "budget", "customers", "data-quality"].forEach((id) => io.observe($(id)));
  }

  updateSegCounts();
  paintTheme();
  renderAll();
  renderQuality();

  /* ---------- Optional backend: set apiBase in config.js ----------
     Expects GET {apiBase}/api/customers -> JSON array (see docs/API.md).
     If it is empty or unreachable, the dashboard keeps the built-in sample data. */
  const apiBase = ((window.ECONO_CONFIG || {}).apiBase || "").replace(/\/$/, "");
  const apiStatus = $("apiStatus");
  function loadApi() {
    if (!apiBase) return;
    apiStatus.hidden = false;
    apiStatus.textContent = "Connecting to the data server… the first request can take up to a minute.";
    const ctl = new AbortController(), timer = setTimeout(() => ctl.abort(), 60000);
    fetch(apiBase + "/api/customers", { headers: { Accept: "application/json" }, signal: ctl.signal })
      .then((r) => { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
      .then((list) => {
        const API_MAX_ROWS = 5000;
        // null, undefined and "" must not turn into 0
        const num = (v) => (v === null || v === undefined || (typeof v === "string" && v.trim() === "") ? NaN : Number(v));
        const ok = (c) => {
          if (!c) return false;
          const e = num(c.engagement), p = num(c.previous_purchases), d = num(c.discount), b = num(c.purchase);
          return Number.isInteger(e) && e >= 0 && e <= 10 &&
            Number.isFinite(p) && p >= 0 && p <= 10 &&
            (d === 0 || d === 1) && (b === 0 || b === 1);
        };
        const all = Array.isArray(list) ? list : [];
        const good = all.filter(ok);
        if (!good.length) throw new Error("no valid rows");
        const rows = good.slice(0, API_MAX_ROWS).map((c, i) => ({
          customer_id: i + 1,
          previous_purchases: Math.round(num(c.previous_purchases)),
          engagement: num(c.engagement),
          discount: num(c.discount),
          purchase: num(c.purchase),
          // optional fields from the backend model (see docs/API.md)
          ite: Number.isFinite(num(c.ite)) ? num(c.ite) : undefined,
          recommended_discount: Number.isFinite(num(c.recommended_discount)) && num(c.recommended_discount) >= 0 ? num(c.recommended_discount) : undefined,
        }));
        const capped = good.length > API_MAX_ROWS ? ` (first ${fmt(API_MAX_ROWS)} of ${fmt(good.length)})` : "";
        setData(rows, `Live data from the API: ${fmt(rows.length)} customers${capped}`, all.length - good.length, true);
        apiStatus.hidden = true;
      })
      .catch(() => {
        apiStatus.innerHTML = 'Could not reach the data server, showing sample data. <button type="button" class="link" id="apiRetry">Try again</button>';
        $("apiRetry").addEventListener("click", loadApi);
      })
      .finally(() => clearTimeout(timer));
  }
  // Read-only access for budget.js (budget allocation section)
  window.ECONO_APP = { customers: () => customers, model: () => model, sample: () => sampleData, usingCustom: () => usingCustom };
  loadApi();

  // One-time reveal: the squares fill in when the page loads
  $("people").classList.add("intro");
  setTimeout(() => $("people").classList.remove("intro"), 2000);
})();


/* ---------- Scroll progress bar + "seen once" reveals (visual polish only) ---------- */
(function () {
  var h = document.querySelector(".site-header");
  if (h) {
    var bar = document.createElement("div");
    bar.className = "scroll-bar"; bar.setAttribute("aria-hidden", "true");
    h.appendChild(bar);
    var tick = function () {
      var max = document.documentElement.scrollHeight - innerHeight;
      bar.style.setProperty("--p", max > 0 ? Math.min(1, scrollY / max) : 0);
    };
    addEventListener("scroll", tick, { passive: true }); addEventListener("resize", tick); tick();
  }
  var els = document.querySelectorAll(".sec-head, .stats");
  if (!("IntersectionObserver" in window)) { els.forEach(function (e) { e.classList.add("in"); }); return; }
  var io = new IntersectionObserver(function (list) {
    list.forEach(function (x) { if (x.isIntersecting) { x.target.classList.add("in"); io.unobserve(x.target); } });
  }, { threshold: 0.35 });
  els.forEach(function (e) { io.observe(e); });
})();