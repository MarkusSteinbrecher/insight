/* ── Data & State ────────────────────────────────────── */
let statsData = null;
let insightsData = null;
let sourcesData = null;
let findingsData = null;
let analysisPage = 1;
let baselineFilter = null; // null = show all, 'new'/'additional'/'common' = filter
const PAGE_SIZE = 15;

/* ── Init ────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', async () => {
  initFindings();
  const [stats, insights, sources, findings] = await Promise.all([
    fetch('data/stats.json').then(r => r.json()).catch(() => null),
    fetch('data/insights.json').then(r => r.json()),
    fetch('data/sources.json').then(r => r.json()),
    fetch('data/findings.json').then(r => r.json()).catch(() => null)
  ]);
  statsData = stats;
  insightsData = insights;
  sourcesData = sources;
  findingsData = findings;
  injectStats();
  renderAnalysisList();
  renderSourcesTable();
  renderFindingClaims();
  renderBaselineSection();
});

/* ── Stats Injection ─────────────────────────────────── */
function injectStats() {
  if (!statsData) return;
  document.querySelectorAll('[data-stat]').forEach(el => {
    const key = el.dataset.stat;
    if (!(key in statsData)) return;
    const val = statsData[key];
    el.textContent = typeof val === 'number' && val >= 1000 && !key.includes('year')
      ? val.toLocaleString()
      : val;
  });

  // Add baseline stat card and methodology paragraph if data exists
  if (statsData.baseline_new != null) {
    const methP = document.getElementById('methodology-baseline');
    if (methP) methP.style.display = '';

    // Hero baseline bar
    const heroBaseline = document.getElementById('hero-baseline');
    if (heroBaseline) {
      const c = statsData.baseline_common || 0;
      const a = statsData.baseline_additional || 0;
      const n = statsData.baseline_new || 0;
      const t = c + a + n;
      if (t) {
        heroBaseline.style.display = '';
        heroBaseline.innerHTML = `
          <a href="#baseline" class="hero-baseline-link">
            <div class="hero-baseline-label">Claim novelty</div>
            <div class="hero-baseline-bar">
              <div class="baseline-seg baseline-seg-new" style="width:${(n/t*100).toFixed(1)}%"></div>
              <div class="baseline-seg baseline-seg-additional" style="width:${(a/t*100).toFixed(1)}%"></div>
              <div class="baseline-seg baseline-seg-common" style="width:${(c/t*100).toFixed(1)}%"></div>
            </div>
            <div class="hero-baseline-labels">
              <span class="hero-bl-item"><span class="baseline-legend-dot new"></span>${n} new</span>
              <span class="hero-bl-item"><span class="baseline-legend-dot additional"></span>${a} additional</span>
              <span class="hero-bl-item"><span class="baseline-legend-dot common"></span>${c} common</span>
            </div>
          </a>
        `;
      }
    }
  }
}

/* ── Findings toggle ─────────────────────────────────── */
function initFindings() {
  document.querySelectorAll('.finding-header').forEach(header => {
    header.addEventListener('click', () => {
      const card = header.closest('.finding-card');
      card.classList.toggle('open');
    });
  });
}

/* ── Finding Claims (injected from findings.json) ───── */
function renderFindingClaims() {
  if (!findingsData || !findingsData.findings) return;

  findingsData.findings.forEach(finding => {
    const card = document.querySelector(`[data-finding-id="${finding.id}"]`);
    if (!card || !finding.claims.length) return;

    const body = card.querySelector('.finding-body');
    if (!body) return;

    const section = document.createElement('div');
    section.className = 'finding-claims';
    section.innerHTML = `
      <div class="finding-claims-header">
        <span class="finding-claims-label">Supporting Claims (${finding.claim_count})</span>
      </div>
      <div class="finding-claims-list">
        ${finding.claims.map(c => {
          const bBadge = c.baseline_category
            ? `<span class="baseline-badge baseline-${c.baseline_category}">${esc(c.baseline_category)}</span>`
            : '';
          return `
          <div class="finding-claim-item">
            <div class="finding-claim-head">
              <span class="analysis-id">${esc(c.id)}</span>${bBadge}
            </div>
            <div class="finding-claim-statement">${esc(c.bottom_line)}</div>
            ${renderSourceQuotes(c.sources)}
          </div>`;
        }).join('')}
      </div>
    `;

    body.appendChild(section);
  });

}

