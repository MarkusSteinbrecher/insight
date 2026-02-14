# /synthesize <topic>

Create a comprehensive synthesis document for a researched and analyzed topic.

## Arguments

$ARGUMENTS — The topic slug to synthesize (e.g., "ai-agents-enterprise")

## Prerequisites

The topic must exist at `knowledge-base/topics/{topic}/` with both sources and insights. Run `/research` and `/analyze` first if needed.

## Process

1. **Verify topic is ready**:
   - Check that `knowledge-base/topics/{topic}/` exists
   - Check that `insights/` contains insight files
   - Read `_index.md` to confirm status is at least "analyzed"

2. **Read all materials**:
   - Read `_index.md` for topic context
   - Read all source files in `sources/` for raw material
   - Read all insight files in `insights/` for analyzed findings

3. **Generate synthesis document**:
   Write `knowledge-base/topics/{topic}/synthesis.md` with the following sections:

   ```yaml
   ---
   title: "Synthesis: {Topic Title}"
   date: YYYY-MM-DD
   sources_analyzed: N
   insights_extracted: N
   ---
   ```

   **Executive Summary** (2-3 paragraphs):
   Overview of the topic landscape — what's happening, why it matters, and the key takeaway.

   **Key Themes** (3-5 themes):
   Major themes with supporting evidence from insights and sources. Each theme gets a subsection.

   **Consensus Areas**:
   Points of broad agreement across sources. What does the field largely agree on?

   **Active Debates**:
   Areas of genuine disagreement or tension. Present both sides fairly.

   **Knowledge Gaps**:
   Important questions that current sources don't adequately address. Opportunities for original research or perspective.

   **Thought Leadership Angles** (3-5 angles):
   The most promising angles for original content. For each angle:
   - The core argument or insight
   - Why it's non-obvious or contrarian
   - Supporting evidence available
   - Suggested content type (blog, POV, presentation)

   **Bibliography**:
   Numbered list of all sources with full attribution.

4. **Update cross-topic connections**:
   - Read `knowledge-base/connections/graph.md`
   - Check if this topic relates to any existing topics
   - Add connections with shared themes, tension points, and synthesis opportunities

5. **Update topic status**:
   - Set `_index.md` status to "synthesized"
   - Update the `updated` date

6. **Present results**:
   - Summary of the synthesis
   - Highlight the 2-3 strongest thought leadership angles
   - Suggest next steps: "Use these angles with `/draft` (future) or write content manually"

## Example

```
/synthesize ai-agents-enterprise
```

Creates a comprehensive synthesis document and identifies the best angles for thought leadership content.
