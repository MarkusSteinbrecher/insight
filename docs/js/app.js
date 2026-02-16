/* ── Data & State ────────────────────────────────────── */
let topicsData = null;
let currentTopic = null;
let statsData = null;
let insightsData = null;
let sourcesData = null;
let findingsData = null;
let useCasesData = null;
let analysisPage = 1;
let ucCategoryFilter = null;
let ucMaturityFilter = null;
let baselineFilter = null;
const PAGE_SIZE = 15;

/* ── Init ────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', async () => {
  // Load topics manifest
  topicsData = await fetch('data/topics.json').then(r => r.json()).catch(() => null);

  // Determine which topic to show
  const params = new URLSearchParams(window.location.search);
  const requestedTopic = params.get('topic');

  if (topicsData && topicsData.topics.length) {
    currentTopic = topicsData.topics.find(t => t.slug === requestedTopic)
      || topicsData.topics.find(t => t.slug === topicsData.default_topic)
      || topicsData.topics[0];
    renderTopicNav();
    await loadTopic(currentTopic.slug);
  } else {
    // Fallback: try loading from flat data/ directory (legacy)
    currentTopic = { slug: '', title: 'Research', phase: 3 };
    await loadTopicData('');
  }

  updateStickyOffsets();
  window.addEventListener('resize', updateStickyOffsets);
});

function renderTopicNav() {
  const list = document.getElementById('topic-nav-list');
  if (!topicsData || !topicsData.topics.length) return;
  list.innerHTML = topicsData.topics.map(t => {
    const active = t.slug === currentTopic.slug ? ' active' : '';
    const phaseLabel = t.phase < 2 ? `<span class="topic-pill-phase">Phase ${t.phase}</span>` : '';
    return `<a class="topic-pill${active}" href="?topic=${t.slug}" onclick="switchTopic(event,'${t.slug}')">${esc(t.title)}${phaseLabel}</a>`;
  }).join('');
}

async function switchTopic(e, slug) {
  e.preventDefault();
  if (slug === currentTopic.slug) return;
  currentTopic = topicsData.topics.find(t => t.slug === slug);
  window.history.pushState({}, '', `?topic=${slug}`);
  renderTopicNav();
  await loadTopic(slug);
}

async function loadTopic(slug) {
  // Reset state
  analysisPage = 1;
  baselineFilter = null;
  statsData = null;
  insightsData = null;
  sourcesData = null;
  findingsData = null;
  useCasesData = null;
  ucCategoryFilter = null;
  ucMaturityFilter = null;

  await loadTopicData(slug);
}

async function loadTopicData(slug) {
  const base = slug ? `data/${slug}` : 'data';

  const [stats, insights, sources, findings, useCases] = await Promise.all([
    fetch(`${base}/stats.json`).then(r => r.ok ? r.json() : null).catch(() => null),
    fetch(`${base}/insights.json`).then(r => r.ok ? r.json() : null).catch(() => null),
    fetch(`${base}/sources.json`).then(r => r.ok ? r.json() : null).catch(() => null),
    fetch(`${base}/findings.json`).then(r => r.ok ? r.json() : null).catch(() => null),
    fetch(`${base}/use-cases.json`).then(r => r.ok ? r.json() : null).catch(() => null),
  ]);

  statsData = stats;
  insightsData = insights;
  sourcesData = sources;
  findingsData = findings;
  useCasesData = useCases;

  renderPage();
}

/* ── Page Render ─────────────────────────────────────── */
function renderPage() {
  const phase = currentTopic.phase != null ? currentTopic.phase : 3;
  const hasFindings = findingsData && findingsData.findings && findingsData.findings.length;
  const hasClaims = insightsData && insightsData.analyses && insightsData.analyses.length;
  const hasSources = sourcesData && sourcesData.sources && sourcesData.sources.length;
  const hasBaseline = statsData && statsData.baseline_new != null;
  const hasUseCases = useCasesData && useCasesData.use_cases && useCasesData.use_cases.length;

  // Update page title
  document.title = `${currentTopic.title || 'Research'} — Research Synthesis`;

  // Hero
  renderHero();

  // Section visibility based on data availability
  const showSections = (id, show) => {
    const el = document.getElementById(id);
    if (el) el.style.display = show ? '' : 'none';
  };

  showSections('early-phase-banner', phase < 2 && !hasFindings);
  showSections('exec-summary-section', phase >= 2 || hasFindings);
  showSections('findings', hasFindings);
  showSections('use-cases', hasUseCases);
  showSections('claims', hasClaims);
  showSections('baseline', hasBaseline);
  showSections('methodology', phase >= 1 && hasClaims);

  // Update section nav links based on what's visible
  updateSectionNav(hasFindings, hasClaims, hasBaseline, hasUseCases);

  // Early phase banner
  if (phase < 2 && !hasFindings) {
    renderEarlyPhaseBanner();
  }

  // Exec summary
  renderExecSummary();

  // Findings
  if (hasFindings) {
    renderFindings();
  }

  // Use Cases
  if (hasUseCases) {
    renderUseCases();
  }

  // Claims
  if (hasClaims) {
    renderAnalysisList();
  }

  // Sources
  if (hasSources) {
    renderSourcesTable();
  }

  // Baseline
  if (hasBaseline) {
    renderBaselineSection();
  }

  // Methodology
  if (phase >= 1 && hasClaims) {
    renderMethodology();
  }

  // Footer
  renderFooter();
}

