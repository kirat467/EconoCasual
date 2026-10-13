/* EconoCasual · customer intelligence dashboard
   Synthetic sample data, descriptive statistics only (no causal claims).
   Charts are drawn as inline SVG, so the page works without any CDN. */
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
  const MIN_N = 5; // hide chart points built on fewer customers than this

  const SEGMENTS = {
    all: { test: () => true },
    high: { test: (c) => c.engagement >= 7 },
    low: { test: (c) => c.engagement <= 3 },
    repeat: { test: (c) => c.previous_purchases >= 5 },
  };

  const state = { seg: "all", search: "", outcome: "all", sort: "customer_id", dir: 1, page: 1, size: 10 };
  let toastTimer;

  const segmentRows = () => customers.filter(SEGMENTS[state.seg].test);
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

  /* Discount gap after comparing customers within the same engagement band */
  function adjustedGap(rows) {
    const bands = [[0, 3], [4, 6], [7, 10]];
    let sum = 0, weight = 0;
    bands.forEach(([lo, hi]) => {
      const g = rows.filter((c) => c.engagement >= lo && c.engagement <= hi);
      const d = g.filter((c) => c.discount === 1), n = g.filter((c) => c.discount === 0);
      if (d.length >= MIN_N && n.length >= MIN_N) {
        sum += (rate(d) - rate(n)) * g.length;
        weight += g.length;
      }
    });
    return weight ? sum / weight : null;
  }

  /* ---------- Hero + stats ---------- */
  function renderHero(rows) {
    const n = rows.length;
    const bought = rows.filter((c) => c.purchase === 1).length;
    const d = rows.filter((c) => c.discount === 1);
    const nd = rows.filter((c) => c.discount === 0);
    const dr = rate(d), nr = rate(nd);
    const adj = adjustedGap(rows);

    if (!n) {
      $("headline").textContent = "No customers in this group.";
      $("subline").textContent = "Pick another group above to see results.";
      return;
    }

    $("headline").innerHTML =
      `${fmt(bought)} of ${fmt(n)} customers bought. ` +
      (dr != null && nr != null
        ? `With a discount, <span class="with">${pct(dr)}</span> did; without, <span class="without">${pct(nr)}</span>.`
        : "There is not enough discount data to compare.");

    let sub = "";
    if (dr != null && nr != null) {
      const gap = (dr - nr) * 100;
      sub = `That is a ${Math.abs(gap).toFixed(1)}-point ${gap >= 0 ? "higher" : "lower"} rate for customers offered a discount.`;
      if (adj != null) sub += ` Among customers with similar engagement the gap is ${(adj * 100).toFixed(1)} points.`;
    }
    $("subline").textContent = sub;

    $("splitFill").style.width = (bought / n) * 100 + "%";
    $("keyBought").textContent = fmt(bought);
    $("keyNot").textContent = fmt(n - bought);

    $("sTotal").textContent = fmt(n);
    $("sTotalNote").textContent = state.seg === "all" ? "full sample" : `of ${fmt(customers.length)} in the sample`;
    $("sRate").textContent = pct(bought / n, 1);
    $("sRateNote").textContent = `${fmt(bought)} purchases recorded`;
    $("sEng").textContent = (rows.reduce((a, c) => a + c.engagement, 0) / n).toFixed(1);
    $("sDisc").textContent = pct(d.length / n, 1);
    $("sDiscNote").textContent = `${fmt(d.length)} customers`;
  }

  /* ---------- Trend chart (SVG) ---------- */
  const W = 680, H = 330, M = { l: 44, r: 16, t: 14, b: 38 };
  const IW = W - M.l - M.r, IH = H - M.t - M.b;
  const xAt = (e) => M.l + (e / 10) * IW;
  let trend = null;

  function renderTrend(rows) {
    const svg = $("trend");
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);

    const series = [
      { key: 1, cls: "with", label: "With discount" },
      { key: 0, cls: "without", label: "No discount" },
    ].map((s) => ({
      ...s,
      pts: range(11).map((e) => {
        const g = rows.filter((c) => c.engagement === e && c.discount === s.key);
        return { e, n: g.length, r: g.length >= MIN_N ? rate(g) : null };
      }),
    }));

    const counts = range(11).map((e) => rows.filter((c) => c.engagement === e).length);
    const maxN = Math.max(...counts, 1);
    const vals = series.flatMap((s) => s.pts.map((p) => p.r)).filter((v) => v != null);
    const yMax = Math.min(1, Math.ceil((Math.max(...vals, 0.2) + 0.04) * 5) / 5);
    const yAt = (r) => M.t + IH - (r / yMax) * IH;
    trend = { series, counts, xAt, yAt };

    let out = "";
    for (let v = 0; v <= yMax + 1e-9; v += 0.2) {
      out += `<line class="grid" x1="${M.l}" x2="${W - M.r}" y1="${yAt(v)}" y2="${yAt(v)}"/>` +
             `<text x="${M.l - 8}" y="${yAt(v) + 4}" text-anchor="end">${Math.round(v * 100)}%</text>`;
    }
    counts.forEach((n, e) => {
      const h = (n / maxN) * 38, bw = (IW / 11) * 0.55;
      out += `<rect class="count" x="${xAt(e) - bw / 2}" y="${M.t + IH - h}" width="${bw}" height="${h}" rx="2"/>`;
    });
    out += `<line class="axis" x1="${M.l}" x2="${W - M.r}" y1="${M.t + IH}" y2="${M.t + IH}"/>`;
    range(11).forEach((e) => (out += `<text x="${xAt(e)}" y="${H - 16}" text-anchor="middle">${e}</text>`));
    out += `<text x="${M.l + IW / 2}" y="${H - 1}" text-anchor="middle">Engagement score</text>`;

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

    // Text alternative for screen readers
    const hi = rows.filter((c) => c.engagement >= 7), lo = rows.filter((c) => c.engagement <= 3);
    $("trendDesc").textContent =
      `Line chart of purchase rate by engagement score. Customers scoring 7 to 10 buy at ${pct(rate(hi))}, ` +
      `customers scoring 0 to 3 buy at ${pct(rate(lo))}. Points with fewer than ${MIN_N} customers are hidden.`;
  }

  function onTrendMove(ev) {
    if (!trend) return;
    const svg = $("trend"), box = svg.getBoundingClientRect();
    const vx = ((ev.clientX - box.left) / box.width) * W;
    const e = clamp(Math.round(((vx - M.l) / IW) * 10), 0, 10);
    const g = $("guide"), tip = $("tip");
    g.setAttribute("x1", trend.xAt(e)); g.setAttribute("x2", trend.xAt(e)); g.setAttribute("visibility", "visible");

    const line = (s, cls) => {
      const p = s.pts[e];
      return `<div><span class="${cls}">${s.label}:</span> ${p.r == null ? "too few customers" : `<b>${pct(p.r)}</b>`} (${p.n})</div>`;
    };
    tip.innerHTML = `<div><b>Engagement ${e}</b> · ${trend.counts[e]} customers</div>` +
      line(trend.series[0], "t-with") + line(trend.series[1], "t-without");
    tip.hidden = false;
    const wrapW = $("trendWrap").clientWidth;
    const px = (trend.xAt(e) / W) * wrapW;
    tip.style.left = clamp(px, 90, wrapW - 90) + "px";
  }
  function onTrendLeave() { $("tip").hidden = true; const g = $("guide"); if (g) g.setAttribute("visibility", "hidden"); }

  /* ---------- Discount comparison, past purchases, notes ---------- */
  function renderCompare(rows) {
    const d = rows.filter((c) => c.discount === 1), nd = rows.filter((c) => c.discount === 0);
    const dr = rate(d), nr = rate(nd), adj = adjustedGap(rows);
    const item = (cls, label, r, n) =>
      `<li class="${cls}"><div class="row"><span>${label}</span><b>${pct(r, 1)}</b></div>` +
      `<div class="track"><i style="width:${(r || 0) * 100}%"></i></div><small>${fmt(n)} customers</small></li>`;
    $("compare").innerHTML = item("with", "Offered a discount", dr, d.length) + item("without", "No discount", nr, nd.length);

    if (dr == null || nr == null) { $("gapLine").textContent = "Not enough customers in both groups to compare."; return; }
    const gap = (dr - nr) * 100;
    $("gapLine").innerHTML =
      `<strong>${gap >= 0 ? "+" : "−"}${Math.abs(gap).toFixed(1)} points</strong> overall` +
      (adj != null ? `<span>${adj >= 0 ? "+" : "−"}${Math.abs(adj * 100).toFixed(1)} points when comparing customers with similar engagement (low, mid and high bands).</span>` : "");
  }

  function renderPrev(rows) {
    const bands = [[0, 2, "0–2 past purchases"], [3, 5, "3–5 past purchases"], [6, 8, "6–8 past purchases"], [9, 10, "9–10 past purchases"]];
    $("prevBars").innerHTML = bands.map(([lo, hi, label]) => {
      const g = rows.filter((c) => c.previous_purchases >= lo && c.previous_purchases <= hi);
      const r = g.length >= MIN_N ? rate(g) : null;
      return `<li><span class="k">${label}</span><span class="bar"><i style="width:${(r || 0) * 100}%"></i></span>` +
             `<span class="v">${pct(r)}</span><span class="n">${fmt(g.length)} customers</span></li>`;
    }).join("");
  }

  function renderNotes(rows) {
    const n = rows.length;
    if (!n) { $("notes").innerHTML = "<li>No customers in this group.</li>"; return; }
    const hi = rows.filter((c) => c.engagement >= 7), lo = rows.filter((c) => c.engagement <= 3);
    const rep = rows.filter((c) => c.previous_purchases >= 5);
    const buyers = rows.filter((c) => c.purchase === 1);
    const items = [];
    if (hi.length >= MIN_N && lo.length >= MIN_N)
      items.push(`<b>Engagement lines up with buying.</b> Customers scoring 7–10 bought at ${pct(rate(hi))}; those scoring 0–3 bought at ${pct(rate(lo))}.`);
    if (buyers.length)
      items.push(`<b>Repeat customers carry the sales.</b> Customers with 5 or more past purchases make up ${pct(rep.filter((c) => c.purchase).length / buyers.length)} of recorded purchases and ${pct(rep.length / n)} of this group.`);
    const adj = adjustedGap(rows);
    if (adj != null)
      items.push(`<b>Compare like with like.</b> The discount gap is ${(adj * 100).toFixed(1)} points once engagement is held roughly constant, so check this number before reading much into the headline gap.`);
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
      `<tr><td class="id">CUST-${String(c.customer_id).padStart(4, "0")}</td>` +
      `<td class="num">${c.previous_purchases}</td>` +
      `<td><span class="meter"><span>${c.engagement}/10</span><i style="--v:${c.engagement}"></i></span></td>` +
      `<td>${c.discount ? '<span class="tag offer">Offered</span>' : '<span class="tag no">Not offered</span>'}</td>` +
      `<td><span class="tag ${c.purchase ? "yes" : "no"}">${c.purchase ? "Purchased" : "Did not purchase"}</span></td></tr>`
    ).join("") || '<tr><td class="empty" colspan="5">No customers match. Clear the search or choose another outcome.</td></tr>';

    $("summaryText").textContent = rows.length
      ? `Showing ${start + 1}–${Math.min(start + state.size, rows.length)} of ${fmt(rows.length)} customers`
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
    renderHero(rows); renderTrend(rows); renderCompare(rows); renderPrev(rows); renderNotes(rows); renderTable();
  }

  /* ---------- Actions ---------- */
  function toast(msg) {
    const t = $("toast");
    t.textContent = msg; t.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => t.classList.remove("show"), 2600);
  }

  function exportCsv() {
    const rows = tableRows();
    const cols = ["customer_id", "previous_purchases", "engagement", "discount", "purchase"];
    const csv = [cols.join(","), ...rows.map((c) => cols.map((k) => c[k]).join(","))].join("\n");
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
    const a = document.createElement("a");
    a.href = url; a.download = "econocasual-customers.csv"; a.click();
    URL.revokeObjectURL(url);
    toast(`Exported ${fmt(rows.length)} customer records`);
  }

  document.querySelectorAll(".seg").forEach((b) =>
    b.addEventListener("click", () => {
      state.seg = b.dataset.seg; state.page = 1;
      document.querySelectorAll(".seg").forEach((s) => {
        const on = s === b; s.classList.toggle("is-on", on); s.setAttribute("aria-pressed", on);
      });
      renderAll();
    })
  );
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
  $("trend").addEventListener("pointermove", onTrendMove);
  $("trend").addEventListener("pointerleave", onTrendLeave);

  // Highlight the nav link for the section in view
  const links = [...document.querySelectorAll(".nav a")];
  if ("IntersectionObserver" in window) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((en) => {
        if (en.isIntersecting) links.forEach((a) => a.classList.toggle("active", a.getAttribute("href") === "#" + en.target.id));
      });
    }, { rootMargin: "-40% 0px -55% 0px" });
    ["summary", "drivers", "customers"].forEach((id) => io.observe($(id)));
  }

  renderAll();
})();
