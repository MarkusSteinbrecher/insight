/* insights.js — Critical Insights page */

function initInsights(url) {
  fetch(url)
    .then(r => r.json())
    .then(data => {
      renderStats(data.summary, data.total_findings, data.total_contradictions);
      renderAvg(data.summary);
      renderBingo(data.summary.top_bingo_terms);
      renderCards(data.analyses);
      renderContradictions(data.contradiction_analyses || []);
      bindFilters();
      bindSort();
    })
    .catch(e => console.error("insights load error:", e));
}

const V = {
  genuine_insight:       { label: "Genuine Insight",       color: "#34a853" },
  partial_insight:       { label: "Partial Insight",       color: "#fbbc04" },
  important_but_obvious: { label: "Important but Obvious", color: "#9aa0a6" },
  platitude:             { label: "Platitude",             color: "#ea4335" },
};

/* ── Stats ── */
function renderStats(s, total, contra) {
  const el = document.getElementById("verdict-stats");
  if (!el) return;
  const order = ["genuine_insight", "partial_insight", "important_but_obvious", "platitude"];
  let h = `<div class="i-stat-item i-stat-total"><div class="i-stat-num">${total}</div><div class="i-stat-lbl">Findings</div></div>`;
  order.forEach(v => {
    const c = (s.verdicts && s.verdicts[v]) || 0;
    h += `<div class="i-stat-item"><div class="i-stat-bar" style="background:${V[v].color}"></div><div class="i-stat-num">${c}</div><div class="i-stat-lbl">${V[v].label}s</div></div>`;
  });
  if (contra > 0) {
    h += `<div class="i-stat-item"><div class="i-stat-bar" style="background:#a142f4"></div><div class="i-stat-num">${contra}</div><div class="i-stat-lbl">Contradictions</div></div>`;
  }
  el.innerHTML = h;
}

/* ── Averages ── */
function renderAvg(s) {
  const el = document.getElementById("avg-scores");
  if (!el) return;
  el.innerHTML = [
    ["Platitude", s.avg_platitude_score, "#ea4335"],
    ["Actionability", s.avg_actionability_score, "#34a853"],
    ["Novelty", s.avg_novelty_score, "#4285f4"],
  ].map(([l, v, c]) =>
    `<span class="i-avg-pill"><span class="i-avg-label">${l}</span><span class="i-avg-val" style="color:${c}">${v}</span><span class="i-avg-max">/10</span></span>`
  ).join("");
}

/* ── Bingo ── */
function renderBingo(terms) {
  const el = document.getElementById("bingo-terms");
  if (!el || !terms || !terms.length) return;
  el.innerHTML = terms.map(t =>
    `<span class="i-bingo-chip">${esc(t.term)}<span class="i-bingo-count">${t.count}</span></span>`
  ).join("");
}

/* ── Score bar ── */
function bar(label, val, color) {
  const pct = Math.round((val / 10) * 100);
  return `<div class="i-bar-row">
    <span class="i-bar-label">${label}</span>
    <div class="i-bar-track"><div class="i-bar-fill" style="width:${pct}%;background:${color}"></div></div>
    <span class="i-bar-val">${val}</span>
  </div>`;
}

/* ── Cards ── */
function renderCards(analyses) {
  const el = document.getElementById("insights-cards");
  if (!el) return;
  el.innerHTML = analyses.map(a => {
    const v = V[a.verdict] || V.platitude;
    const bingo = (a.bullshit_bingo_terms && a.bullshit_bingo_terms.length)
      ? `<div class="i-card-bingo">${a.bullshit_bingo_terms.map(t => `<span class="i-bingo-chip-sm">${esc(t)}</span>`).join("")}</div>` : "";
    const actions = (a.what_to_actually_do && a.what_to_actually_do.length)
      ? `<div class="i-section"><div class="i-section-title">What to actually do</div><ol class="i-action-list">${a.what_to_actually_do.map(s => `<li>${esc(s)}</li>`).join("")}</ol></div>` : "";

    return `<article class="i-card" data-verdict="${a.verdict}" data-id="${a.id}"
              data-platitude="${a.platitude_score}" data-actionability="${a.actionability_score}"
              data-novelty="${a.novelty_score}" data-sources="${a.source_count || 0}">
      <div class="i-card-head" onclick="toggleCard(this)">
        <div class="i-card-badge" style="background:${v.color}"></div>
        <div class="i-card-main">
          <div class="i-card-meta">
            <span class="i-card-verdict" style="color:${v.color}">${v.label}</span>
            <span class="i-card-scores">${a.source_count || "?"} sources &middot; P:${a.platitude_score} &middot; A:${a.actionability_score} &middot; N:${a.novelty_score}</span>
          </div>
          <div class="i-card-statement">${esc(a.statement)}</div>
        </div>
        <svg class="i-card-chevron" viewBox="0 0 24 24" width="20" height="20"><path d="M7 10l5 5 5-5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </div>
      <div class="i-card-body">
        <div class="i-bars">
          ${bar("Platitude", a.platitude_score, "#ea4335")}
          ${bar("Actionability", a.actionability_score, "#34a853")}
          ${bar("Novelty", a.novelty_score, "#4285f4")}
        </div>
        ${bingo}
        <div class="i-section i-section-critique">
          <div class="i-section-title">The Critique</div>
          <div class="i-section-text">${fmt(a.the_critique)}</div>
        </div>
        <div class="i-section">
          <div class="i-section-title">What it actually means</div>
          <div class="i-section-text">${fmt(a.what_it_actually_means)}</div>
        </div>
        <div class="i-section">
          <div class="i-section-title">The practical value</div>
          <div class="i-section-text">${fmt(a.the_practical_value)}</div>
        </div>
        ${actions}
        <div class="i-section i-section-bottom">
          <div class="i-section-title">Bottom line</div>
          <div class="i-section-text"><strong>${fmt(a.bottom_line)}</strong></div>
        </div>
        ${a.who_this_matters_to ? `<div class="i-card-audience">Matters to: ${esc(a.who_this_matters_to)}</div>` : ""}
      </div>
    </article>`;
  }).join("");
}

