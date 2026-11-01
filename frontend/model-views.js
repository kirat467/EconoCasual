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

  async function load() {
    try {
      const [curve, drift] = await Promise.all([get("/api/uplift-curve"), get("/api/drift")]);
      drawQini(curve);
      const bad = drift.features.filter((f) => f.drift).map((f) => f.name);
      $("causalDrift").innerHTML = drift.drift_detected
        ? `<p class="causal-warn"><strong>Data drift detected</strong> in ${bad.join(", ")}. The model's estimates may no longer be reliable. <em>(Example result: until there is a live data feed, the API returns a simulated shift.)</em></p>` : "";
      await optimize();
    } catch (e) { $("causalSummary").textContent = "Could not reach the model API: " + e.message; }
  }
  $("causalGo").addEventListener("click", optimize);
  load();
})();
