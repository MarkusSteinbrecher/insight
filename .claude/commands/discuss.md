# /discuss <topic>

Interactive discussion of findings for a topic. Walk through findings one by one, challenge assumptions, gather the user's perspective.

## Arguments

$ARGUMENTS — The topic slug to discuss (e.g., "ea-for-ai")

## Prerequisites

The topic must have findings in the knowledge graph. Run `/synthesize <topic>` first if needed.

## Process

1. **Load findings from the graph**:
   ```python
   from insight.graph import InsightGraph
   g = InsightGraph()
   findings = g.get_findings_by_topic(topic)
   ```

2. **Present overview**: Show total findings and categories. Ask the user how to proceed:
   - **All findings** in order
   - **Selective** (user picks which to discuss)

3. **Walk through findings one at a time**:

   **a) Present the finding**: title, description, category, linked claims with evidence

   **b) Ask targeted questions using AskUserQuestion**:
   - "Does this match your experience?"
   - "What resonates here? What's most useful?"
   - "Can you think of a concrete example?"
   - "What would make this actionable for your audience?"

   For **contradictions**:
   - "Which side do you lean towards? Why?"
   - "Have you seen organizations navigate this tension?"

   **c) Record the user's response**

   **d) Closing question**: "Keep as-is / Upgrade / Downgrade / Flag for research / Discard?"

4. **After each finding**: "Continue to next, or pause here?"

5. **Save discussion output** to `knowledge-base/sessions/discussion-{topic}-{date}.yaml`

## Guidelines

- Be conversational, not robotic
- Probe deeper on short answers
- Capture specific quotes and examples — gold for content creation
- Flag research topics when gaps emerge
- The user's perspective is a primary source

## Example

```
/discuss ea-for-ai
```