/* ── Analysis List ───────────────────────────────────── */
function renderAnalysisList() {
  if (!insightsData) return;
  const allItems = insightsData.analyses;
  const items = baselineFilter
    ? allItems.filter(a => a.baseline_category === baselineFilter)
    : allItems;
  const totalPages = Math.ceil(items.length / PAGE_SIZE);
  if (analysisPage > totalPages) analysisPage = totalPages || 1;
  const start = (analysisPage - 1) * PAGE_SIZE;
  const pageItems = items.slice(start, start + PAGE_SIZE);

  document.getElementById('analysis-count').innerHTML = baselineFilter
    ? `Showing ${start + 1}\u2013${Math.min(start + PAGE_SIZE, items.length)} of ${items.length} <strong>${baselineFilter}</strong> claims <a href="#" onclick="clearBaselineFilter(event)" class="filter-clear">show all</a>`
    : `Showing ${start + 1}\u2013${Math.min(start + PAGE_SIZE, items.length)} of ${items.length} claims`;

  const container = document.getElementById('analysis-list');
  container.innerHTML = pageItems.map(a => {
    const baselineBadge = a.baseline_category
      ? `<span class="baseline-badge baseline-${a.baseline_category}">${esc(a.baseline_category)}</span>`
      : '';
    return `
    <div class="analysis-card" data-id="${a.id}">
      <div class="analysis-card-head">
        <span class="analysis-id">${a.id}</span>${baselineBadge}
      </div>
      <div class="analysis-statement">${esc(a.bottom_line)}</div>
      <div class="analysis-detail">
        ${a.sources && a.sources.length ? `
        <div class="detail-section">
          <div class="detail-label">Source Segments (${a.sources.length} sources)</div>
          ${renderSourceQuotes(a.sources)}
        </div>` : ''}
        <div class="detail-section">
          <div class="detail-label">Critique</div>
          <p>${esc(a.critique)}</p>
        </div>
        <div class="detail-section">
          <div class="detail-label">Practical Value</div>
          <p>${esc(a.practical_value)}</p>
        </div>
        ${a.action_steps && a.action_steps.length ? `
        <div class="detail-section">
          <div class="detail-label">Action Steps</div>
          <ol class="action-steps">
            ${a.action_steps.map(s => `<li>${esc(s)}</li>`).join('')}
          </ol>
        </div>` : ''}
      </div>
    </div>
  `}).join('');

  // click to expand (ignore clicks on links)
  container.querySelectorAll('.analysis-card').forEach(card => {
    card.addEventListener('click', (e) => {
      if (e.target.closest('a')) return;
      card.classList.toggle('open');
    });
  });

  // pagination
  renderPagination(items.length, totalPages);
}

function renderPagination(total, totalPages) {
  const container = document.getElementById('analysis-pagination');
  if (totalPages <= 1) {
    container.innerHTML = '';
    return;
  }
  container.innerHTML = `
    <button class="page-btn" onclick="changePage(-1)" ${analysisPage <= 1 ? 'disabled' : ''}>Prev</button>
    <span class="page-info">${analysisPage} / ${totalPages}</span>
    <button class="page-btn" onclick="changePage(1)" ${analysisPage >= totalPages ? 'disabled' : ''}>Next</button>
  `;
}

