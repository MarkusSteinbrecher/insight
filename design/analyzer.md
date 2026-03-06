# Component: Analyzer

Parent: [v2 Architecture](v2-architecture.md) | Spec: [Analyzer](specs/analyzer.md)
Status: **MVP complete** (graph helpers implemented, 17/17 tests passing)

---

## Purpose

Graph helper functions for the analysis pipeline. Claude Code performs all intelligence (segmentation, claim alignment, etc.) during command execution. The Python module handles graph read/write operations only — no Claude API calls.

## How It Works

1. Claude Code reads content blocks from the graph via query helpers
2. Claude Code performs analysis (segmentation, classification, alignment)
3. Claude Code writes results to the graph via write helpers

## Key Modules

- **`insight/analyzer/segmentation.py`** — get unsegmented sources, get source content, write segments, composition stats
- **`insight/analyzer/alignment.py`** — get claim-relevant segments, write claims with segment links, write contradictions, alignment stats
- **`insight/analyzer/queries.py`** — topic summary (counts of all node types, segmented vs unsegmented)

## MVP Scope

- Segmentation: ContentBlock → Segment nodes (10-type taxonomy)
- Claim alignment: Segment → Claim nodes (canonical, unique, contradiction)

## MLP Additions (future)

- Critical analysis helpers
- Baseline comparison helpers
- Gap detection queries
- Synthesis generation support
