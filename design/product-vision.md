# Insight — Product Vision

---

## The Problem

Consultants creating thought leadership need to understand what's already been said on a topic — by whom, where firms agree or disagree, and where the gaps are. Today this is manual work: searching the web, reading reports, watching talks, taking notes, trying to synthesize across dozens of sources. It takes weeks and the result is fragile — claims are hard to trace back to sources, coverage gaps are invisible, and starting a new topic means starting from scratch.

## The Vision

Insight helps consultants go from "I want to research topic X" to "I have a defensible, sourced position with a publishable draft" in days instead of weeks. It does this by building a **knowledge graph** that captures every source, every claim, every relationship — and makes the landscape visible.

## Target User

**Management and technology consultants** who produce thought leadership content: blog posts, points of view, whitepapers, presentations. They research topics in technology and AI, need to understand the existing landscape, and create content that adds a new perspective.

## The Jobs To Be Done

### Job 1 — Landscape Scan
> "Show me what's out there on this topic."

Collect sources from web articles, PDF reports, YouTube talks, and documents. Track what's been gathered, from which firms, how recent. Flag duplicates. The consultant should have 20-50 relevant sources structured in one session.

### Job 2 — Extract & Structure
> "Break these sources down so I don't have to read every page."

Automatically segment each source into claims, statistics, evidence, recommendations. Every piece of content traceable to its exact location (page, timestamp, heading). The consultant reviews and refines — they don't transcribe.

### Job 3 — Cross-Source Intelligence
> "Where do they agree? Where do they disagree? What's missing?"

Align claims across sources. Show consensus, contradictions, and unique positions. Compare against common knowledge to identify what's genuinely novel. Surface gaps — what nobody is talking about yet. **This is the core value.**

### Job 4 — Source Tracking & Coverage
> "What do I have? What's been processed? Where did this claim come from?"

Full awareness of the source landscape: by firm, by type, by date, by processing status. Coverage analysis — "I have nothing from academia" or "all my sources are from 2025." Every claim traces back to its source with a citation-ready reference.

### Job 5 — Content Creation
> "Help me write something that adds a new perspective."

Generate drafts backed by the knowledge graph. Identify thought leadership angles — contrarian positions, underserved topics, novel connections. Every claim in the output links to its evidence chain. The consultant edits and refines, not writes from scratch.

### Job 6 — Cumulative Knowledge
> "I shouldn't start from scratch every time."

The knowledge graph grows across topics and over time. Sources collected for one topic are available when researching adjacent topics. The consultant's knowledge compounds.

## Product Goals

| # | Goal | Success Metric |
|---|------|----------------|
| G1 | Fast landscape scan | 20-50 sources collected and structured in one session |
| G2 | Automated extraction | Every source broken into traceable claims without manual reading |
| G3 | Cross-source intelligence | Consensus, contradictions, gaps, and novelty surfaced automatically |
| G4 | Source tracking | Full provenance — any claim traceable to source, page, paragraph |
| G5 | Content-ready output | Draft content backed by evidence chains |
| G6 | Cumulative knowledge | Knowledge compounds across topics and time |

## Product Principles

1. **Traceability over convenience.** Every insight must trace back to a specific location in a specific source. If we can't cite it, we can't claim it.

2. **Structure over summaries.** Don't summarize — decompose. Claims, statistics, evidence as discrete, queryable units. Summaries lose information; structure preserves it.

3. **Show the landscape, don't hide it.** The consultant should see where sources agree, disagree, and stay silent. Transparency builds confidence in the output.

4. **Compound, don't restart.** Every source collected, every claim extracted, every insight refined adds to the knowledge graph permanently. New research builds on existing knowledge.

5. **Assist, don't replace.** The system handles collection, extraction, and cross-referencing. The consultant makes the judgment calls — what's important, what angle to take, what to publish.

## Architecture Summary

Four components connected through a central knowledge graph:

```
Collector → Knowledge Graph (KuzuDB) → Presenter
                    ↑↓
                 Analyzer
```

- **Collector** — gets sources in (web, PDF, YouTube, documents). Discovery + extraction.
- **Knowledge Graph** — central store. Sources, content blocks, segments, claims, findings, recommendations. All relationships as typed edges.
- **Analyzer** — the intelligence. Segmentation, claim alignment, critique, synthesis. Powered by Claude API.
- **Presenter** — makes the graph visible. Interactive explorer, source dashboard, content views. Static site.

Detailed architecture: [v2-architecture.md](v2-architecture.md)

## Priorities

Based on the value chain:

1. **Collector + Graph** — without sources in the graph, nothing else works
2. **Analyzer** — cross-source intelligence is the core differentiator
3. **Presenter** — consultants need to see and explore the landscape
4. **Content pipeline** — highest value but depends on 1-3 being solid

## Release Plan

### MVP — "I can research a topic end-to-end"

The minimum product that delivers value to one consultant on one topic.

