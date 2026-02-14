/* ── Data & State ────────────────────────────────────── */
let insightsData = null;
let sourcesData = null;
let currentFilter = 'all';
let currentSort = 'id';
let analysisPage = 1;
const PAGE_SIZE = 15;

/* ── Init ────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', async () => {
  initFindings();
  const [insights, sources] = await Promise.all([
    fetch('data/insights.json').then(r => r.json()),
    fetch('data/sources.json').then(r => r.json())
  ]);
  insightsData = insights;
  sourcesData = sources;
  renderVerdictChart();
  renderScores();
  renderAnalysisList();
  renderSourcesTable();
});

/* ── Findings toggle ─────────────────────────────────── */
function initFindings() {
  document.querySelectorAll('.finding-header').forEach(header => {
    header.addEventListener('click', () => {
      const card = header.closest('.finding-card');
      card.classList.toggle('open');
    });
  });
}

/* ── Verdict Chart ───────────────────────────────────── */
function renderVerdictChart() {
  if (!insightsData) return;
  const v = insightsData.summary.verdicts;
  const total = Object.values(v).reduce((a, b) => a + b, 0);
  const bars = [
    { key: 'genuine_insight', label: 'Genuine Insight', count: v.genuine_insight, cls: 'genuine' },
    { key: 'partial_insight', label: 'Partial Insight', count: v.partial_insight, cls: 'partial' },
    { key: 'important_but_obvious', label: 'Important but Obvious', count: v.important_but_obvious, cls: 'obvious' },
    { key: 'platitude', label: 'Platitude', count: v.platitude, cls: 'platitude' },
  ];
  const container = document.getElementById('verdict-bars');
  container.innerHTML = bars.map(b => `
    <div class="verdict-bar-row">
      <span class="verdict-bar-label">${b.label}</span>
      <div class="verdict-bar-track">
        <div class="verdict-bar-fill ${b.cls}" style="width: ${(b.count / total * 100).toFixed(1)}%"></div>
      </div>
      <span class="verdict-bar-count">${b.count}</span>
    </div>
  `).join('');
}

function renderScores() {
  if (!insightsData) return;
  const s = insightsData.summary;
  document.getElementById('score-platitude').textContent = s.avg_platitude_score.toFixed(1);
  document.getElementById('score-actionability').textContent = s.avg_actionability_score.toFixed(1);
  document.getElementById('score-novelty').textContent = s.avg_novelty_score.toFixed(1);
}

/* ── Analysis List ───────────────────────────────────── */
function getFilteredSorted() {
  let items = insightsData.analyses;
  if (currentFilter !== 'all') {
    items = items.filter(a => a.verdict === currentFilter);
  }
  items = [...items];
  switch (currentSort) {
    case 'novelty': items.sort((a, b) => b.scores.novelty - a.scores.novelty); break;
    case 'actionability': items.sort((a, b) => b.scores.actionability - a.scores.actionability); break;
    case 'platitude': items.sort((a, b) => b.scores.platitude - a.scores.platitude); break;
    default: break; // id order
  }
  return items;
}

function renderAnalysisList() {
  if (!insightsData) return;
  const items = getFilteredSorted();
  const totalPages = Math.ceil(items.length / PAGE_SIZE);
  if (analysisPage > totalPages) analysisPage = totalPages || 1;
  const start = (analysisPage - 1) * PAGE_SIZE;
  const pageItems = items.slice(start, start + PAGE_SIZE);

  document.getElementById('analysis-count').textContent =
    `Showing ${start + 1}\u2013${Math.min(start + PAGE_SIZE, items.length)} of ${items.length} findings`;

  const container = document.getElementById('analysis-list');
  container.innerHTML = pageItems.map(a => `
    <div class="analysis-card" data-id="${a.id}">
      <div class="analysis-card-head">
        <span class="analysis-id">${a.id}</span>
        <span class="verdict-badge ${a.verdict}">${formatVerdict(a.verdict)}</span>
      </div>
      <div class="analysis-statement">${esc(a.statement)}</div>
      <div class="analysis-bottomline">${esc(a.bottom_line)}</div>
      <div class="analysis-scores">
        <span title="Platitude score"><span class="score-dot" style="background:var(--platitude)"></span>Platitude ${a.scores.platitude}/10</span>
        <span title="Actionability score"><span class="score-dot" style="background:var(--genuine)"></span>Action ${a.scores.actionability}/10</span>
        <span title="Novelty score"><span class="score-dot" style="background:var(--accent)"></span>Novelty ${a.scores.novelty}/10</span>
      </div>
      <div class="analysis-detail">
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
  `).join('');

  // click to expand
  container.querySelectorAll('.analysis-card').forEach(card => {
    card.addEventListener('click', () => card.classList.toggle('open'));
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
  document.getElementById('analysis').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function setFilter(verdict) {
  currentFilter = verdict;
  analysisPage = 1;
  document.querySelectorAll('.filter-btn').forEach(b => {
    b.classList.toggle('active', b.dataset.filter === verdict);
  });
  renderAnalysisList();
}

function setSort(value) {
  currentSort = value;
  analysisPage = 1;
  renderAnalysisList();
}

function formatVerdict(v) {
  return v.replace(/_/g, ' ');
}

/* ── Sources Table ───────────────────────────────────── */
let sourceSortCol = 'id';
let sourceSortDir = 1;

function renderSourcesTable() {
  if (!sourcesData) return;
  let items = [...sourcesData.sources];

  switch (sourceSortCol) {
    case 'title': items.sort((a, b) => sourceSortDir * a.title.localeCompare(b.title)); break;
    case 'author': items.sort((a, b) => sourceSortDir * a.author.localeCompare(b.author)); break;
    case 'type': items.sort((a, b) => sourceSortDir * a.type.localeCompare(b.type)); break;
    case 'relevance': items.sort((a, b) => sourceSortDir * (a.relevance - b.relevance)); break;
    case 'date': items.sort((a, b) => sourceSortDir * String(a.date).localeCompare(String(b.date))); break;
    default: break;
  }

  const tbody = document.getElementById('sources-tbody');
  tbody.innerHTML = items.map((s, i) => `
    <tr>
      <td>${s.id.replace('source-', '')}</td>
      <td class="source-title">${s.url ? `<a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.title)}</a>` : esc(s.title)}</td>
      <td>${esc(s.author)}</td>
      <td><span class="type-badge ${s.type}">${s.type}</span></td>
      <td>${s.date || '—'}</td>
      <td class="relevance-dots">${renderRelevance(s.relevance)}</td>
    </tr>
  `).join('');
}

function sortSources(col) {
  if (sourceSortCol === col) {
    sourceSortDir *= -1;
  } else {
    sourceSortCol = col;
    sourceSortDir = col === 'relevance' ? -1 : 1;
  }
  renderSourcesTable();
}

function renderRelevance(n) {
  let out = '';
  for (let i = 1; i <= 5; i++) {
    out += i <= n
      ? '<span class="dot-filled">\u25CF</span>'
      : '<span class="dot-empty">\u25CF</span>';
  }
  return out;
}

/* ── Utilities ───────────────────────────────────────── */
function esc(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
