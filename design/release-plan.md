# Release Plan

How we get from here to a product. Each release is independently useful.

Parent: [Product Vision](product-vision.md) | [Architecture](v2-architecture.md) | [Backlog](../backlog.md)

---

## Release Overview

| Release | Theme | Goal | Status |
|---------|-------|------|--------|
| **MVP** | "I can research a topic end-to-end" | Collect → segment → align → view for one topic | In progress |
| **MLP** | "I'd recommend this to a colleague" | + PDFs, gap analysis, graph explorer, content drafting | Not started |
| **Full** | "This changes how I work" | + Cross-topic, content pipeline, collaboration | Not started |

---

## MVP — End-to-End Research

**User story:** A consultant collects 20-50 web and YouTube sources on a topic, the system extracts and aligns claims automatically, and they can view the source landscape and claim map in a browser.

**Success criteria:**
- Collect a web source into the graph with one command
- Collect a YouTube video into the graph with one command
- Source registry prevents duplicate collection
- Sources are segmented into typed units (claim, statistic, evidence, etc.)
- Claims are aligned across sources (consensus, contradictions, unique)
- Every claim traces back to its source location
- Basic web UI shows source list and claim list with attribution
- Full pipeline validated on a real topic (EA for AI)

### MVP Milestones

| # | Milestone | Scope | Status |
|---|-----------|-------|--------|
| M1 | Graph Foundation | KuzuDB schema, Python API, CRUD, queries, migration | **Done** (50/50 tests) |
| M2 | Collector | Web + YouTube extractors, discovery, source registry, CLI | In progress |
| M3 | Analyzer (core) | Segmentation (ContentBlock → Segment), claim alignment (Segment → Claim) | Not started |
| M4 | Presenter (basic) | Graph → JSON export, static site with source list + claim list | Not started |
| M5 | Integration | Wire commands, GitHub Actions, documentation, end-to-end validation | Not started |

### MVP Component Scope

| Component | What's in | What's out |
|-----------|-----------|------------|
| **Collector** | Web extraction (Playwright + BS4), YouTube transcripts, URL normalization, source registry, CLI | PDF, PowerPoint, Word, parallel collection |
| **Graph** | Source, ContentBlock, VisualExtraction, Segment, Claim nodes. CONTAINS, EXTRACTED_FROM, SEGMENTED_FROM, SUPPORTS, CONTRADICTS edges | Finding, Recommendation, Concept nodes. RELATES_TO, BASED_ON edges. Rich traversal queries |
| **Analyzer** | Segmentation (10-type taxonomy), claim alignment (canonical, unique, contradiction) | Critical analysis, baseline comparison, gap detection, synthesis, discussion |
| **Presenter** | Source list with metadata, claim list with source attribution, basic filtering, static site | Graph explorer, coverage dashboard, evidence drill-down, content views |

### MVP Dependencies

```
M1 Graph Foundation ──→ M2 Collector ──→ M3 Analyzer ──→ M4 Presenter ──→ M5 Integration
     (done)              (in progress)    (needs M1+M2)   (needs M1+M3)    (needs all)
```

M2 and M3 both depend on M1 (done). M3 could start in parallel with M2 since its graph operations are already tested. M4 needs M3 output to render claims. M5 wires everything together.

---

## MLP — Minimum Lovable Product

**User story:** A consultant chooses this over their manual research process. They can ingest PDFs, see what's genuinely novel vs common knowledge, explore the evidence graph interactively, and get a content draft with citations.

**What it adds over MVP:**

| Capability | Component | Why it matters |
|------------|-----------|----------------|
| PDF + document ingestion | Collector | Most consulting research is in PDFs and reports |
| Visual extraction (charts, diagrams) | Collector | Key data lives in figures, not just text |
| Critical analysis (claim strength, value) | Analyzer | Not all claims are equal — practitioners need to know what to act on |
| Baseline comparison (novel vs common) | Analyzer | Separates genuine insights from things everyone already knows |
| Gap detection | Analyzer | The most valuable insight is often what nobody is saying |
| Synthesis generation | Analyzer | Narrative that weaves claims into a coherent story |
| Interactive discussion | Analyzer | Human-in-the-loop refinement of findings |
| Findings + recommendations | Analyzer + Graph | Synthesized patterns and actionable output |
| Interactive graph explorer | Presenter | Click a finding, see its evidence chain, explore by concept |
| Source coverage dashboard | Presenter | See gaps: "nothing from academia", "all sources from 2025" |
| Content drafting | Presenter | Generate draft blog/POV from graph with citations |

**MLP Milestones** (to be detailed when MVP is complete):

| # | Milestone | Scope |
|---|-----------|-------|
| M6 | Document Ingestion | PDF extractor (Docling), visual extraction (Claude vision), document CLI |
| M7 | Extended Graph | Finding, Recommendation, Concept nodes. Evidence chain traversal |
| M8 | Deep Analysis | Critical analysis, baseline comparison, gap detection, synthesis |
| M9 | Graph Explorer | Interactive D3/Svelte graph, evidence drill-down, coverage dashboard |
| M10 | Content Pipeline | Draft generation from graph, citation management, format templates |

---

## Full Product — Compound Knowledge

**User story:** A consultant's knowledge compounds. Research on one topic feeds into adjacent topics. Content flows from research through drafting to publication. Teams share knowledge bases.

**What it adds over MLP:**

| Capability | Component |
|------------|-----------|
| Cross-topic knowledge graph | Graph |
| Content pipeline (ideate → draft → validate → publish) | Analyzer + Presenter |
| Multiple content formats (blog, POV, presentation, LinkedIn, brief) | Presenter |
| Collaborative features (shared KB, team contributions) | All |
| API for integration with other tools | All |
| Audio/podcast transcription | Collector |

Full product milestones will be defined when MLP is complete.

---

## What We Already Have (v1)

Before the v2 redesign, we built a working v1 pipeline with:

- Web scraping and source collection
- Per-source segmentation (10-type taxonomy)
- Cross-source claim alignment
- Critical analysis and baseline evaluation
- Synthesis generation
- Static site with dashboard, insights, and sources pages
- Two completed research topics: EA for AI (56 sources), AI in Project Management (32 sources)

**v1 limitations that motivated v2:**
- YAML files don't scale — grep-based traceability breaks at 50+ sources
- Batch processing — can't add one source without re-processing everything
- No graph structure — cross-referencing requires string matching across files
- Build pipeline is 8 separate scripts with fragile coupling

**v1 → v2 transition:**
- v1 code remains in `scripts/` (build scripts still work with existing data)
- v1 research data is preserved locally in `knowledge-base/topics/`
- 56 EA for AI sources have been migrated into the v2 graph (892 content blocks)
- v2 components gradually replace v1 scripts as each milestone completes
- v1 static site continues to serve until v2 Presenter (M4) is ready

---

## Risk & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| KuzuDB limitations (reserved words, query quirks) | Development friction | Document workarounds, prefix column names, maintain a KuzuDB lessons file |
| Claude API costs for analysis at scale | MLP cost per topic | Incremental analysis (per-source, not batch), caching, prompt optimization |
| PDF extraction quality varies | MLP data quality | Multiple extraction strategies, human review step, confidence scoring |
| Graph explorer complexity | MLP development time | Start with simpler list views, add interactivity incrementally |
| Scope creep into MLP during MVP | MVP delay | Strict MVP component scope table above — if it's not listed, it waits |
