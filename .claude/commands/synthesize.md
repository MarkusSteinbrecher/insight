# /synthesize <topic>

Group aligned claims into findings, classify each finding by category, and store in the knowledge graph.

## Arguments

$ARGUMENTS — The topic slug to synthesize (e.g., "ea-for-ai")

## Prerequisites

The topic must have completed claim alignment (step 1.2). Check `_index.md` for `completed_steps` including `"1.2"`.

## Process

### 1. Load claims

Read all canonical claims from the graph:

```python
import sys; sys.path.insert(0, '.')
from insight.graph import InsightGraph
g = InsightGraph()
claims = g.get_claims_by_topic("{topic}", category="canonical")
```

Also read `extractions/claim-alignment.yaml` for the full claim details including source segments, and `extractions/critical-analysis.yaml` for the critique and practical value assessments.

### 2. Group claims into findings

Review all canonical claims and group them into **findings** — higher-level thematic patterns that emerge from multiple related claims. A finding is NOT just a renamed claim; it synthesizes multiple claims into a coherent insight.

Guidelines:
- Each finding should group 2-6 related claims
- A claim can belong to at most one finding
- Not every claim needs to be in a finding — minor or isolated claims can remain standalone
- Each finding needs a clear, descriptive title (e.g., "EA frameworks lack AI-specific guidance")
- Each finding needs a description paragraph explaining the pattern and why it matters
- Aim for 8-15 findings total depending on the topic breadth

### 3. Classify each finding

Assign each finding a **category** — a domain label that groups findings at the highest level. Categories should emerge from the data, not be predefined. Examples for EA for AI might include:
- Governance & Risk
- People & Skills
- Architecture & Frameworks
- Technology & Infrastructure
- Strategy & Transformation
- Data & AI Operations

Guidelines:
- Use 4-8 categories total
- Categories should be meaningful to the target audience
- Each finding gets exactly one category
- Category names should be short (2-4 words)

### 4. Store findings in the graph

For each finding:

```python
g.add_finding(
    finding_id="{topic}:finding-{NNN}",
    topic="{topic}",
    title="Finding title",
    description="Description paragraph",
    category="Category Name",
)

# Link each claim to its finding
for claim_id in finding_claims:
    g.link_claim_to_finding(claim_id, finding_id)
```

### 5. Clear previous findings first

Before creating findings, clear any existing ones:

```python
g.conn.execute("""
    MATCH (f:Finding) WHERE f.topic = $topic DETACH DELETE f
""", parameters={"topic": "{topic}"})
```

### 6. Export and rebuild

After storing findings:

```python
from insight.exporter.export import export_all, export_graph
from insight.exporter.audit import export_audit

export_all(g, 'site/static/data', kb_path='knowledge-base')
export_graph('{topic}', g, 'site/static/data')
export_audit('{topic}', g, 'site/static/data', kb_path='knowledge-base')
g.close()
```

Then rebuild the site:
```bash
cd site && npm run build
```

### 7. Update topic status

Update `_index.md`:
- Add `"2.1"` to `completed_steps`
- Set `current_step: "2.2"`
- Update `finding_count` with the total

### 8. Present results

Show a summary table:

```
## Findings for {topic}

| # | Finding | Category | Claims |
|---|---------|----------|--------|
| 1 | EA frameworks lack AI-specific guidance | Architecture & Frameworks | cc-001, cc-003, cc-012 |
| 2 | ... | ... | ... |

Categories: {list categories with finding counts}
Unlinked claims: {list any canonical claims not assigned to a finding}
```

## Example

```
/synthesize ea-for-ai
```

Groups the 62 canonical claims into findings, classifies each by category, stores in graph, and exports data.
