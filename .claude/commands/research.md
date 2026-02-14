# /research <topic>

Research a topic by gathering sources from the web across multiple angles.

## Arguments

$ARGUMENTS — The topic to research (e.g., "AI agents in the enterprise", "platform engineering trends")

## Process

1. **Create topic directory**:
   - Generate a slug from the topic: lowercase, hyphens, no special characters
   - Create `knowledge-base/topics/{slug}/` with subdirectories `documents/`, `sources/`, and `insights/`
   - Create `_index.md` with metadata (status: researching, today's date, auto-generated tags from the taxonomy)
   - Note: users can also drop PDFs and other files into `documents/` and run `/ingest {slug}` to process them

2. **Launch parallel research agents**:
   Launch 3 web-researcher agents in parallel, each with a different angle:

   **Agent 1 — Recent Developments**:
   - Focus: News, announcements, and developments from the last 12 months
   - Search terms: topic + "2024" or "2025", recent news, latest developments

   **Agent 2 — Foundational Perspectives**:
   - Focus: Academic papers, foundational concepts, established frameworks
   - Search terms: topic + research, papers, frameworks, foundations

   **Agent 3 — Industry & Practitioner Insights**:
   - Focus: Industry reports, case studies, practitioner experience
   - Search terms: topic + enterprise, adoption, case study, report, best practices

3. **Consolidate results**:
   - Update `_index.md` with source count
   - Present a summary to the user:
     - Total sources gathered
     - Key themes emerging across all angles
     - Most notable findings
     - Gaps in coverage

4. **Ask the user**:
   - "Would you like to go deeper on any sub-topic or angle?"
   - "Ready to analyze? Run `/analyze {slug}` to extract insights."

## Example

```
/research AI agents in enterprise software
```

Creates `knowledge-base/topics/ai-agents-enterprise/` and gathers ~24-36 sources across three research angles.
