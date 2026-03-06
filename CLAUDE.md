# Insight — Product & Engineering Guide

## Product Overview

Insight helps consultants go from "I want to research topic X" to "I have a defensible, sourced position with a publishable draft" in days instead of weeks. It builds a knowledge graph that captures every source, every claim, every relationship — and makes the landscape visible.

**Product vision:** [design/product-vision.md](design/product-vision.md)

**Product Sponsor:** The user. Sets direction, approves scope, makes priority decisions.
**Product Manager / Engineering:** Claude Code. Manages roadmap, writes specs, implements, tests, reports status.

---

## Architecture (v2)

Four components connected through a central knowledge graph:

```
Collector → Knowledge Graph (KuzuDB) → Presenter (static site)
                    ↑↓
                 Analyzer
```

**Detailed architecture:** [design/v2-architecture.md](design/v2-architecture.md)

### Components

| Component | Purpose | Status |
|-----------|---------|--------|
| **Knowledge Graph** | KuzuDB-backed central store. All data lives here. | Schema implemented, migration done |
| **Collector** | Discovery (find sources) + Extraction (fetch & parse into graph) | Spec written, code drafted |
| **Analyzer** | Segmentation, claim alignment, critique, synthesis | Design only |
| **Presenter** | Static site with graph explorer, JSON export | Design only |

### The Traceability Chain

Every insight traces back to a specific location in a specific source:

```
Source → ContentBlock → Segment → Claim → Finding → Recommendation
```

Every arrow is a typed edge in the graph.

---

## Project Structure

```
insight/                   # Python package (v2)
├── graph.py               # Knowledge graph interface (KuzuDB)
├── collector/             # Discovery + extraction
│   ├── web.py             # Web page extractor
│   ├── youtube.py         # YouTube transcript extractor
│   └── cli.py             # CLI entry point
├── analyzer/              # (future) Segmentation, alignment, critique
└── exporter/              # (future) Graph → JSON for website

tests/
├── unit/                  # Fast, no network, mocked inputs
├── integration/           # Full pipeline tests (marked, skipped by default)
└── fixtures/              # Sample HTML, transcripts, etc.

design/
├── v2-architecture.md     # Architecture overview
├── collector.md           # Component design (intent, rationale)
├── knowledge-graph.md     # Component design
├── analyzer.md            # Component design
├── presenter.md           # Component design
├── specs/                 # Detailed specifications
│   ├── graph-schema.md    # Node/edge types, Python API, acceptance criteria
│   └── collector.md       # Extractors, discovery, CLI, acceptance criteria
└── decisions/             # Architecture Decision Records (ADRs)

scripts/                   # v1 pipeline scripts (will be archived)
knowledge-base/            # v1 research data (being migrated to graph)
docs/                      # Static site (v1, will be rebuilt)
data/                      # Graph database files (gitignored)
```

---

## Development Process

### Workflow

```
Design doc → Spec (with acceptance criteria) → Tests → Code → Tests pass → Review
```

- **No code without a spec.** Every module has a spec in `design/specs/` with interface definitions, data contracts, behavior descriptions, and acceptance criteria.
- **Acceptance criteria become tests.** The spec's AC section maps directly to test cases.
- **Tests before or alongside code.** Not after.

### Spec Format

Each spec in `design/specs/` follows this structure:
1. **Overview** — what the module does
2. **Interface** — function signatures, CLI commands
3. **Data Contracts** — input/output schemas
4. **Behavior** — what happens, edge cases, error handling
5. **Acceptance Criteria** — testable conditions (AC-XX format)
6. **Test Plan** — which test files cover which ACs

### Decisions

Architecture decisions are recorded in `design/decisions/` as ADRs (Architecture Decision Records). Each captures context, options considered, decision, and consequences.

### Testing

- **Unit tests** (`tests/unit/`): Fast, no network. Mocked inputs. Run with `pytest`.
- **Integration tests** (`tests/integration/`): Full pipeline. Marked `@pytest.mark.integration`, skipped by default. Run with `pytest -m integration`.
- **Fixtures** (`tests/fixtures/`): Sample data for offline testing.
- **Framework:** pytest with pytest-cov.
- **Run:** `pytest` (unit only) or `pytest -m integration` (integration only) or `pytest --run-all` (everything).

