# /conclude <topic>

Draw conclusions from completed research — Phase 3 of the research pipeline.

## Arguments

$ARGUMENTS — The topic slug to conclude (e.g., "ea-for-ai")

## Prerequisites

The topic must exist at `knowledge-base/topics/{topic}/` with completed Phase 2 (synthesis). Run `/synthesize` first if needed.

## Resume Support

This command reads `_index.md` frontmatter (`completed_steps`) and resumes from the next incomplete step:

- **3.1** — Reader perspective (actionability analysis per finding)
- **3.2** — Recommendations (prioritized, concrete actions)
- **3.3** — Thought leadership angles (structured positions with supporting claims)

If all 3.x steps are complete, report that and suggest content creation.

## Process

### Step 3.1 — Reader Perspective (Actionability Analysis)

1. Read `findings.yaml`, `synthesis.md`, and `extractions/critical-analysis.yaml`
2. For each finding, assess:
   - **Actionability**: high / medium / low — can a practitioner act on this within 6 months?
   - **Barriers**: what prevents adoption (organizational, technical, cultural, economic)?
   - **Missing for action**: what information or capability is absent for a practitioner to act?
3. Review and refine existing `practitioner` text in `findings.yaml` if needed
4. Write the `actionability` section of `extractions/conclusions.yaml`
5. Update `_index.md`: add "3.1" to `completed_steps`, set `current_step: "3.2"`

### Step 3.2 — Recommendations

1. Read `findings.yaml`, `synthesis.md` (especially Sections 4-6), and the step 3.1 actionability assessment
2. Generate 8-12 prioritized recommendations:
   - Each recommendation: title, description, priority (high/medium/low), effort (high/medium/low), dependencies, related findings
   - Sequence by dependency and effort — what must come first, what delivers quick wins
   - Draw from findings' practitioner implications and synthesis content roadmap
3. Write the `recommendations` section of `extractions/conclusions.yaml`
4. Update `_index.md`: add "3.2" to `completed_steps`, set `current_step: "3.3"`

### Step 3.3 — Thought Leadership Angles

1. Read `synthesis.md` Section 5 (existing thought leadership positions)
2. Read `extractions/claim-alignment.yaml` for supporting claim IDs
3. Structure each position into the YAML format:
   - Title, position statement, novelty rationale, supporting claims, suggested format
   - Apply the same objectivity standards used throughout the research
4. Write the `angles` section of `extractions/conclusions.yaml`
5. Update `_index.md`: add "3.3" to `completed_steps`, set phase to 3, status to "phase-3"

## Output Schema

```yaml
meta:
  topic: {topic-slug}
  target_audience: "..."
  generated: YYYY-MM-DD

actionability:
  - finding_id: finding-01
    actionability: high | medium | low
    barriers:
      - "..."
    missing_for_action: "..."

recommendations:
  - id: rec-01
    title: "..."
    description: "..."
    priority: high | medium | low
    effort: high | medium | low
    dependencies: [rec-XX]
    related_findings: [finding-01]

angles:
  - id: angle-01
    title: "..."
    position: "..."
    why_novel: "..."
    supporting_claims: [cc-XXX]
    suggested_format: "blog | pov | presentation | linkedin"
```

## Writing Guidelines

Follow the project's objectivity standards:
- Report findings, do not judge them
- No sarcasm, snark, or condescension
- Attribute positions to sources rather than asserting them as fact
- Let evidence and data speak — avoid loaded language
- Recommendations should be concrete and actionable, not generic advice

## Example

```
/conclude ea-for-ai
```

Generates or resumes Phase 3 conclusions for the EA for AI topic.
