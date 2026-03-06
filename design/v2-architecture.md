# Insight v2 — Architecture Overview

Status: **MVP in progress** (Milestone 1 complete)
Started: 2026-03-06

Product vision: [product-vision.md](product-vision.md)

Component designs: [Collector](collector.md) | [Knowledge Graph](knowledge-graph.md) | [Analyzer](analyzer.md) | [Presenter](presenter.md)

Specifications: [Graph Schema](specs/graph-schema.md) | [Collector](specs/collector.md) | Analyzer (TODO) | Presenter (TODO)

Release plan: [release-plan.md](release-plan.md)

---

## Vision

Help consultants go from "I want to research topic X" to "I have a defensible, sourced position" in days instead of weeks — by building a knowledge graph that captures every source, every claim, every relationship, and makes the landscape visible.

Four components, each with a single responsibility, connected through a central graph.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    1. COLLECTOR                          │
│  Web scraping, document ingestion, source management    │
│  Writes: source nodes, raw content blocks               │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│               2. KNOWLEDGE GRAPH (KuzuDB)               │
│  Nodes: sources, content blocks, segments, claims,      │
│         concepts, findings, recommendations, angles     │
│  Edges: contains, supports, contradicts, relates_to,    │
│         based_on, from_source                           │
│  Single source of truth for all components              │
└──────────┬──────────────────────────────────┬───────────┘
           │                                  │
           ▼                                  ▼
┌─────────────────────────┐   ┌───────────────────────────┐
│     3. ANALYZER          │   │    4. PRESENTER           │
│  Segmentation, claim     │   │  Static site with graph   │
│  extraction, alignment,  │   │  explorer                 │
│  critique, synthesis     │   │                           │
│  Reads + writes graph    │   │  Reads exported JSON      │
└──────────────────────────┘   └───────────────────────────┘
```

## Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Graph database | KuzuDB | Embedded (no server), Cypher queries, Python bindings, purpose-built for graph workloads |
| Web publishing | Static JSON export | KuzuDB is local-only; export at build time, site reads JSON. Keeps GitHub Pages deployment. |
| Frontend framework | TBD | Vanilla JS won't scale for graph explorer. Svelte or React candidates. |
| Analysis engine | Claude Code | Claude Code performs analysis during command execution — no programmatic API calls |
| Content extraction | Playwright, Docling, youtube-transcript-api, Whisper | Per-format extractors, structured output with location anchors |

## Component Summary

Each component has its own design document with full details.

### 1. Collector ([detail](collector.md))
Ingests content from diverse sources (web, PDF, YouTube, audio, Office docs) and writes structured, position-anchored content blocks to the graph. No analysis — just faithful extraction with provenance metadata.

### 2. Knowledge Graph ([detail](knowledge-graph.md))
KuzuDB-backed central store. Typed nodes and edges with a Python query interface. Provides CRUD, traversal queries, and JSON export for the website. Schema-versioned.

### 3. Analyzer ([detail](analyzer.md))
All intelligence: segmentation, claim alignment, critical analysis, synthesis, insight generation. Operates incrementally against the graph. Each operation reads from and writes to the graph. Claude Code performs the analysis during command execution — there are no programmatic Claude API calls. The Python module provides graph operation helpers that Claude Code calls.

### 4. Presenter ([detail](presenter.md))
Static site with graph explorer for interactive knowledge traversal. Built from exported JSON. Deployed to GitHub Pages.

## The Traceability Chain

The core design principle — every piece of knowledge has an unbroken chain back to a specific location in a specific source:

```
Source → Content Block → Segment → Claim → Finding → Recommendation
         (page/timestamp/   (typed unit    (cross-source   (synthesized   (actionable
          slide/heading)     of meaning)    alignment)       pattern)       output)
```

Every arrow is an edge in the graph carrying location metadata. Any node can be traced backwards to its origins.

## What Changes from v1

| Aspect | v1 (current) | v2 |
|--------|-------------|-----|
| Data store | YAML files + Markdown | KuzuDB graph database |
| Data model | String references across files | Typed nodes and edges with Cypher queries |
| Source extraction | Flat markdown per source | Positioned content blocks with location anchors |
| Analysis mode | Batch (all sources at once) | Incremental (per-source, aligns against existing) |
| Build pipeline | 8 separate Python scripts | Single export module with parameterized queries |
| Traceability | Manual (grep across files) | Native graph traversal |
| Site | Vanilla JS SPA | Framework-based, graph explorer |
| Source types | Web + PDF | Web, PDF, YouTube, audio, Office docs |

## What Stays the Same

- Research methodology (phases 0-3 conceptually)
- Claude as the analysis engine
- Segment classification taxonomy (10 types)
- Static site deployed to GitHub Pages
- Markdown for narrative content (synthesis, insights)

---

## Development Process

```
Design doc → Spec → Tests (from acceptance criteria) → Code → Tests pass → Review
```

Each component follows this sequence. No code without a spec. No spec without acceptance criteria that become tests.

### Project Structure

```
insight/                   # Python package
├── __init__.py
├── graph.py               # Knowledge graph interface (KuzuDB)
├── collector/             # Discovery + extraction
│   ├── web.py             # Web page extractor
│   ├── youtube.py         # YouTube transcript extractor
│   ├── pdf.py             # PDF extractor (Docling)
│   └── cli.py             # CLI entry point
├── analyzer/              # Segmentation, alignment, critique (future)
└── exporter/              # Graph → JSON for website (future)

