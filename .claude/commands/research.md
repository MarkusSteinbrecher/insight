# /research <topic>

Research a topic by discovering and collecting sources from the web into the knowledge graph.

## Arguments

$ARGUMENTS — The topic to research (e.g., "ea-for-ai", "platform-engineering")

## Mode Detection

1. Check the knowledge graph for existing sources: `python3 -c "from insight.graph import InsightGraph; g = InsightGraph(); print(g.count_sources(topic='$ARGUMENTS'))"`
2. **If no sources** → run **Initial Research** (Mode A)
3. **If sources exist** → run **Additional Sources** (Mode B)

---

## Mode A — Initial Research (new topic)

### Process

1. **Search for sources** across three angles in parallel:
   - **Recent Developments**: topic + "2025" or "2026", recent news, latest developments
   - **Foundational Perspectives**: topic + research, papers, frameworks, foundations
   - **Industry & Practitioner Insights**: topic + enterprise, adoption, case study, report

2. **For each promising source**, use the Collector to add it to the graph:
   ```python
   from insight.collector.web import extract_web
   from insight.graph import InsightGraph
   g = InsightGraph()
   extract_web(url, topic_slug, g)
   ```

3. **For PDF documents**, place them in `docs/documents/` and use:
   ```python
   from insight.collector.pdf import extract_pdf
   extract_pdf(pdf_path, topic_slug, g, source_id=None)
   ```

4. **Present summary**: total sources, key themes, gaps in coverage

5. **Ask the user**: "Ready to analyze? Run `/analyze {slug}`"

---

## Mode B — Additional Sources (existing topic)

### Process

1. Show current source coverage from the graph (count, types, authors)
2. Ask: "What angles or criteria should I search for?"
3. Search with targeted queries, present candidates
4. For each accepted source, collect via the appropriate extractor
5. Report what was added, suggest next steps

---

## Examples

```
/research ea-for-ai
/research platform-engineering
```
