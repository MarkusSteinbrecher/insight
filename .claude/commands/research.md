# /research <topic>

Research a topic by gathering sources from the web. Operates in two modes depending on whether the topic already exists.

## Arguments

$ARGUMENTS — The topic to research (e.g., "AI agents in the enterprise", "platform engineering trends")

## Mode Detection

1. Look up the topic in `knowledge-base/topics/` (match by slug or folder name)
2. **If topic does not exist** → run **Initial Research** (Mode A)
3. **If topic exists and has sources** → run **Additional Sources** (Mode B)

---

## Mode A — Initial Research (new topic)

For topics that don't exist yet. Creates the topic and gathers a broad initial set of sources.

### Process

1. **Create topic directory**:
   - Generate a slug from the topic: lowercase, hyphens, no special characters
   - Create `knowledge-base/topics/{slug}/` with subdirectories `documents/`, `sources/`, `raw/`, `extractions/`, and `discussion/`
   - Create `_index.md` with metadata (status: phase-0, today's date, auto-generated tags)
   - Create empty `source-input.yaml` from template
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
   - Run `python3 scripts/build-overview.py` to generate `sources/_overview.md`
   - Present a summary to the user:
     - Total sources gathered
     - Key themes emerging across all angles
     - Most notable findings
     - Gaps in coverage

4. **Ask the user**:
   - "Would you like to go deeper on any sub-topic or angle?"
   - "Ready to analyze? Run `/analyze {slug}` to extract insights."

---

## Mode B — Additional Sources (existing topic)

For topics that already have sources. Processes queued entries and searches for targeted additions.

### Process

1. **Check source-input.yaml for pending entries**:
   - Read `knowledge-base/topics/{slug}/source-input.yaml`
   - If there are entries with `status` missing or set to `queued`, process them:
     - Run `python3 scripts/scrape-sources.py "{slug}"` to fetch all pending URLs via Playwright and generate source notes automatically (no LLM needed — extracts metadata from HTML tags, full text from page content)
     - The script updates `source-input.yaml` entries with `status: gathered` and the assigned `source` ID
     - For `document` entries (PDFs, etc.): note them for `/ingest` processing
   - If the scrape script fails on specific URLs (JS-heavy pages, paywalled content), fall back to using WebFetch for those URLs individually

2. **Ask for search criteria**:
   - Show the user current source coverage (count, types, key institutions)
   - Ask: "What angles or criteria should I search for?"
   - Accept criteria such as:
     - Specific institutions or authors (e.g., "Find BCG or Accenture reports")
     - Time ranges (e.g., "Papers from 2025 or later")
     - Sub-topics or keywords (e.g., "Agent governance frameworks")
     - Gap filling (e.g., "More practitioner case studies")

3. **Search with targeted queries**:
   - Construct web searches from the user's criteria combined with the topic
   - Present candidate sources with: title, URL, author, and relevance rationale
   - Let the user pick which to add

4. **Create source notes**:
   - For each accepted source, create `sources/source-NNN.md` (next sequential number)
   - Run `python3 scripts/build-overview.py` to regenerate `sources/_overview.md`

5. **Summary**:
   - Report what was added
   - Suggest next steps: `/analyze {slug}` if new sources need processing through the pipeline

---

## Examples

```
# New topic — runs Mode A (3-angle initial research)
/research AI agents in enterprise software

# Existing topic — runs Mode B (criteria-based additions)
/research EA for AI
```
