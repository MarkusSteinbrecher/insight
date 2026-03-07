# /ingest <topic>

Process uploaded PDF documents into the knowledge graph.

## Arguments

$ARGUMENTS — The topic slug to ingest documents for (e.g., "ea-for-ai")

## Purpose

Many valuable sources are behind paywalls or only available as downloaded files. This command processes PDFs placed in `docs/documents/` into the knowledge graph.

## Process

1. **Scan for documents**: List PDF files in `docs/documents/`

2. **Check what's already ingested**: Query the graph for existing PDF sources in this topic

3. **Process each new document**:
   ```python
   from insight.collector.pdf import extract_pdf
   from insight.graph import InsightGraph
   g = InsightGraph()
   extract_pdf(pdf_path, topic_slug, g)
   ```

4. **Present results**: For each processed document, show source ID, title, block count, extract count

5. **Suggest next steps**: "Run `/analyze {topic}` to extract insights from all sources"

## Supported File Types

- **PDF** (`.pdf`) — Full text, structure, and image extraction via PyMuPDF

## Example

```
# 1. Drop PDFs into docs/documents/
# 2. Process them
/ingest ea-for-ai
```