/* ── Contradictions ── */
function renderContradictions(items) {
  const el = document.getElementById("contradiction-cards");
  const heading = document.getElementById("contradictions-heading");
  if (!el || !items.length) return;
  if (heading) heading.style.display = "";

  el.innerHTML = items.map(c => {
    const tensionTag = c.is_real_tension !== undefined
      ? `<span style="color:${c.is_real_tension ? '#ea4335' : '#34a853'};font-weight:600;font-size:0.75rem">${c.is_real_tension ? 'Real tension' : 'False tension'}</span>` : "";
    return `<article class="i-card i-card-contra" data-verdict="contradiction">
      <div class="i-card-head" onclick="toggleCard(this)">
        <div class="i-card-badge" style="background:#a142f4"></div>
        <div class="i-card-main">
          <div class="i-card-meta"><span class="i-card-verdict" style="color:#a142f4">Tension</span>${tensionTag}</div>
          <div class="i-card-statement">${esc(c.tension)}</div>
        </div>
        <svg class="i-card-chevron" viewBox="0 0 24 24" width="20" height="20"><path d="M7 10l5 5 5-5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </div>
      <div class="i-card-body">
        <div class="i-section i-section-critique"><div class="i-section-title">The Critique</div><div class="i-section-text">${fmt(c.the_critique)}</div></div>
        <div class="i-section"><div class="i-section-title">What it actually means</div><div class="i-section-text">${fmt(c.what_it_actually_means)}</div></div>
        <div class="i-section"><div class="i-section-title">Practical resolution</div><div class="i-section-text">${fmt(c.practical_resolution)}</div></div>
        ${c.who_wins ? `<div class="i-card-audience">Who wins: ${esc(c.who_wins)}</div>` : ""}
        <div class="i-section i-section-bottom"><div class="i-section-title">Bottom line</div><div class="i-section-text"><strong>${fmt(c.bottom_line)}</strong></div></div>
      </div>
    </article>`;
  }).join("");
}

/* ── Interactions ── */
function toggleCard(el) { el.closest(".i-card").classList.toggle("open"); }

function bindFilters() {
  document.querySelectorAll(".i-chip").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".i-chip").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      const v = btn.dataset.verdict;
      document.querySelectorAll("#insights-cards .i-card").forEach(c => {
        c.style.display = (v === "all" || c.dataset.verdict === v) ? "" : "none";
      });
    });
  });
}

function bindSort() {
  const sel = document.getElementById("sort-select");
  if (!sel) return;
  sel.addEventListener("change", () => {
    const cont = document.getElementById("insights-cards");
    const cards = Array.from(cont.querySelectorAll(".i-card"));
    cards.sort((a, b) => {
      switch (sel.value) {
        case "actionability": return int(b, "actionability") - int(a, "actionability");
        case "novelty":       return int(b, "novelty") - int(a, "novelty");
        case "platitude":     return int(b, "platitude") - int(a, "platitude");
        case "sources":       return int(b, "sources") - int(a, "sources");
        default:              return a.dataset.id.localeCompare(b.dataset.id);
      }
    });
    cards.forEach(c => cont.appendChild(c));
  });
}

function int(el, key) { return parseInt(el.dataset[key]) || 0; }

function esc(s) {
  if (!s) return "";
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function fmt(s) {
  if (!s) return "";
  return esc(s).replace(/\n\n/g, "</p><p>").replace(/\n/g, "<br>");
}