function changePage(delta) {
  analysisPage += delta;
  renderAnalysisList();
  document.getElementById('claims').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/* ── Sources Table ───────────────────────────────────── */
let sourceSortCol = 'id';
let sourceSortDir = 1;

function buildSourceClaimIndex() {
  // Build: sourceId → [{ claimId, bottom_line, quotes[], findings[] }]
  const index = {};

  // Build claim → findings reverse map
  const claimToFindings = {};
  if (findingsData && findingsData.findings) {
    findingsData.findings.forEach(f => {
      (f.claims || []).forEach(c => {
        if (!claimToFindings[c.id]) claimToFindings[c.id] = [];
        claimToFindings[c.id].push({ id: f.id, title: f.title });
      });
    });
  }

  // Walk insights analyses to build source → claims
  if (insightsData && insightsData.analyses) {
    insightsData.analyses.forEach(a => {
      const claimId = a.id;
      const findings = claimToFindings[claimId] || [];
      (a.sources || []).forEach(src => {
        const sid = src.id || src;
        if (!index[sid]) index[sid] = [];
        const entry = {
          claimId,
          bottom_line: a.bottom_line || '',
          quotes: src.quotes || [],
          findings,
        };
        if (a.baseline_category) entry.baseline_category = a.baseline_category;
        index[sid].push(entry);
      });
    });
  }

  return index;
}

function renderSourcesTable() {
  if (!sourcesData) return;

  // Show legend if baseline data exists
  const legend = document.getElementById('sources-legend');
  if (legend && statsData && statsData.baseline_new != null) legend.style.display = '';

  let items = [...sourcesData.sources];

  const claimIndex = buildSourceClaimIndex();

  // Pre-compute baseline counts and relevance score per source
  items.forEach(s => {
    const claims = claimIndex[s.id] || [];
    s._claimCount = claims.length;
    s._baselineCounts = { common: 0, additional: 0, new: 0 };
    claims.forEach(c => {
      if (c.baseline_category && s._baselineCounts[c.baseline_category] != null) {
        s._baselineCounts[c.baseline_category]++;
      }
    });
    s._relevanceScore = (s._baselineCounts.new * 3) + (s._baselineCounts.additional * 1);
  });

  // Compute max score for normalization
  const maxScore = Math.max(...items.map(s => s._relevanceScore), 1);
  items.forEach(s => {
    s._relevanceDots = s._claimCount === 0 ? 0 : Math.max(1, Math.ceil(s._relevanceScore / maxScore * 5));
  });

  switch (sourceSortCol) {
    case 'title': items.sort((a, b) => sourceSortDir * a.title.localeCompare(b.title)); break;
    case 'author': items.sort((a, b) => sourceSortDir * a.author.localeCompare(b.author)); break;
    case 'type': items.sort((a, b) => sourceSortDir * a.type.localeCompare(b.type)); break;
    case 'claims': items.sort((a, b) => sourceSortDir * (a._claimCount - b._claimCount)); break;
    case 'relevance': items.sort((a, b) => sourceSortDir * (a._relevanceScore - b._relevanceScore)); break;
    case 'date': items.sort((a, b) => sourceSortDir * String(a.date).localeCompare(String(b.date))); break;
    default: break;
  }

  const tbody = document.getElementById('sources-tbody');
  tbody.innerHTML = items.map(s => {
    const claims = claimIndex[s.id] || [];
    const claimCount = claims.length;
    const hasDetail = claimCount || s.body_html;
    const chevron = hasDetail
      ? '<svg class="source-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>'
      : '';
    return `
    <tr class="source-row${hasDetail ? ' has-claims' : ''}" data-source-id="${s.id}">
      <td>${s.id.replace('source-', '')} ${chevron}</td>
      <td class="source-title">${s.url
        ? `<a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.title)}</a>`
        : `<a href="https://www.google.com/search?q=${encodeURIComponent(s.title)}" target="_blank" rel="noopener" title="Search for this document">${esc(s.title)}</a>`}</td>
      <td>${esc(s.author)}</td>
      <td>${renderTypeIcon(s.type)}</td>
      <td class="nowrap">${s.date || '\u2014'}</td>
      <td>${renderBaselineBar(s._baselineCounts, claimCount)}</td>
      <td>${renderRelevanceDots(s._relevanceDots)}</td>
    </tr>
    ${(s.body_html || claimCount) ? `
    <tr class="source-detail-row" data-source-detail="${s.id}">
      <td colspan="7">
        <div class="source-detail">
          ${s.body_html ? `
          <div class="source-accordion open" data-accordion="summary-${s.id}">
            <div class="source-accordion-header">
              <span class="source-accordion-title">Source Notes</span>
              <svg class="source-accordion-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>
            </div>
            <div class="source-accordion-body">
              <div class="source-body-html">${s.body_html}</div>
            </div>
          </div>` : ''}
          ${claimCount ? `
          <div class="source-accordion open" data-accordion="claims-${s.id}">
            <div class="source-accordion-header">
              <div class="source-accordion-header-row">
                <span class="source-accordion-title">${claimCount} Claim${claimCount !== 1 ? 's' : ''} Reference This Source</span>
                <div class="source-claims-legend">
                  <span class="source-legend-item" data-filter="new" data-source="${s.id}"><span class="baseline-legend-dot new"></span> New</span>
                  <span class="source-legend-item" data-filter="additional" data-source="${s.id}"><span class="baseline-legend-dot additional"></span> Additional</span>
                  <span class="source-legend-item" data-filter="common" data-source="${s.id}"><span class="baseline-legend-dot common"></span> Common</span>
                </div>
              </div>
              <svg class="source-accordion-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>
            </div>
            <div class="source-accordion-body">
              <div class="source-claims-list" data-claims-source="${s.id}">
              ${claims.map(c => {
                const srcBBadge = c.baseline_category
                  ? `<span class="baseline-badge baseline-${c.baseline_category}">${esc(c.baseline_category)}</span>`
                  : '';
                return `
                <div class="source-claim-item" data-claim-category="${c.baseline_category || ''}">
                  <div class="source-claim-head">
                    <span class="analysis-id">${esc(c.claimId)}</span>${srcBBadge}
                    ${c.findings.length ? c.findings.map(f =>
                      `<span class="finding-tag" title="${esc(f.title)}">Finding ${f.id.replace('finding-', '')}</span>`
                    ).join('') : ''}
                  </div>
                  <div class="source-claim-assessment">${esc(c.bottom_line)}</div>
                  ${c.quotes.length ? c.quotes.map(q =>
                    `<p class="source-quote">\u201c${esc(q)}\u201d</p>`
                  ).join('') : ''}
                </div>`;
              }).join('')}
              </div>
            </div>
          </div>` : ''}
        </div>
      </td>
    </tr>` : ''}`;
  }).join('');

  // Row accordion toggle (open/close detail row)
  tbody.querySelectorAll('.source-row.has-claims').forEach(row => {
    row.addEventListener('click', (e) => {
      if (e.target.closest('a')) return;
      const sid = row.dataset.sourceId;
      const detail = tbody.querySelector(`[data-source-detail="${sid}"]`);
      if (detail) {
        row.classList.toggle('open');
        detail.classList.toggle('open');
      }
    });
  });

  // Inner accordion toggle (summary / claims sections)
  tbody.querySelectorAll('.source-accordion-header').forEach(header => {
    header.addEventListener('click', (e) => {
      // Don't toggle if clicking a legend filter item
      if (e.target.closest('.source-legend-item')) return;
      const accordion = header.closest('.source-accordion');
      if (accordion) accordion.classList.toggle('open');
    });
  });

  // Claims legend filter
  tbody.querySelectorAll('.source-legend-item').forEach(item => {
    item.addEventListener('click', (e) => {
      e.stopPropagation();
      const category = item.dataset.filter;
      const sourceId = item.dataset.source;
      const claimsList = tbody.querySelector(`[data-claims-source="${sourceId}"]`);
      if (!claimsList) return;

      // Toggle active state
      const wasActive = item.classList.contains('active');
      // Clear all legend items for this source
      claimsList.closest('.source-accordion').querySelectorAll('.source-legend-item').forEach(li => li.classList.remove('active'));

      if (wasActive) {
        // Show all claims
        claimsList.querySelectorAll('.source-claim-item').forEach(ci => { ci.style.display = ''; });
      } else {
        item.classList.add('active');
        // Filter claims by category
        claimsList.querySelectorAll('.source-claim-item').forEach(ci => {
          ci.style.display = ci.dataset.claimCategory === category ? '' : 'none';
        });
      }
    });
  });
}

