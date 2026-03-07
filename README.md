# Insight

A knowledge graph-powered research analysis system that collects and analyzes content from a variety of sources.

**Status:** v2 redesign in progress — [product vision](design/product-vision.md) | [architecture](design/v2-architecture.md)

## What It Does

Insight helps consultants go from "I want to research topic X" to "I have a defensible, sourced position with a publishable draft" in days instead of weeks.

## Research Process

### Phase 0 — Collect

Gather sources from the web, PDFs, YouTube, and documents. Each source is stored in the knowledge graph with full metadata.

```
/research <topic>    # Discover and collect web sources
/ingest <topic>      # Ingest uploaded documents (PDFs, reports)
```

### Phase 1 — Extract & Align

Break each source into **extracts** — the smallest meaningful unit of information (a sentence, a short paragraph, or a heading). Each extract is classified by type:

| Type | What it means |
|------|--------------|
| **assertion** | A statement making a claim or position |
| **statistic** | A quantitative data point |
| **evidence** | Data-backed support for a position |
| **recommendation** | An actionable suggestion |
| **definition** | A term or concept being defined |
| **example** | A case study or illustration |
| **methodology** | How research was conducted |
| **context** | Background information |

Then align assertions across sources to identify **claims** — positions that multiple sources independently support:

- **Canonical claims**: 2+ sources agree on the same point
- **Unique claims**: Only one source makes this point, but it's significant
- **Contradictions**: Sources disagree

```
/analyze <topic>     # Extract, classify, and align claims
```

### Phase 2 — Findings

Group related claims into **findings** — higher-level patterns and themes that emerge from the evidence. Each finding is backed by specific claims, which trace back to specific extracts in specific sources.

```
/synthesize <topic>  # Generate findings from claims
```

### Phase 3 — Conclusions

Generate recommendations and thought leadership angles based on findings.

```
/conclude <topic>    # Recommendations and angles
```

### The Traceability Chain

Every insight traces back to a specific location in a specific source:

```
Source → Extract → Claim → Finding → Recommendation
(web/pdf/   (atomic unit,    (cross-source    (thematic      (actionable
 youtube)    classified)      alignment)       pattern)        output)
```

## How It Works

```
Collector → Knowledge Graph (KuzuDB) → Presenter (static site)
                    ↑↓
                 Analyzer
```

- **Collector** — discovers and extracts sources from web, YouTube, PDF, documents
- **Knowledge Graph** — KuzuDB-backed store of sources, extracts, claims, and relationships
- **Analyzer** — classifies extracts, aligns claims, identifies gaps and contradictions
- **Presenter** — interactive graph explorer, deep dive inspector, and source dashboard

## Quick Start

### Prerequisites

- Python 3.9+
- [Claude Code](https://claude.com/claude-code) CLI installed

### Setup

```bash
pip install -r requirements.txt
playwright install chromium
```

### Commands

```
/research <topic>    # Discover and collect sources from the web
/ingest <topic>      # Ingest uploaded documents (PDFs, reports)
/analyze <topic>     # Extract, classify, align claims, critical analysis
/synthesize <topic>  # Generate findings from claims
/conclude <topic>    # Generate recommendations and thought leadership angles
/baseline <topic>    # Evaluate claim novelty against common knowledge
/kb <query>          # Search the knowledge base
/status              # Project and pipeline status
```

### Collector CLI

```bash
# Collect web sources
python -m insight.collector extract --urls "https://..." --topic my-topic

# Collect YouTube videos
python -m insight.collector extract --urls "https://youtube.com/watch?v=..." --topic my-topic

# Check what's already collected
python -m insight.collector status --topic my-topic

# Check URLs against registry (what's new?)
python -m insight.collector discover --urls "https://..." --topic my-topic
```

## Project Structure

```
insight/                   # Python package (v2)
├── graph.py               # Knowledge graph interface (KuzuDB)
├── collector/             # Source discovery + extraction
│   ├── web.py             # Web page extractor
│   ├── youtube.py         # YouTube transcript extractor
│   └── cli.py             # CLI entry point
└── exporter/              # Graph → JSON for static site

design/                    # Product and engineering docs
├── product-vision.md      # Product vision, goals, release plan
├── v2-architecture.md     # Architecture overview
├── specs/                 # Detailed specifications
├── decisions/             # Architecture Decision Records
└── ways-of-working.md     # Development process

tests/                     # Unit and integration tests
knowledge-base/            # Research data (topics, sources, analysis)
site/                      # SvelteKit source for static site
docs/                      # Built static site for GitHub Pages
scripts/                   # Build and utility scripts
```

## Documentation

- [Product Vision](design/product-vision.md) — goals, user jobs, release plan
- [Release Plan](design/release-plan.md) — MVP → MLP → Full with milestones, scope, and dependencies
- [Architecture](design/v2-architecture.md) — components, tech decisions, milestones
- [Ways of Working](design/ways-of-working.md) — development process, roles, lessons learned
- [Decisions](design/decisions/) — architecture decision records
- [Backlog](backlog.md) — work items and priorities