function renderHero() {
  const title = currentTopic.title || 'Research';
  document.getElementById('hero-title').textContent = title;

  const sources = statsData ? statsData.sources : (currentTopic.source_count || 0);
  const yearMin = statsData ? statsData.source_year_min : '';
  const yearMax = statsData ? statsData.source_year_max : '';
  const claims = statsData ? statsData.canonical_claims : 0;
  const findings = statsData ? statsData.key_findings : 0;

  // Subtitle
  const subtitle = document.getElementById('hero-subtitle');
  if (subtitle) subtitle.style.display = 'none';

  // Meta
  const meta = document.getElementById('hero-meta');
  const metaParts = [];
  if (sources) {
    const yearRange = yearMin && yearMax ? ` (${yearMin}\u2013${yearMax})` : '';
    metaParts.push(`${sources} sources${yearRange}`);
  }
  if (claims) metaParts.push(`${claims} canonical claims analyzed`);
  metaParts.push('Updated February 2026');
  meta.innerHTML = metaParts.map(m => `<span>${m}</span>`).join('');

  // Stats strip
  const statsStrip = document.getElementById('hero-stats');
  const cards = [];
  const ucCount = useCasesData ? useCasesData.total_use_cases : 0;
  if (findings) cards.push(`<a class="stat-card" href="#findings"><div class="number">${findings}</div><div class="label">Findings</div></a>`);
  if (ucCount) cards.push(`<a class="stat-card" href="#use-cases"><div class="number">${ucCount}</div><div class="label">Use Cases</div></a>`);
  if (claims) cards.push(`<a class="stat-card" href="#claims"><div class="number">${claims}</div><div class="label">Claims</div></a>`);
  if (sources) cards.push(`<a class="stat-card" href="#sources"><div class="number">${sources}</div><div class="label">Sources</div></a>`);
  statsStrip.innerHTML = cards.join('');

  // Baseline bar in hero
  const heroBaseline = document.getElementById('hero-baseline');
  if (statsData && statsData.baseline_new != null) {
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
    } else {
      heroBaseline.style.display = 'none';
    }
  } else {
    heroBaseline.style.display = 'none';
  }
}

function updateSectionNav(hasFindings, hasClaims, hasBaseline, hasUseCases) {
  const nav = document.getElementById('section-nav');
  const links = [];
  if (hasFindings) links.push('<a class="nav-link" href="#findings">Findings</a>');
  if (hasUseCases) links.push('<a class="nav-link" href="#use-cases">Use Cases</a>');
  if (hasClaims) links.push('<a class="nav-link" href="#claims">Claims</a>');
  links.push('<a class="nav-link" href="#sources">Sources</a>');
  if (hasBaseline) links.push('<a class="nav-link" href="#baseline">Baseline</a>');
  nav.innerHTML = links.join('');
}