function sortSources(col) {
  if (sourceSortCol === col) {
    sourceSortDir *= -1;
  } else {
    sourceSortCol = col;
    sourceSortDir = (col === 'claims' || col === 'relevance') ? -1 : 1;
  }
  renderSourcesTable();
}

const TYPE_ICONS = {
  paper: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/><path d="M8 7h6"/><path d="M8 11h8"/></svg>',
  report: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><rect x="7" y="13" width="3" height="5" rx=".5"/><rect x="12" y="9" width="3" height="9" rx=".5"/><rect x="17" y="5" width="3" height="13" rx=".5"/></svg>',
  article: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M7 7h4v4H7z"/><path d="M13 7h4"/><path d="M13 11h4"/><path d="M7 15h10"/><path d="M7 19h7"/></svg>',
  blog: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/><path d="m15 5 4 4"/></svg>',
};

function renderTypeIcon(type) {
  const svg = TYPE_ICONS[type] || '';
  const label = type.charAt(0).toUpperCase() + type.slice(1);
  return `<span class="type-icon type-icon-${type}" title="${label}">${svg}<span class="type-icon-label">${label}</span></span>`;
}

function renderRelevanceDots(dots) {
  if (dots === 0) return '<span style="color:var(--text-muted)">\u2014</span>';
  let html = '<div class="relevance-dots">';
  for (let i = 1; i <= 5; i++) {
    html += `<span class="rel-dot${i <= dots ? ' filled' : ''}"></span>`;
  }
  html += '</div>';
  return html;
}

