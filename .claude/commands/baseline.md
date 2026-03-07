# /baseline <topic>

Establish the research scope for a topic: define the question, set search keywords, discover sources, and track what has been found. This is the starting point for any new research topic and the re-entry point for finding additional sources.

## Arguments

$ARGUMENTS — The topic slug (e.g., "ea-for-ai")

## Modes

This command has two modes, selected automatically:

1. **Create** — If `knowledge-base/baselines/{slug}.yaml` does not exist, create it
2. **Discover** — If the baseline exists, run discovery using its keywords

---

## Mode 1: Create Baseline

1. Check if `knowledge-base/baselines/{slug}.yaml` exists
2. If not, ask the user using AskUserQuestion:
   - "What is the research question for this topic?"
   - Suggest a default based on the topic slug
3. Ask for search keywords using AskUserQuestion:
   - "What keywords should we search for? (I'll suggest some based on the question)"
   - Suggest 5-8 keywords derived from the research question
   - Include both web and YouTube keyword suggestions
4. Create the baseline YAML file:

   ```yaml
   topic: {slug}
   title: {derived from slug or user input}
   question: {user's research question}
   keywords:
     - "keyword one"
     - "keyword two"
   youtube_keywords:
     - "youtube keyword one"
   sources: []
   runs: []
   ```

5. Save to `knowledge-base/baselines/{slug}.yaml` using:
   ```python
   from insight.collector.baseline import save_baseline, Baseline
   ```
6. Immediately proceed to Mode 2 (Discover) to run the first discovery round.

---

## Mode 2: Discover

1. Load the baseline:
   ```python
   from insight.collector.baseline import load_baseline, save_baseline, record_run, add_sources, SourceRecord
   ```

2. Show current state:
   ```
   Baseline: {title}
   Question: {question}
   Keywords: {count} web, {count} YouTube
   Sources tracked: {count} ({collected} collected, {pending} pending)
   Runs: {count} (last: {date})
   ```

3. **Search using each keyword** — launch parallel research agents (up to 3) using the Agent tool:

   For each keyword in `keywords`:
   - Use WebSearch to find relevant URLs
   - Collect all candidate URLs

   For each keyword in `youtube_keywords`:
   - Use WebSearch with `site:youtube.com {keyword}` to find YouTube content
   - Collect candidate video URLs

4. **Deduplicate candidates** — combine all found URLs, remove duplicates

5. **Check against source registry** — for each candidate URL:
   - Check against baseline's tracked sources (`baseline.source_urls`)
   - Check against graph registry using:
     ```python
     from insight.collector.discovery import check_urls
     ```
   - Classify each URL as new or already tracked

6. **Present results to the user**:
   ```
   Discovery results:
     Searched: {N} keywords
     Found: {M} candidate URLs
     New: {K} not yet tracked
     Already tracked: {J}

   New sources found:
     + https://example.com/article-title
     + https://youtube.com/watch?v=...
     ...

   Already tracked:
     - https://example.com/existing
     ...
   ```

7. **Ask the user** using AskUserQuestion:
   - "Which sources should we collect?" with options:
     - "All new sources" — extract all
     - "Let me pick" — present the list for selection
     - "None for now" — just track them in baseline

8. **Update the baseline**:
   - Add new URLs as source records (with empty `source_id` until extracted)
   - Record the run (date, keywords used, found/new/existing counts)
   - Save the baseline file

9. **Extract selected sources** (if user chose to collect):
   - Run extraction for each selected URL:
     ```bash
     python3 -m insight.collector extract --urls {urls} --topic {slug}
     ```
   - The extract command will auto-update the baseline with source IDs and titles

10. **Summary**:
    ```
    Discovery complete:
      New sources tracked: {N}
      Sources extracted: {M}
      Total sources for topic: {T}

    Next steps:
      /baseline {slug}    — run another discovery round
      /research {slug}    — targeted deep research
      /analyze {slug}     — analyze collected sources
    ```

---

## Important Notes

- The baseline is the **scope definition** for a topic — what we're looking for and what we've found
- Keywords are human-edited in the YAML file — the user can add/remove keywords between runs
- Sources are tracked in the baseline AND in the graph — the baseline is the discovery ledger, the graph is the content store
- Each discovery run is recorded with stats so the user can see discovery progress over time
- The baseline does NOT contain analysis (themes, claims, evaluations) — that belongs to `/analyze`
- If the user wants to add sources manually (not via search), they can use `python -m insight.collector extract --urls ... --topic {slug}` directly

## Example

```
# New topic — creates baseline, runs first discovery
/baseline platform-engineering

# Existing topic — runs another discovery round with stored keywords
/baseline ea-for-ai
```