function renderEarlyPhaseBanner() {
  const phase = currentTopic.phase != null ? currentTopic.phase : 0;
  const sources = statsData ? statsData.sources : (currentTopic.source_count || 0);

  const phases = [
    { label: 'Data gathering', step: 0 },
    { label: 'Analysis', step: 1 },
    { label: 'Synthesis', step: 2 },
    { label: 'Conclusions', step: 3 },
  ];

  document.getElementById('early-phase-title').textContent =
    phase === 0 ? 'Research in Progress' : 'Analysis in Progress';
  document.getElementById('early-phase-desc').textContent =
    phase === 0
      ? `This topic is in the data gathering phase. ${sources} sources collected so far.`
      : `This topic is being analyzed. ${sources} sources are being processed through the extraction pipeline.`;

  document.getElementById('early-phase-progress').innerHTML = phases.map(p => {
    const cls = p.step < phase ? 'completed' : p.step === phase ? 'current' : '';
    return `<span class="phase-step ${cls}"><span class="phase-dot"></span>${p.label}</span>`;
  }).join('');
}

function renderExecSummary() {
  const el = document.getElementById('exec-summary');
  if (!statsData) {
    el.innerHTML = '';
    return;
  }
  const s = statsData;
  if (s.canonical_claims) {
    el.innerHTML = `
      <p>This synthesis draws from ${s.sources} sources published between ${s.source_year_min} and ${s.source_year_max}, spanning practitioner articles, academic research, industry reports, and analyst frameworks. Cross-source analysis identified ${s.canonical_claims} canonical claims \u2014 themes where two or more sources agree \u2014 along with ${s.unique_claims || 0} unique positions and ${s.contradictions || 0} direct contradictions.</p>
    `;
  } else {
    el.innerHTML = `<p>${s.sources} sources have been gathered for this topic. Analysis will begin once data gathering is complete.</p>`;
  }
}

/* ── Findings (dynamic from JSON) ────────────────────── */
function renderFindings() {
  if (!findingsData || !findingsData.findings) return;

  const heading = document.getElementById('findings-heading');
  const s = statsData || {};
  heading.textContent = `Key findings from ${s.sources || '?'} sources and ${s.canonical_claims || '?'} claims`;

  const container = document.getElementById('findings-list');
  container.innerHTML = findingsData.findings.map((f, i) => {
    const num = String(i + 1).padStart(2, '0');
    const bodyHtml = f.body_html || '';
    const practitioner = f.practitioner_text
      ? `<div class="practitioner-box"><strong>Practitioner implication:</strong> ${esc(f.practitioner_text)}</div>`
      : '';

    return `
    <div class="finding-card" data-finding-id="${esc(f.id)}">
      <div class="finding-header">
        <span class="finding-number">${num}</span>
        <div class="finding-content">
          <div class="finding-title">${esc(f.title)}</div>
          <div class="finding-bottomline">${esc(f.bottom_line || '')}</div>
        </div>
        <svg class="finding-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>
      </div>
      <div class="finding-body">
        ${bodyHtml}
        ${practitioner}
      </div>
    </div>`;
  }).join('');

  // Toggle behavior
  container.querySelectorAll('.finding-header').forEach(header => {
    header.addEventListener('click', () => {
      header.closest('.finding-card').classList.toggle('open');
    });
  });

  // Inject supporting claims into finding bodies
  renderFindingClaims();
}