function renderBaselineBar(counts, total) {
  if (!total) return '<span style="color:var(--text-muted)">\u2014</span>';
  const segments = [
    { key: 'new', count: counts.new, color: '#16a34a', label: 'New' },
    { key: 'additional', count: counts.additional, color: '#bbf7d0', label: 'Additional' },
    { key: 'common', count: counts.common, color: '#cbd5e1', label: 'Common' },
  ].filter(s => s.count > 0);
  const tooltip = segments.map(s => `${s.count} ${s.label.toLowerCase()}`).join(', ');
  const bar = segments.map(s => {
    const pct = (s.count / total * 100).toFixed(1);
    return `<div class="baseline-seg baseline-seg-${s.key}" style="width:${pct}%" title="${s.count} ${s.label.toLowerCase()}"></div>`;
  }).join('');
  return `<div class="baseline-bar-wrap" title="${total} claims: ${tooltip}">
    <div class="baseline-bar">${bar}</div>
    <span class="baseline-bar-count">${total}</span>
  </div>`;
}

/* ── Baseline Section ────────────────────────────────── */
function filterByCategoryAndScroll(category) {
  baselineFilter = baselineFilter === category ? null : category;
  analysisPage = 1;
  renderAnalysisList();
  updateBaselineCardHighlights();
  // Scroll to the claim list (cards are already in the claims section)
  document.getElementById('analysis-count').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function clearBaselineFilter(e) {
  e.preventDefault();
  baselineFilter = null;
  analysisPage = 1;
  renderAnalysisList();
  updateBaselineCardHighlights();
}

function updateBaselineCardHighlights() {
  document.querySelectorAll('.baseline-category-card').forEach(card => {
    const cat = card.dataset.category;
    if (baselineFilter && cat !== baselineFilter) {
      card.classList.add('dimmed');
    } else {
      card.classList.remove('dimmed');
    }
  });
}

function renderBaselineSection() {
  if (!statsData || statsData.baseline_new == null) return;

  // ── Claims section: bar + category cards ──
  const claimsBaseline = document.getElementById('claims-baseline');
  if (claimsBaseline) {
    const common = statsData.baseline_common || 0;
    const additional = statsData.baseline_additional || 0;
    const newClaims = statsData.baseline_new || 0;
    const total = common + additional + newClaims;
    if (total) {
      const pctCommon = (common / total * 100).toFixed(0);
      const pctAdditional = (additional / total * 100).toFixed(0);
      const pctNew = (newClaims / total * 100).toFixed(0);

      claimsBaseline.style.display = '';
      claimsBaseline.innerHTML = `
        <div class="baseline-overview">
          <div class="baseline-bar-large">
            <div class="baseline-seg baseline-seg-new" style="width:${pctNew}%" title="${newClaims} new"></div>
            <div class="baseline-seg baseline-seg-additional" style="width:${pctAdditional}%" title="${additional} additional"></div>
            <div class="baseline-seg baseline-seg-common" style="width:${pctCommon}%" title="${common} common"></div>
          </div>
          <div class="baseline-cards">
            <div class="baseline-category-card baseline-cat-new" data-category="new" onclick="filterByCategoryAndScroll('new')">
              <div class="baseline-cat-count">${newClaims}</div>
              <div class="baseline-cat-label">New</div>
              <div class="baseline-cat-pct">${pctNew}%</div>
              <div class="baseline-cat-desc">Genuinely novel</div>
              <div class="baseline-cat-action">Filter claims</div>
            </div>
            <div class="baseline-category-card baseline-cat-additional" data-category="additional" onclick="filterByCategoryAndScroll('additional')">
              <div class="baseline-cat-count">${additional}</div>
              <div class="baseline-cat-label">Additional</div>
              <div class="baseline-cat-pct">${pctAdditional}%</div>
              <div class="baseline-cat-desc">Adds detail or angle</div>
              <div class="baseline-cat-action">Filter claims</div>
            </div>
            <div class="baseline-category-card baseline-cat-common" data-category="common" onclick="filterByCategoryAndScroll('common')">
              <div class="baseline-cat-count">${common}</div>
              <div class="baseline-cat-label">Common</div>
              <div class="baseline-cat-pct">${pctCommon}%</div>
              <div class="baseline-cat-desc">Readily found via search</div>
              <div class="baseline-cat-action">Filter claims</div>
            </div>
          </div>
        </div>
      `;
    }
  }

  // ── Baseline section: summary + sources accordion ──
  const section = document.getElementById('baseline');
  if (!section) return;
  section.style.display = '';

  const blSummary = statsData.baseline_summary || [];
  const blSources = statsData.baseline_sources || [];

  const container = document.getElementById('baseline-content');
  container.innerHTML = `
    ${blSummary.length ? `
    <div class="baseline-summary-list">
      ${blSummary.map(b => {
        // Render **bold** as <strong>
        const html = esc(b).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        return `<div class="baseline-summary-item">${html}</div>`;
      }).join('')}
    </div>` : ''}
    ${blSources.length ? `
    <div class="baseline-sources-accordion">
      <div class="baseline-sources-toggle" onclick="this.parentElement.classList.toggle('open')">
        <span>${blSources.length} web sources used as benchmark</span>
        <svg class="baseline-sources-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>
      </div>
      <div class="baseline-sources-body">
        <div class="baseline-sources-list">
          ${blSources.map((s, i) => `
            <div class="baseline-source-item">
              <span class="baseline-source-num">${i + 1}</span>
              <div class="baseline-source-body">
                ${s.url
                  ? `<a href="${esc(s.url)}" target="_blank" rel="noopener" class="baseline-source-title">${esc(s.title)}</a>`
                  : `<span class="baseline-source-title">${esc(s.title)}</span>`}
                <div class="baseline-source-summary">${esc(s.summary)}</div>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    </div>` : ''}
  `;
}

/* ── Utilities ───────────────────────────────────────── */
function esc(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function renderSourceQuotes(sources) {
  if (!sources || !sources.length) return '';
  return sources.map(s => {
    const quotes = (s.quotes || []).map(q =>
      `<p class="source-quote">\u201c${esc(q)}\u201d</p>`
    ).join('');
    const url = esc(s.url || '');
    const link = url
      ? `<a href="${url}" class="source-link" target="_blank" rel="noopener">${esc(s.title)}</a>`
      : esc(s.title);
    return `
      <div class="source-quote-block">
        ${quotes}
        <div class="source-quote-attribution">${link}</div>
      </div>`;
  }).join('');
}
