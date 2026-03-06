# Insight

A knowledge graph-powered research analysis system for consultants creating thought leadership content.

**Status:** v2 redesign in progress — [product vision](design/product-vision.md) | [architecture](design/v2-architecture.md)

## What It Does

Insight helps consultants go from "I want to research topic X" to "I have a defensible, sourced position with a publishable draft" in days instead of weeks.

1. **Collect** — Gather sources from the web, PDFs, YouTube, and documents. Track what you have, from which firms, what's been processed.
2. **Extract** — Break each source into structured claims, statistics, and evidence — without reading every page. Everything traceable to its exact location.
3. **Analyze** — Align claims across sources. See where they agree, disagree, and what nobody is talking about yet.
4. **Present** — Explore the knowledge graph interactively. Drill from a finding down to the source paragraph that supports it.
5. **Create** — Produce drafts backed by evidence chains. Every claim linked to its sources.

## How It Works

```
Collector → Knowledge Graph (KuzuDB) → Presenter (static site)
                    ↑↓
                 Analyzer
```

- **Collector** — discovers and extracts sources from web, YouTube, PDF, documents
- **Knowledge Graph** — KuzuDB-backed store of sources, claims, findings, and relationships
- **Analyzer** — segments sources, aligns claims, identifies gaps and contradictions (Claude API)
- **Presenter** — interactive graph explorer and source dashboard

### The Traceability Chain

Every insight traces back to a specific location in a specific source:

```
Source → Content Block → Segment → Claim → Finding → Recommendation
         (page/timestamp/   (typed unit    (cross-source   (synthesized   (actionable
          heading)           of meaning)    alignment)       pattern)       output)
```

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
/analyze <topic>     # Segment sources, align claims, critical analysis
/discuss <topic>     # Interactive discussion of findings
/synthesize <topic>  # Create synthesis document
/conclude <topic>    # Generate recommendations and thought leadership angles
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
└── collector/             # Source discovery + extraction
    ├── web.py             # Web page extractor
    ├── youtube.py         # YouTube transcript extractor
    └── cli.py             # CLI entry point

design/                    # Product and engineering docs
├── product-vision.md      # Product vision, goals, release plan
├── v2-architecture.md     # Architecture overview
├── specs/                 # Detailed specifications
├── decisions/             # Architecture Decision Records
└── ways-of-working.md     # Development process

tests/                     # Unit and integration tests
knowledge-base/            # Research data (topics, sources, analysis)
docs/                      # Static site for GitHub Pages
scripts/                   # Build and utility scripts
```

## Release Plan

| Release | What it delivers |
|---------|-----------------|
| **MVP** | Collect from web + YouTube, segment and align claims, basic source/claim viewer. End-to-end research on one topic. |
| **MLP** | + PDF ingestion, gap analysis, interactive graph explorer, source coverage dashboard, content drafting. |
| **Full** | + Cross-topic knowledge, content pipeline, collaboration, API. |

## Documentation

- [Product Vision](design/product-vision.md) — goals, user jobs, release plan
- [Release Plan](design/release-plan.md) — MVP → MLP → Full with milestones, scope, and dependencies
- [Architecture](design/v2-architecture.md) — components, tech decisions, milestones
- [Ways of Working](design/ways-of-working.md) — development process, roles, lessons learned
- [Decisions](design/decisions/) — architecture decision records
- [Backlog](backlog.md) — work items and priorities
