# /analyze <topic>

Run the analysis pipeline for a topic — build extracts from content blocks, then link extracts to claims.

## Arguments

$ARGUMENTS — The topic slug to analyze (e.g., "ea-for-ai")

## Prerequisites

The topic must have sources in the knowledge graph. Run `/research <topic>` or `/ingest <topic>` first.

## Process

### 1. Check current state

```python
from insight.graph import InsightGraph
g = InsightGraph()
sources = g.count_sources(topic=topic)
extracts = g.count_extracts_by_topic(topic) if hasattr(g, 'count_extracts_by_topic') else 0
claims = g.count_claims(topic=topic)
```

Determine which step to run:
- No extracts → **Step 1: Build Extracts**
- Extracts but no claims → **Step 2: Claim Alignment**
- Claims exist → **Step 3: Critical Analysis** (or report complete)

### 2. Step 1 — Build Extracts

Run the extract builder to create atomic Extract nodes from ContentBlocks:

```
python3 scripts/build-extracts.py {topic}
```

This splits long prose into atomic units, classifies each by type (assertion, statistic, evidence, recommendation, etc.), and stores as Extract nodes linked to Sources.

### 3. Step 2 — Claim Alignment

Analyze all extracts across sources. Identify:
- **Canonical claims** (`cc-NNN`): 2+ sources agree on a position
- **Unique claims** (`uc-NNN`): single-source positions
- **Contradictions** (`ct-NNN`): sources disagree

Store claims in the graph with EXTRACT_SUPPORTS edges.

Run audit after alignment:
```
python3 scripts/audit-claims.py {topic}
```

### 4. Step 3 — Critical Analysis

For each canonical claim, assess:
- Critique: strengths, gaps, what would strengthen it
- Practical value: what a practitioner can do with this
- Action steps: 2-3 concrete actions
- Bottom line: one-sentence assessment

Store assessments on Claim nodes in the graph.

### 5. Present results and suggest next steps

- After Step 1: "Run `/analyze {topic}` again to proceed to claim alignment."
- After Step 2: "Run `/analyze {topic}` again for critical analysis."
- After Step 3: "Analysis complete. Run `/synthesize {topic}` to create findings."

## Example

```
/analyze ea-for-ai
```
