# /discuss <topic>

Engage in an interactive, structured discussion about the critical insights for a topic. Walk through findings one by one, challenge assumptions, gather the user's perspective, and document the discussion for further use.

## Arguments

$ARGUMENTS — The topic slug to discuss insights for (e.g., "EA for AI")

## Prerequisites

The topic must have critical analysis files at `knowledge-base/topics/{topic}/extractions/critical-analysis-part*.yaml`. Run `/analyze <topic>` first and ensure the critical analysis has been generated.

## Process

1. **Load the critical analysis data**:
   - Read all `critical-analysis-part*.yaml` files from `knowledge-base/topics/{topic}/extractions/`
   - Read the `claim-alignment.yaml` for context on supporting claims
   - Count total findings and group by verdict

2. **Present overview to the user**:
   - Show total findings, verdict distribution, average scores
   - Ask the user how they want to proceed:
     - **All findings** in order (full walkthrough)
     - **Genuine insights only** (focus on the best stuff)
     - **Platitudes and obvious** (focus on what to challenge/discard)
     - **Most actionable** (sorted by actionability score, descending)

3. **Walk through findings one at a time**:
   For each finding, present a structured discussion block:

   **a) Present the finding:**
   - Show: statement, verdict, scores (platitude/actionability/novelty)
   - Show: the critique (skeptic view) and the bottom line
   - Show: key action items from `what_to_actually_do`

   **b) Ask the user 2-3 targeted questions using AskUserQuestion:**

   Choose questions contextually based on the verdict:

   For **platitudes** and **important_but_obvious**:
   - "Does this match your experience? Is this truly obvious in your org, or is there a gap between 'everyone knows this' and 'everyone does this'?"
   - "What's the real blocker? Why isn't this being done if everyone agrees it should be?"
   - "Is there a specific 'how' that would make this actionable for your audience?"

   For **partial_insights**:
   - "What resonates here? What part of this is genuinely useful vs. noise?"
   - "Can you think of a concrete example from your experience that illustrates this?"
   - "What additional angle or nuance would strengthen this insight?"

   For **genuine_insights**:
   - "Is this as novel as the analysis suggests? Have you seen this applied in practice?"
   - "Who in your network would find this most surprising or valuable?"
   - "What would be the strongest way to present this in a thought leadership piece?"

   For **contradictions**:
   - "Which side of this tension do you lean towards? Why?"
   - "Have you seen organisations navigate this tension? What worked?"
   - "Is there a third option the sources missed?"

   **c) Record the user's response** — save it as structured discussion notes

   **d) Ask a closing question for each finding:**
   - Verdict: "Based on our discussion, should we: Keep as-is / Upgrade / Downgrade / Flag for deeper research / Discard?"
   - Any specific topics or questions flagged for further investigation

4. **After each finding, ask:** "Continue to next finding, or pause here?"
   - If pausing, save progress so discussion can be resumed with `/discuss {topic}` later

5. **Save discussion output**:
   After completing the walkthrough (or when the user pauses), write structured output to:
   `knowledge-base/topics/{topic}/discussion/discussion-{date}.yaml`

   Structure:
   ```yaml
   # Interactive Discussion Notes
   topic: "{topic}"
   date: "2026-02-14"
   findings_discussed: 5
   findings_total: 27

   discussions:
     - finding_id: cc-001
       statement: "..."
       original_verdict: important_but_obvious
       user_assessment: "keep" | "upgrade" | "downgrade" | "research_further" | "discard"
       user_notes: |
         What the user said about this finding...
       key_quotes: []
       further_research:
         - topic: "How organisations actually implement AI governance step-by-step"
           priority: high
           context: "Sources identify the what but not the how"
       revised_verdict: null  # or new verdict if user changed it

   research_topics:
     - topic: "..."
       priority: high | medium | low
       source_finding: cc-001
       context: "Why this needs further research"

   summary:
     total_discussed: 5
     kept: 3
     upgraded: 1
     downgraded: 0
     flagged_for_research: 2
     discarded: 0
     key_themes: []
   ```

6. **At the end of the session**, present a summary:
   - Findings discussed and verdicts
   - Research topics identified (these become inputs for `/research`)
   - Suggested next steps

## Important Guidelines

- **Be conversational, not robotic.** This is a discussion, not a survey. React to the user's input, build on their points, challenge them constructively.
- **Don't just accept "yes" or "no."** If the user gives a short answer, probe deeper: "Can you give me a specific example?" or "What makes you say that?"
- **Capture specific quotes and examples.** If the user shares a concrete experience or opinion, record it — this is gold for content creation.
- **Flag research topics actively.** Whenever a gap or question emerges that the current sources don't answer, note it as a research topic.
- **Keep momentum.** Don't spend more than 3-4 exchanges per finding unless the user wants to go deeper. The goal is to cover ground, not get stuck.
- **The user's perspective is the most valuable input.** They bring real-world experience the sources lack. Treat their input as a primary source.

## Example

```
/discuss EA for AI
```

Walks through the critical insights on Enterprise Architecture for AI, gathering the user's perspective on each finding and documenting the discussion for content creation.
