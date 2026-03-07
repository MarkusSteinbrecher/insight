# /conclude <topic>

Draw conclusions from completed research — actionability analysis, recommendations, and thought leadership angles.

## Arguments

$ARGUMENTS — The topic slug to conclude (e.g., "ea-for-ai")

## Prerequisites

The topic must have findings in the knowledge graph. Run `/synthesize <topic>` first if needed.

## Process

### Step 1 — Actionability Analysis

1. Load findings and their linked claims from the graph
2. For each finding, assess:
   - **Actionability**: high / medium / low
   - **Barriers**: organizational, technical, cultural, economic
   - **Missing for action**: what's absent for a practitioner to act

### Step 2 — Recommendations

1. Generate 8-12 prioritized recommendations:
   - Title, description, priority, effort, dependencies, related findings
   - Sequence by dependency and effort
2. Write recommendations

### Step 3 — Thought Leadership Angles

1. Structure positions from synthesis into:
   - Title, position statement, novelty rationale, supporting claims, suggested format
2. Apply objectivity standards throughout

## Output

Write conclusions to `knowledge-base/sessions/conclusions-{topic}-{date}.yaml`

## Writing Guidelines

- Report findings, do not judge them
- No sarcasm, snark, or condescension
- Attribute positions to sources
- Recommendations should be concrete and actionable

## Example

```
/conclude ea-for-ai
```