/* ── Finding Claims (injected from findings.json) ───── */
function renderFindingClaims() {
  if (!findingsData || !findingsData.findings) return;

  findingsData.findings.forEach(finding => {
    const card = document.querySelector(`[data-finding-id="${finding.id}"]`);
    if (!card || !finding.claims || !finding.claims.length) return;

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
            <div class="finding-claim-statement">${esc(c.bottom_line || c.statement)}</div>
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

  const heading = document.getElementById('claims-heading');
  if (heading && statsData) {
    heading.textContent = `${statsData.canonical_claims || '?'} claims from cross-source analysis`;
  }

  const allItems = insightsData.analyses || [];
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

  container.querySelectorAll('.analysis-card').forEach(card => {
    card.addEventListener('click', (e) => {
      if (e.target.closest('a')) return;
      card.classList.toggle('open');
    });
  });

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
  const index = {};
  const claimToFindings = {};
  if (findingsData && findingsData.findings) {
    findingsData.findings.forEach(f => {
      (f.claims || []).forEach(c => {
        if (!claimToFindings[c.id]) claimToFindings[c.id] = [];
        claimToFindings[c.id].push({ id: f.id, title: f.title });
      });
    });
  }

  if (insightsData && insightsData.analyses) {
    // Build from critical analysis (primary source)
    insightsData.analyses.forEach(a => {
      const claimId = a.id;
      const findings = claimToFindings[claimId] || [];
      (a.sources || []).forEach(src => {
        const sid = src.id || src;
        if (!index[sid]) index[sid] = [];
        const entry = {
          claimId,
          bottom_line: a.bottom_line || a.statement || '',
          quotes: src.quotes || [],
          findings,
        };
        if (a.baseline_category) entry.baseline_category = a.baseline_category;
        index[sid].push(entry);
      });
    });
  } else if (findingsData && findingsData.findings) {
    // Fallback: build from findings data when no critical analysis exists
    findingsData.findings.forEach(f => {
      (f.claims || []).forEach(c => {
        const claimId = c.id;
        const findings = claimToFindings[claimId] || [];
        (c.sources || []).forEach(src => {
          const sid = src.id || src;
          if (!index[sid]) index[sid] = [];
          const entry = {
            claimId,
            bottom_line: c.bottom_line || c.statement || '',
            quotes: src.quotes || [],
            findings,
          };
          if (c.baseline_category) entry.baseline_category = c.baseline_category;
          index[sid].push(entry);
        });
      });
    });
  }

  return index;
}

function renderSourcesTable() {
  if (!sourcesData) return;

  const heading = document.getElementById('sources-heading');
  if (heading && statsData) {
    const yearRange = statsData.source_year_min && statsData.source_year_max
      ? ` (${statsData.source_year_min}\u2013${statsData.source_year_max})`
      : '';
    heading.textContent = `${statsData.sources} sources analyzed${yearRange}`;
  } else if (heading && sourcesData.sources) {
    heading.textContent = `${sourcesData.sources.length} sources`;
  }

  const legend = document.getElementById('sources-legend');
  if (legend && statsData && statsData.baseline_new != null) legend.style.display = '';
  else if (legend) legend.style.display = 'none';

  let items = [...sourcesData.sources];
  const claimIndex = buildSourceClaimIndex();

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
                  <div class="source-claim-assessment">${esc(c.bottom_line || c.statement || '')}</div>
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

  // Row accordion toggle
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

  // Inner accordion toggle
  tbody.querySelectorAll('.source-accordion-header').forEach(header => {
    header.addEventListener('click', (e) => {
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

      const wasActive = item.classList.contains('active');
      claimsList.closest('.source-accordion').querySelectorAll('.source-legend-item').forEach(li => li.classList.remove('active'));

      if (wasActive) {
        claimsList.querySelectorAll('.source-claim-item').forEach(ci => { ci.style.display = ''; });
      } else {
        item.classList.add('active');
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
  const label = type ? type.charAt(0).toUpperCase() + type.slice(1) : '';
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
    { key: 'new', count: counts.new, label: 'New' },
    { key: 'additional', count: counts.additional, label: 'Additional' },
    { key: 'common', count: counts.common, label: 'Common' },
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

  // Claims section: bar + category cards
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

  // Baseline section: summary + sources accordion
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

/* ── Methodology ─────────────────────────────────────── */
function renderMethodology() {
  const el = document.getElementById('methodology-content');
  if (!el || !statsData) return;
  const s = statsData;
  let html = `<p>${s.sources} sources were collected through web research and document ingestion. Each source was broken into numbered segments (sentences, bullets, table rows) and classified by type (claim, statistic, evidence, definition, recommendation, context, methodology, example, attribution, noise). This produced ${(s.total_segments || 0).toLocaleString()} total segments across all sources.</p>`;
  html += `<p>Cross-source claim alignment identified ${s.canonical_claims} canonical claims (themes where 2+ sources agree), ${s.unique_claims || 0} unique claims (single-source positions), and ${s.contradictions || 0} direct contradictions. Each canonical claim was then critically assessed for practical value, with supporting source segments traced back to their origins.</p>`;
  if (s.baseline_new != null) {
    html += `<p>Claims were also evaluated against a common-knowledge baseline \u2014 a web search on the core research question \u2014 to assess novelty. Each claim was categorised as <em>common</em> (readily found via search), <em>additional</em> (adds detail beyond baseline), or <em>new</em> (genuinely novel observation).</p>`;
  }
  el.innerHTML = html;
}

/* ── Use Cases ───────────────────────────────────────── */
function renderUseCases() {
  if (!useCasesData || !useCasesData.use_cases) return;
  const ucs = useCasesData.use_cases;
  const maturity = useCasesData.maturity || {};

  // Intro
  const intro = document.getElementById('uc-intro');
  if (intro) {
    const deployed = maturity.deployed || 0;
    const emerging = maturity.emerging || 0;
    const conceptual = maturity.conceptual || 0;
    intro.textContent = `${ucs.length} concrete use cases identified across ${useCasesData.sources_scanned || 0} sources \u2014 ${deployed} deployed, ${emerging} emerging, ${conceptual} conceptual.`;
  }

  // Maturity bar
  const barEl = document.getElementById('uc-maturity-bar');
  if (barEl) {
    const total = ucs.length || 1;
    const d = maturity.deployed || 0;
    const e = maturity.emerging || 0;
    const c = maturity.conceptual || 0;
    const mActive = m => ucMaturityFilter === m ? ' active' : '';
    barEl.innerHTML = `
      <div class="uc-bar">
        <div class="uc-bar-seg uc-bar-deployed${mActive('deployed')}" style="width:${(d/total*100).toFixed(1)}%" title="${d} deployed" onclick="filterUseCaseMaturity('deployed')"></div>
        <div class="uc-bar-seg uc-bar-emerging${mActive('emerging')}" style="width:${(e/total*100).toFixed(1)}%" title="${e} emerging" onclick="filterUseCaseMaturity('emerging')"></div>
        <div class="uc-bar-seg uc-bar-conceptual${mActive('conceptual')}" style="width:${(c/total*100).toFixed(1)}%" title="${c} conceptual" onclick="filterUseCaseMaturity('conceptual')"></div>
      </div>
      <div class="uc-bar-labels">
        <span class="uc-bar-label${mActive('deployed')}" onclick="filterUseCaseMaturity('deployed')"><span class="uc-dot uc-dot-deployed"></span>${d} Deployed</span>
        <span class="uc-bar-label${mActive('emerging')}" onclick="filterUseCaseMaturity('emerging')"><span class="uc-dot uc-dot-emerging"></span>${e} Emerging</span>
        <span class="uc-bar-label${mActive('conceptual')}" onclick="filterUseCaseMaturity('conceptual')"><span class="uc-dot uc-dot-conceptual"></span>${c} Conceptual</span>
      </div>`;
  }

  // Category filters
  const filtersEl = document.getElementById('uc-filters');
  if (filtersEl) {
    const cats = useCasesData.categories || {};
    const sorted = Object.entries(cats).sort((a, b) => b[1] - a[1]);
    const catLabels = {
      planning: 'Planning', scheduling: 'Scheduling', risk_management: 'Risk Mgmt',
      resource_allocation: 'Resources', reporting: 'Reporting', communication: 'Communication',
      decision_support: 'Decisions', cost_management: 'Cost Mgmt',
      knowledge_management: 'Knowledge', governance: 'Governance', other: 'Other',
      quality_assurance: 'Quality',
    };
    const pills = sorted.map(([cat, count]) => {
      const active = ucCategoryFilter === cat ? ' active' : '';
      const label = catLabels[cat] || cat.replace(/_/g, ' ');
      return `<button class="uc-filter-pill${active}" onclick="filterUseCases('${cat}')">${label} <span class="uc-filter-count">${count}</span></button>`;
    });
    const allActive = !ucCategoryFilter ? ' active' : '';
    filtersEl.innerHTML = `<button class="uc-filter-pill${allActive}" onclick="filterUseCases(null)">All <span class="uc-filter-count">${ucs.length}</span></button>` + pills.join('');
  }

  // Grid
  renderUseCaseGrid();
}

function filterUseCases(cat) {
  ucCategoryFilter = ucCategoryFilter === cat ? null : cat;
  renderUseCases();
}

function filterUseCaseMaturity(mat) {
  ucMaturityFilter = ucMaturityFilter === mat ? null : mat;
  renderUseCases();
}

function renderUseCaseGrid() {
  const grid = document.getElementById('uc-grid');
  if (!grid || !useCasesData) return;

  let ucs = useCasesData.use_cases;
  if (ucCategoryFilter) {
    ucs = ucs.filter(uc => uc.category === ucCategoryFilter);
  }
  if (ucMaturityFilter) {
    ucs = ucs.filter(uc => uc.maturity === ucMaturityFilter);
  }

  const catLabels = {
    planning: 'Planning', scheduling: 'Scheduling', risk_management: 'Risk Mgmt',
    resource_allocation: 'Resources', reporting: 'Reporting', communication: 'Communication',
    decision_support: 'Decisions', cost_management: 'Cost Mgmt',
    knowledge_management: 'Knowledge', governance: 'Governance', other: 'Other',
    quality_assurance: 'Quality',
  };

  grid.innerHTML = ucs.map(uc => {
    const matClass = `uc-maturity-${uc.maturity || 'emerging'}`;
    const matLabel = (uc.maturity || 'emerging').charAt(0).toUpperCase() + (uc.maturity || 'emerging').slice(1);
    const catLabel = catLabels[uc.category] || uc.category;
    const evidence = (uc.evidence || []).map(e =>
      `<li class="uc-evidence-item">${esc(typeof e === 'string' ? e : e.toString())}</li>`
    ).join('');
    const evidenceBlock = evidence
      ? `<ul class="uc-evidence-list">${evidence}</ul>`
      : '';
    const srcCount = uc.source_count || (uc.sources || []).length;

    return `
      <div class="uc-card">
        <div class="uc-card-header">
          <span class="uc-card-cat">${esc(catLabel)}</span>
          <span class="uc-badge ${matClass}">${matLabel}</span>
        </div>
        <h3 class="uc-card-title">${esc(uc.use_case)}</h3>
        <p class="uc-card-desc">${esc(uc.description)}</p>
        ${evidenceBlock}
        <div class="uc-card-footer">
          <span class="uc-src-count">${srcCount} source${srcCount !== 1 ? 's' : ''}</span>
        </div>
      </div>`;
  }).join('');
}

/* ── Footer ──────────────────────────────────────────── */
function renderFooter() {
  const el = document.getElementById('footer-content');
  if (!el) return;
  const title = currentTopic.title || 'Research';
  const sources = statsData ? statsData.sources : (currentTopic.source_count || 0);
  el.textContent = sources
    ? `Research Agent \u2014 ${title} \u00b7 Synthesised from ${sources} published sources`
    : `Research Agent \u2014 ${title}`;
}

/* ── Sticky Offsets ──────────────────────────────────── */
function updateStickyOffsets() {
  const disclaimer = document.querySelector('.disclaimer-bar');
  const topicNav = document.querySelector('.topic-nav');
  const sectionNav = document.querySelector('.nav');

  let offset = 0;
  if (disclaimer) {
    offset += disclaimer.offsetHeight;
  }
  if (topicNav) {
    topicNav.style.top = offset + 'px';
    offset += topicNav.offsetHeight;
  }
  if (sectionNav) {
    sectionNav.style.top = offset + 'px';
  }
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