### Status Reporting

Use `/status` to get current project status including:
- Milestone progress (what's done, what's next)
- Open issues and blockers
- Test coverage status
- Backlog overview

---

## Key Conventions

### Code

- Python 3.9+ compatible (use `from __future__ import annotations`)
- Package: `insight/` with submodules per component
- Dependencies in `pyproject.toml`
- No code without reading existing code first
- Follow existing patterns in the codebase

### Naming

- Topic slugs: lowercase, hyphens (e.g., `ea-for-ai`)
- Source IDs: `{topic}:source-{NNN}` (zero-padded)
- Block IDs: `{source_id}:block-{NNN}`
- Extraction IDs: `{block_id}:visual`

### Graph

- KuzuDB database at `data/insight.db` (gitignored)
- All graph access through `insight.graph.InsightGraph`
- Metadata fields store JSON as strings (KuzuDB has no native JSON type)
- Content hash: SHA-256 of concatenated text content

### Writing Style

All generated text follows objectivity guidelines:
- Report findings, do not judge them
- No sarcasm, snark, or loaded language
- Attribute positions to sources ("three sources argue X")
- Let data speak — scores and evidence over strong language

---

## Research Phases

The research methodology from v1 carries forward conceptually, but the implementation changes from file-based to graph-based:

| Phase | What happens | v2 component |
|-------|-------------|--------------|
| 0 — Data Gathering | Collect sources from web, documents, video | Collector |
| 1 — Data Analysis | Segment, align claims, critical analysis | Analyzer |
| 2 — Insight Refinement | Discussion, synthesis | Analyzer |
| 3 — Conclusions | Recommendations, thought leadership angles | Analyzer |

---

## Current Milestone Status

### Milestone 1 — Graph Foundation
- [x] KuzuDB selected and installed
- [x] Graph schema implemented (Source, ContentBlock, VisualExtraction nodes; CONTAINS, EXTRACTED_FROM edges)
- [x] Python API implemented (`insight.graph.InsightGraph`)
- [x] v1 migration script built and run (56 sources, 892 blocks for EA for AI)
- [x] Graph schema spec written (`design/specs/graph-schema.md`)
- [ ] Unit tests for graph module
- [ ] Tests pass

### Milestone 2 — Collector
- [x] Collector spec written (`design/specs/collector.md`)
- [x] Web extractor drafted (`insight/collector/web.py`)
- [x] YouTube extractor drafted (`insight/collector/youtube.py`)
- [x] CLI drafted (`insight/collector/cli.py`)
- [ ] Discovery module (URL normalization, registry check)
- [ ] Unit tests (web extraction, YouTube parsing, discovery)
- [ ] Integration tests
- [ ] Tests pass

### Milestone 3 — Analyzer
- [ ] Design doc expansion
- [ ] Spec
- [ ] Implementation

### Milestone 4 — Presenter
- [ ] Design doc expansion
- [ ] Spec
- [ ] Implementation

### Milestone 5 — Cleanup & CI
- [ ] GitHub Actions
- [ ] Archive v1 pipeline
- [ ] Update documentation

---

## Backlog

Tracked in [backlog.md](backlog.md). GitHub Issues will be used for tracking once the planning phase stabilizes.

---

## Available Commands

### Research Pipeline
- `/research <topic>` — Discover and collect sources (uses Collector)
- `/ingest <topic>` — Process uploaded documents
- `/analyze <topic>` — Run analysis pipeline
- `/discuss <topic>` — Interactive discussion of findings
- `/synthesize <topic>` — Generate synthesis document
- `/conclude <topic>` — Generate recommendations and angles
- `/baseline <topic>` — Establish common-knowledge baseline

### Utility
- `/kb <query>` — Search the knowledge base
- `/status` — Project and pipeline status dashboard
- `/session-writeup` — Document session outcomes

---

## Available MCP Servers

- **Playwright**: Use for JavaScript-heavy pages that WebFetch can't render
- **GitHub**: Use for repository operations when `gh` CLI is insufficient
