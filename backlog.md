# Backlog

Structured backlog for the Research Agent project. Organised as **Epics > Features > Items**. Individual task execution is tracked in Claude Code sessions; this file tracks planning and progress at the item level.

## Status Key

- **planned** — Defined, not yet started
- **in-progress** — Actively being worked on
- **done** — Completed
- **blocked** — Waiting on a dependency or decision

---

## Epic 1: Increase Usage of Scripts

Reduce manual effort and improve reproducibility by automating repetitive pipeline steps with standalone scripts.

### Feature 1.1: Data Scraping Scripts

Automate the collection and structuring of web-based source material.

| # | Item | Status | Notes |
|---|------|--------|-------|
| 1.1.1 | Create a script that automatically scrapes data from websites and converts them into a structured source note format | done | `scripts/scrape-sources.py` — uses ScrapeGraphAI + Playwright + Claude to extract structured data from URLs in `source-input.yaml` and generate `sources/source-NNN.md` files. |

---
