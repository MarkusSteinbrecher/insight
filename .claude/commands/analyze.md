# /analyze <topic>

Analyze collected sources for a topic — extract insights, patterns, contradictions, and gaps.

## Arguments

$ARGUMENTS — The topic slug to analyze (e.g., "ai-agents-enterprise")

## Prerequisites

The topic must exist at `knowledge-base/topics/{topic}/` with sources in the `sources/` directory. Run `/research <topic>` first if needed.

## Process

1. **Verify topic exists**:
   - Check that `knowledge-base/topics/{topic}/` exists
   - Check that `sources/` contains at least one source file
   - Read `_index.md` to get current status

2. **Read all sources**:
   - List all source files in `knowledge-base/topics/{topic}/sources/`
   - Split them into two roughly equal groups for parallel analysis

3. **Launch parallel analyst agents**:

   **Agent 1 — Claims and Evidence**:
   - Focus: Extract specific claims, statistics, data points, and evidence
   - Assess evidence strength and cross-reference between sources
   - Write insights of type: evidence, trend

   **Agent 2 — Patterns and Gaps**:
   - Focus: Identify recurring themes, contradictions, and knowledge gaps
   - Look for what sources agree/disagree on and what's missing
   - Write insights of type: pattern, contradiction, gap

4. **Consolidate results**:
   - Create `insights/` directory if it doesn't exist
   - Update `_index.md`: set status to "analyzed", update insight_count and updated date
   - Present key findings to the user:
     - Top patterns identified
     - Notable contradictions
     - Knowledge gaps worth investigating
     - Strongest evidence and data points
     - Most interesting angles for thought leadership

5. **Suggest next steps**:
   - "Run `/synthesize {topic}` to create a comprehensive synthesis."
   - "Run `/research {topic}` again to go deeper on any gaps identified."

## Example

```
/analyze ai-agents-enterprise
```

Reads all sources, extracts insights, and presents key findings organized by type.
