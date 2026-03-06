# Backlog

Work items for Insight. Organized by MVP milestone. Items follow spec-driven workflow: spec → tests → code → validate.

Sponsor: User | PM/Engineering: Claude Code

Current target: **MVP** — end-to-end research on one topic (collect → segment → align → view)

---

## MVP Milestone 1 — Graph Foundation

The graph schema and Python API. Everything else builds on this.

### Done
- [x] **G.1** Set up `insight/` Python package structure
- [x] **G.2** Add KuzuDB dependency, verify installation
- [x] **G.3** Implement KuzuDB schema (Source, ContentBlock, VisualExtraction + edges)
- [x] **G.4** Implement `insight/graph.py` — CRUD, queries, utilities
- [x] **G.5** Write v1→v2 migration script
- [x] **G.6** Run migration — 56 EA for AI sources, 892 content blocks
- [x] **G.7** Write graph schema spec (`design/specs/graph-schema.md`)

### Open

(All items complete — milestone done.)

### Recently Completed
- [x] **G.8** Extend graph schema for MVP: add Segment, Claim node tables + SEGMENTED_FROM, SUPPORTS, CONTRADICTS edges
- [x] **G.9** Write unit tests for graph module (50 tests, AC-S1 through AC-EC6)
- [x] **G.10** All graph tests pass (50/50)

---

## MVP Milestone 2 — Collector

Discovery + extraction for web and YouTube. Source registry.

### Done
- [x] **C.1** Write collector spec (`design/specs/collector.md`)
- [x] **C.2** Draft web extractor (`insight/collector/web.py`)
- [x] **C.3** Draft YouTube extractor (`insight/collector/youtube.py`)
- [x] **C.4** Draft CLI (`insight/collector/cli.py`)

### Done
- [x] **C.5** Implement discovery module (`insight/collector/discovery.py`) — URL normalization, registry check
- [x] **C.6** Create test fixtures — sample HTML page, nested elements, minimal page
- [x] **C.7** Write unit tests — web extraction (23 tests, AC-W1 through AC-W9)
- [x] **C.8** Write unit tests — YouTube extraction (19 tests, AC-Y1 through AC-Y6)
- [x] **C.9** Write unit tests — discovery (19 tests, AC-D1 through AC-D5)

### Open
- [ ] **C.10** Write integration tests — web + YouTube pipelines, source registry
- [ ] **C.11** All collector tests pass (unit: 61/61, integration: TBD)
- [ ] **C.12** End-to-end: collect a real web source into graph
- [ ] **C.13** End-to-end: collect a real YouTube video into graph

---

## MVP Milestone 3 — Analyzer (core)

Segmentation and claim alignment only. Critical analysis, gap detection, synthesis are MLP.

### Open
- [ ] **A.1** Write analyzer spec — segmentation + claim alignment operations
- [ ] **A.2** Implement segmentation (ContentBlock → Segment nodes in graph)
- [ ] **A.3** Implement claim alignment (Segment → Claim nodes, consensus/contradiction/unique)
- [ ] **A.4** Write unit tests for segmentation
- [ ] **A.5** Write unit tests for claim alignment
- [ ] **A.6** All analyzer tests pass
- [ ] **A.7** End-to-end: segment a source, align claims across sources

---

## MVP Milestone 4 — Presenter (basic)

Source list and claim list. No graph explorer — that's MLP.

### Open
- [ ] **P.1** Write presenter spec — MVP views (source list, claim list), JSON export format
- [ ] **P.2** Implement graph → JSON exporter (sources, claims with attribution)
- [ ] **P.3** Build basic static site — source list with metadata, claim list with source links
- [ ] **P.4** Deploy to GitHub Pages
- [ ] **P.5** All presenter tests pass

---

## MVP Milestone 5 — Integration & Polish

Wire everything together, update docs.

### Open
- [ ] **X.1** Update `/research` command to use Collector
- [ ] **X.2** Update `/analyze` command to use Analyzer
- [ ] **X.3** Update `/status` command to report from graph
- [ ] **X.4** Set up GitHub Actions (unit tests on push)
- [ ] **X.5** Update CLAUDE.md for MVP state
- [ ] **X.6** MVP validation: full topic research end-to-end

---

## MLP (after MVP) — not yet scheduled

### Collector
- [ ] PDF extractor (Docling + visual extraction)
- [ ] PowerPoint extractor
- [ ] Word doc extractor
- [ ] Parallel collection
- [ ] Source coverage analysis

### Graph
- [ ] Finding, Recommendation, Concept node tables
- [ ] RELATES_TO, BASED_ON edges
- [ ] Graph traversal queries (evidence chains)
- [ ] Rich JSON export for graph explorer

### Analyzer
- [ ] Critical analysis (claim strength, practical value)
- [ ] Baseline comparison (novel vs common knowledge)
- [ ] Gap detection
- [ ] Synthesis generation
- [ ] Interactive discussion
- [ ] Findings extraction
- [ ] Recommendations + thought leadership angles

### Presenter
- [ ] Interactive graph explorer
- [ ] Source coverage dashboard
- [ ] Evidence chain drill-down
- [ ] Content drafting view

---

## Project Management

### Done
- [x] Product vision doc (`design/product-vision.md`)
- [x] Architecture overview (`design/v2-architecture.md`)
- [x] Component design docs (collector, graph, analyzer, presenter)
- [x] Specs: graph schema, collector
- [x] ADR structure + initial decisions
- [x] Ways of working doc
- [x] Rewrite CLAUDE.md as product guide
- [x] Rewrite README.md
- [x] Update `/status` command
- [x] Set up pyproject.toml, test structure, .gitignore

---

## v1 Backlog (paused — superseded by v2)

<details>
<summary>v1 open items</summary>

- [ ] 1.3.1 merge-critical-analysis.py
- [ ] 1.3.2 Batch step 1.3
- [ ] 1.4.1 Section-by-section cross-source analysis
- [ ] 1.5.1 prepare-baseline-eval.py
- [ ] 1.6.1 Section-by-section synthesis

</details>

<details>
<summary>v1 completed items</summary>

- [x] 1.1.1 segment-source.py
- [x] 1.1.2 Integrate into /analyze
- [x] 1.2.1 prepare-alignment.py
- [x] 1.2.2 Use pre-clustered input
- [x] 2.1.1 scrape-sources.py
- [x] 2.1.2 Integrate into /research
- [x] 2.2.1 check-progress.py
- [x] 2.3.1 audit-claims.py integration
- [x] 2.4.1 build-usecases-data.py
- [x] 3.1.1 Rewrite /analyze with 4-step pipeline
- [x] 3.1.2 Resume support for /analyze
- [x] 3.2.1 Scope document-analyst agent
- [x] 3.3.1–3.3.3 CLAUDE.md updates
- [x] 4.1.1–4.4.1 Cleanup items

</details>