**What it does:**
- Collect sources from web and YouTube into the knowledge graph
- Track all sources (what I have, from whom, what type, what's been processed)
- Segment and extract claims from sources
- Align claims across sources (consensus, contradictions, unique positions)
- View the source landscape and claim map in a basic web interface
- Every claim traceable back to its source

**What it doesn't do yet:**
- PDF/document ingestion (manual workaround: paste content)
- Content generation (consultant writes manually, using the graph as reference)
- Multi-user support
- Polished graph explorer

**Goals covered:** G1 (landscape scan), G2 (extraction), G3 (partial — alignment without gap analysis), G4 (source tracking)

**Components needed:**
- Collector: web + YouTube extractors, discovery, source registry
- Knowledge Graph: full schema (sources through claims)
- Analyzer: segmentation + claim alignment
- Presenter: basic source list + claim view (minimal UI)

---

### MLP — "I'd recommend this to a colleague"

The Minimum Lovable Product — good enough that a consultant would choose to use it over their manual process.

**What it adds over MVP:**
- PDF and document ingestion (Docling + visual extraction)
- Gap analysis — what's missing from the landscape, what nobody is saying
- Baseline comparison — what's common knowledge vs genuinely novel
- Interactive graph explorer — click a finding, see its evidence chain, explore by concept
- Source coverage dashboard — by firm, by type, by date, with gap indicators
- Content drafting support — generate draft blog/POV from graph with citations

**Goals covered:** G1-G5 fully, G6 (partial — single topic compounds but cross-topic not yet)

**Components needed:**
- Collector: + PDF extractor, visual extraction
- Analyzer: + critical analysis, baseline comparison, gap detection, synthesis
- Presenter: graph explorer, source dashboard, content views

---

### Full Product — "This changes how I work"

The complete vision where knowledge compounds and content flows from research.

**What it adds over MLP:**
- Cross-topic knowledge — sources and claims shared across related topics
- Content pipeline — ideation, drafting, validation, publishing workflow
- Multiple content formats — blog, POV, presentation, LinkedIn, executive brief
- Collaborative features — shared knowledge base, team source contributions
- API for integration — feed insights into other tools

**Goals covered:** G1-G6 fully

---

### Component Scope per Release

#### Collector

| Capability | MVP | MLP | Full |
|---|---|---|---|
| Web page extraction (Playwright + BS4) | x | x | x |
| YouTube transcript extraction | x | x | x |
| Source registry (dedup, URL tracking) | x | x | x |
| Source metadata (title, author, type, date, URL) | x | x | x |
| Discovery — check candidates against registry | x | x | x |
| CLI (`python -m insight.collector`) | x | x | x |
| PDF extraction (Docling, page-level anchoring) | | x | x |
| Visual extraction (figures, charts → Claude vision) | | x | x |
| PowerPoint extraction | | x | x |
| Word doc extraction | | x | x |
| Parallel collection (concurrent scraping) | | x | x |
| Audio/podcast transcription (Whisper) | | | x |
| Authentication support (paywalled sources) | | | x |

#### Knowledge Graph

| Capability | MVP | MLP | Full |
|---|---|---|---|
| Source nodes (metadata, content hash) | x | x | x |
| ContentBlock nodes (positioned, typed) | x | x | x |
| CONTAINS edges (Source → ContentBlock) | x | x | x |
| Segment nodes (typed: claim, statistic, etc.) | x | x | x |
| SEGMENTED_FROM edges (Segment → ContentBlock) | x | x | x |
| Claim nodes (aligned across sources) | x | x | x |
| SUPPORTS / CONTRADICTS edges | x | x | x |
| Python API (CRUD, queries) | x | x | x |
| JSON export (basic — source list, claim list) | x | x | x |
| VisualExtraction nodes | | x | x |
| Finding nodes (synthesized patterns) | | x | x |
| Recommendation nodes | | x | x |
| Concept nodes (topics, themes) | | x | x |
| RELATES_TO, BASED_ON edges | | x | x |
| Graph traversal queries (evidence chains) | | x | x |
| JSON export (rich — graph explorer data) | | x | x |
| Cross-topic edges | | | x |
| Schema versioning / migrations | | | x |

#### Analyzer

| Capability | MVP | MLP | Full |
|---|---|---|---|
| Segmentation (ContentBlock → typed Segments) | x | x | x |
| Claim alignment (consensus, contradictions, unique) | x | x | x |
| Incremental analysis (per-source, not batch) | x | x | x |
| Critical analysis (assess claim strength, value) | | x | x |
| Baseline comparison (novel vs common knowledge) | | x | x |
| Gap detection (what's missing from landscape) | | x | x |
| Synthesis generation (narrative from graph) | | x | x |
| Interactive discussion (human-in-the-loop) | | x | x |
| Findings extraction (patterns across claims) | | x | x |
| Recommendations generation | | x | x |
| Thought leadership angles | | x | x |
| Cross-topic pattern detection | | | x |

#### Presenter

| Capability | MVP | MLP | Full |
|---|---|---|---|
| Source list with metadata and processing status | x | x | x |
| Claim list with source attribution | x | x | x |
| Basic filtering and sorting | x | x | x |
| Static site (GitHub Pages deployable) | x | x | x |
| Source coverage dashboard (by firm, type, date) | | x | x |
| Interactive graph explorer (click, traverse) | | x | x |
| Evidence chain drill-down (claim → segments → source) | | x | x |
| Findings view with supporting evidence | | x | x |
| Content drafting view | | x | x |
| Gap visualization | | x | x |
| Cross-topic navigation | | | x |
| Collaboration views | | | x |

---

### Release Sequence

```
MVP                          MLP                         Full Product
───                          ───                         ────────────
Collector (web + YouTube)    + PDF + visual extraction   + audio, auth
Graph (sources → claims)     + findings, concepts        + cross-topic
Analyzer (segment + align)   + critique, gaps, synthesis + cross-topic patterns
Presenter (basic lists)      + graph explorer, dashboard + collaboration
                             + content drafting
```

Each release is independently useful. A consultant gets value from MVP — they don't have to wait for the full product.

---

## What This Is Not

- **Not a search engine.** It doesn't find answers — it maps the landscape of positions and evidence.
- **Not a summarizer.** It doesn't compress — it decomposes and cross-references.
- **Not a writing tool.** It doesn't generate polished content — it provides the structured evidence and angles that make writing faster and more rigorous.
