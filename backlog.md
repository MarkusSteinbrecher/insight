# Backlog

Checklist of improvement items for the Research Agent project. Done items are moved to the bottom.

---

## Open

### Reduce Agent Token Usage

- [ ] **1.3.1** Create `merge-critical-analysis.py` — concatenate batched critical analysis parts into unified YAML, recalculate counts
- [ ] **1.3.2** Update `/analyze` command to batch step 1.3 explicitly (15-20 claims per batch), write temp files, then merge
- [ ] **1.4.1** Update `/analyze` command to generate cross-source analysis section-by-section (by theme cluster from step 1.2) rather than all-at-once
- [ ] **1.5.1** Create `prepare-baseline-eval.py` — extract claim IDs and summary text from claim-alignment.yaml into a condensed evaluation input file
- [ ] **1.6.1** Update `/synthesize` command to generate each section in a separate focused prompt with only the relevant subset of data

---

## Done

- [x] **1.1.1** Create `segment-source.py` — deterministic splitting + async Claude API classification
- [x] **1.1.2** Update `/analyze` command to call `segment-source.py` for step 1.1
- [x] **1.2.1** Create `prepare-alignment.py` — TF-IDF pre-clustering of claim-relevant segments (~51% input reduction)
- [x] **1.2.2** Update `/analyze` command to use pre-clustered input for step 1.2
- [x] **2.1.1** Create `scrape-sources.py` — Playwright + BeautifulSoup web scraping into structured source notes
- [x] **2.1.2** Integrate `scrape-sources.py` into the `/research` command flow
- [x] **2.2.1** Create `check-progress.py` — pipeline status scanner with human-readable and JSON output
- [x] **2.3.1** Integrate `audit-claims.py` into `/analyze` as post-step validation
- [x] **2.4.1** Add `build-usecases-data.py` to `build.sh`
- [x] **3.1.1** Rewrite `/analyze` command with actual 4-step Phase 1 pipeline
- [x] **3.1.2** Add resume support to `/analyze` (reads completed_steps, runs next step)
- [x] **3.2.1** Scope `document-analyst.md` agent to ingestion only
- [x] **3.3.1** Update CLAUDE.md site configuration with correct data file paths
- [x] **3.3.2** Add findings.yaml to topic directory structure docs
- [x] **3.3.3** Add use-case-inventory.yaml and build scripts to CLAUDE.md
- [x] **4.1.1** Remove orphaned Hugo submodule (`.git/modules/site/`)
- [x] **4.1.2** Remove Hugo entries from `.gitignore`
- [x] **4.2.1** Remove empty `knowledge-base/connections/` and all graph.md references
- [x] **4.3.1** Consolidate 4 critical-analysis part files into single `critical-analysis.yaml`
- [x] **4.4.1** Move `fix-claims.py` to `scripts/archive/`