tests/
├── unit/                  # Fast, no network, mocked inputs
│   ├── test_graph.py
│   ├── test_web_extractor.py
│   ├── test_youtube_extractor.py
│   └── ...
├── integration/           # Full pipeline, optional network
│   ├── test_web_pipeline.py
│   └── ...
└── fixtures/              # Sample HTML, transcripts, etc.
    ├── sample_article.html
    ├── sample_transcript.json
    └── ...

design/
├── v2-architecture.md     # This file — high-level overview
├── collector.md           # Component design (intent, rationale, decisions)
├── knowledge-graph.md     # Component design
├── analyzer.md            # Component design
├── presenter.md           # Component design
└── specs/                 # Detailed specifications (contracts, interfaces, acceptance criteria)
    ├── graph-schema.md    # Node/edge types, Python API, queries
    ├── collector.md       # Extractors, discovery, registry
    ├── analyzer.md        # (future)
    └── presenter.md       # (future)
```

### Testing Strategy

- **Unit tests** (`tests/unit/`): Fast, no network. Mocked HTML/transcripts/API responses. Test extraction logic, graph operations, data transformations. Run on every change.
- **Integration tests** (`tests/integration/`): Full pipeline with real network or recorded responses. Marked with `@pytest.mark.integration`, skipped by default. Run explicitly with `pytest -m integration`.
- **Fixtures** (`tests/fixtures/`): Representative sample data — HTML pages, YouTube transcripts, PDF extracts. Used by unit tests to verify extraction without hitting the network.
- **Framework**: pytest with pytest-cov for coverage.
- **CI**: GitHub Actions running unit tests on push.

---

## Build Plan

Each milestone: spec → tests → code → validate.

### Milestone 1 — Graph Foundation ✓
- [x] Spec: graph schema (node/edge types, Python API)
- [x] Tests: 50 tests covering all acceptance criteria
- [x] Code: graph module (`insight/graph.py`)
- [x] Migration: v1 YAML → graph (56 sources, 892 blocks)
- [x] All tests pass (50/50)

### Milestone 2 — Collector (in progress)
- [x] Spec: extractors, discovery, registry, CLI
- [ ] Tests: web extraction (mocked HTML), YouTube (mocked transcript), registry logic
- [ ] Code: web extractor, YouTube extractor, CLI
- [ ] Integration tests: collect a real web source + YouTube video
- [ ] Tests pass

### Milestone 3 — Analyzer
- [ ] Spec: graph helper functions, data contracts, command integration
- [ ] Tests: graph helpers (segment writing, claim alignment, traceability)
- [ ] Code: analyzer module (graph operations, no API calls)
- [ ] Tests pass

### Milestone 4 — Presenter
- [ ] Spec: export format, site architecture, views
- [ ] Code: exporter, new site
- [ ] Tests pass

### Milestone 5 — Cleanup & CI
- [ ] GitHub Actions for unit tests
- [ ] Remove v1 pipeline
- [ ] Update CLAUDE.md

---

## Decisions Made

1. **Graph database**: KuzuDB (embedded, Cypher, Python bindings)
2. **Project structure**: Python package (`insight/`) with submodules
3. **Testing**: pytest, unit + integration, fixtures for offline testing
4. **Multi-topic**: One graph, topic as a property on Source nodes
5. **Content block granularity**: Paragraph-level from Collector, sentence-level from Analyzer
6. **Image storage**: Files on disk, referenced from graph nodes, visual extractions as separate nodes
7. **Source versioning**: Not needed. Registry tracks collected sources, manual re-collect if needed.
8. **Discovery/extraction split**: Separate responsibilities with registry check between them

## Open Questions

1. **Frontend framework** — Svelte vs React vs other?
2. **CI scope** — GitHub Actions for tests only, or also build + deploy the site?
