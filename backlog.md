# Site Backlog

**Issue tracking has moved to [Beads](https://github.com/steveyegge/beads)** — an AI-native, git-native issue tracker that lives in the private repo (`.beads/issues.jsonl`).

## Viewing Issues

```bash
# In ~/Code/insight-private
bd list                          # All issues
bd list -l frontend              # Frontend issues only
bd list -l backend               # Backend issues only
bd list --status open -p 1       # Open P1 issues
bd show Research\ Agent-1        # Issue details
```

## Current Issues (snapshot)

### P1 — High Priority
- **Research Agent-1** [frontend] Build review page UI (dev-only) — Spec: `site/specs/review-page.md`
- **Research Agent-2** [backend] Build /refine command for review feedback

### P2 — Medium Priority
- **Research Agent-3** [backend] Extract publication dates from sources
- **Research Agent-4** [backend] Integrate review patterns into extraction pipeline
- **Research Agent-5** [backend] Fix block boundary quality (3.8% failure rate)
- **Research Agent-6** [backend] Remove cross-source duplicate blocks (4.4% rate)
- **Research Agent-7** [frontend] Conclusions page empty despite data
- **Research Agent-8** [both] Visuals: broken image paths
- **Research Agent-9** [frontend] Source detail drawer/panel
- **Research Agent-10** [frontend] Add image placeholders on Visuals page
- **Research Agent-11** [frontend] Consistent empty states across pages

### P3 — Low Priority
- **Research Agent-12** [frontend] Findings category pills wrap on small screens
- **Research Agent-13** [frontend] Graph detail panel shows raw IDs
- **Research Agent-14** [frontend] No loading states on pages
- **Research Agent-15** [frontend] Graph zoom controls
- **Research Agent-16** [frontend] Duplicate pill styles across components

### P4 — Backlog
- **Research Agent-17** [frontend] Graph component is monolithic

### Done
- **Research Agent-18** [backend] Review data exporter (export_review)
