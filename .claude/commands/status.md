# /status

Report project status to the product sponsor. Covers engineering progress, research pipeline, and next actions.

## Arguments

No arguments required.

## Process

### 1. Engineering Status

Read `CLAUDE.md` milestone status section and report:
- Which milestones are complete, in progress, or not started
- For in-progress milestones: what's done, what's remaining
- Any blockers or open decisions needing sponsor input

### 2. Test Status

Run `pytest --tb=no -q 2>&1` to check test status:
- How many tests pass / fail / skipped
- Note any failing tests

### 3. Knowledge Graph Status

If the graph database exists (`data/insight.db`), run:
```python
from insight.graph import InsightGraph
g = InsightGraph()
# Report: total sources, total blocks, sources per topic
```

### 4. Research Pipeline Status

Scan `knowledge-base/topics/` for each topic:
- Read `_index.md` for phase, completed_steps, source_count
- Report current phase and next step

### 5. Backlog Summary

Read `backlog.md` and report:
- Count of open items per category
- Next priority items

### 6. Present Dashboard

```
# Project Status — {date}

## Engineering
| Milestone | Status | Progress |
|-----------|--------|----------|
| 1. Graph Foundation | In progress | 5/7 tasks done |
| 2. Collector | In progress | Spec done, tests pending |
| ... | | |

## Tests
- Unit: X pass, Y fail
- Integration: not yet running

## Knowledge Graph
- Topics: N
- Sources: N (web: X, youtube: Y, pdf: Z)
- Content blocks: N

## Research Topics
| Topic | Phase | Sources | Next step |
|-------|-------|---------|-----------|
| ea-for-ai | 3 (complete) | 56 | Content creation |

## Blockers / Decisions Needed
- {Any items needing sponsor input}

## Next Actions
- {Prioritized list of what to work on next}
```
