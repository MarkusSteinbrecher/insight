# Backlog

Structured backlog for the Research Agent project. Organised as **Epics > Features > Items**. Individual task execution is tracked in Claude Code sessions; this file tracks planning and progress at the item level.

## Status Key

- **planned** — Defined, not yet started
- **in-progress** — Actively being worked on
- **done** — Completed
- **blocked** — Waiting on a dependency or decision

---

## Epic 1: Reduce Agent Token Usage

Agents stall when output tokens hit their limit. The biggest offenders are in Phase 1 (`/analyze`), where raw segmentation, claim alignment, and critical analysis produce large YAML outputs within a single agent context window. Moving deterministic or structured-output work into Python scripts (with direct API calls where LLM reasoning is needed) eliminates the orchestration overhead and allows parallel processing.

### Feature 1.1: Script-Based Raw Segmentation (Step 1.1)

Raw segmentation is the single largest token consumer. Each source produces 200-600 lines of YAML. Running 30-50 sources through an agent serially accumulates context until the agent stalls. The schema is rigid (10 types, fixed YAML format, sentence-level splitting), making this highly scriptable.

| # | Item | Status | Notes |
|---|------|--------|-------|
| 1.1.1 | Create `segment-source.py` — split source text into segments deterministically (sentence splitting, bullet detection, heading detection), classify each segment via a focused API call, write raw YAML | planned | Process sources in parallel with `asyncio`. One API call per source with just the segment text + classification taxonomy. Removes the biggest token sink from agent context. |
| 1.1.2 | Update `/analyze` command to call `segment-source.py` for step 1.1 instead of doing segmentation inline | planned | Depends on 1.1.1. |

### Feature 1.2: Pre-Processing for Claim Alignment (Step 1.2)

Step 1.2 currently loads ALL raw YAML files into context at once. EA for AI has 44,243 lines of raw YAML (~110K tokens input) before the agent even starts reasoning. Pre-filtering and clustering reduces this dramatically.

| # | Item | Status | Notes |
|---|------|--------|-------|
| 1.2.1 | Create `prepare-alignment.py` — extract only `claim`-type segments from all raw files, pre-cluster by keyword similarity (TF-IDF or word overlap), output condensed candidate clusters | planned | Reduces LLM input from ~110K tokens to ~20-30K tokens. |
| 1.2.2 | Update `/analyze` command to use pre-clustered input for step 1.2 | planned | Depends on 1.2.1. The LLM then reviews and refines clusters rather than searching through everything. |

### Feature 1.3: Batched Critical Analysis (Step 1.3)

EA for AI's critical-analysis.yaml is 5,038 lines (single file). The AI-in-PM topic had to be split into 4 part files (164-175 lines each) — a symptom of hitting output limits. Explicit batching and a merge script prevents this.

| # | Item | Status | Notes |
|---|------|--------|-------|
| 1.3.1 | Create `merge-critical-analysis.py` — concatenate batched critical analysis parts into unified YAML, recalculate counts | planned | Simple deterministic concat + validation. |
| 1.3.2 | Update `/analyze` command to batch step 1.3 explicitly (15-20 claims per batch), write temp files, then merge | planned | Depends on 1.3.1. |

### Feature 1.4: Batched Cross-Source Analysis (Step 1.4)

Step 1.4 loads all raw files (~110K tokens) plus claim-alignment.yaml (~31K tokens) into a single context for narrative comparison.

| # | Item | Status | Notes |
|---|------|--------|-------|
| 1.4.1 | Update `/analyze` command to generate cross-source analysis section-by-section (by theme cluster from step 1.2) rather than all-at-once | planned | Can reuse the cluster structure from `prepare-alignment.py`. |

### Feature 1.5: Baseline Evaluation Input Reduction

The baseline evaluation reads the full claim-alignment.yaml to evaluate each claim. A script can extract just the claim IDs + summaries for a ~60% input reduction.

| # | Item | Status | Notes |
|---|------|--------|-------|
| 1.5.1 | Create `prepare-baseline-eval.py` — extract claim IDs and summary text from claim-alignment.yaml into a condensed evaluation input file | planned | Batching already exists in `/baseline` (20-30 claims per batch) — this further reduces per-batch context. |

### Feature 1.6: Section-by-Section Synthesis

`/synthesize` loads all sources + insights + claim alignment + critical analysis (~80K+ input tokens) into a single context.

| # | Item | Status | Notes |
|---|------|--------|-------|
| 1.6.1 | Update `/synthesize` command to generate each section (Key Themes, Consensus Areas, Active Debates, Knowledge Gaps, etc.) in a separate focused prompt with only the relevant subset of data | planned | Each section gets its own context window. A final pass stitches sections together. |

---

## Epic 2: Increase Usage of Scripts

Reduce manual effort and improve reproducibility by automating repetitive pipeline steps with standalone scripts.

### Feature 2.1: Data Scraping Scripts

Automate the collection and structuring of web-based source material.

| # | Item | Status | Notes |
|---|------|--------|-------|
| 2.1.1 | Create a script that automatically scrapes data from websites and converts them into a structured source note format | done | `scripts/scrape-sources.py` — uses Playwright + BeautifulSoup to extract structured data from URLs in `source-input.yaml` and generate `sources/source-NNN.md` files. |
| 2.1.2 | Integrate `scrape-sources.py` into the `/research` command flow | planned | Currently the `/research` command uses web-researcher agents with WebFetch. The scrape script handles JS rendering and metadata extraction better. Could replace or supplement the agent for URL-based source gathering. |

### Feature 2.2: Pipeline Status Script

Each command currently scans directories to verify topic state. A shared status script eliminates this repetitive work.

| # | Item | Status | Notes |
|---|------|--------|-------|
| 2.2.1 | Create `check-progress.py` — scan topic directory, determine which pipeline steps are complete based on file existence and `_index.md` frontmatter, output status JSON | planned | Replaces the "verify topic exists" boilerplate in every command. Can be called from commands or used standalone. |

### Feature 2.3: Validation Integration

`audit-claims.py` performs quality checks (seg-tbd detection, AI relevance scoring, coherence checks) but is not wired into the pipeline.

| # | Item | Status | Notes |
|---|------|--------|-------|
| 2.3.1 | Integrate `audit-claims.py` into the `/analyze` command as a post-step validation | planned | Run automatically after step 1.2 (claim alignment) to catch seg-tbd placeholders and low-relevance sources before proceeding to critical analysis. |

### Feature 2.4: Build Pipeline Completeness

| # | Item | Status | Notes |
|---|------|--------|-------|
| 2.4.1 | Add `build-usecases-data.py` to `build.sh` | planned | Script exists, site JS expects `use-cases.json`, but the build doesn't run it. Only AI-in-PM topic currently has `use-case-inventory.yaml`. |

---

---
