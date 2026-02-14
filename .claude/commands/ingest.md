# /ingest <topic>

Process uploaded documents (PDFs, reports, etc.) from a topic's `documents/` folder into structured source notes.

## Arguments

$ARGUMENTS — The topic slug to ingest documents for (e.g., "ai-agents-enterprise")

## Purpose

Many valuable sources are behind login walls, paywalls, or only available as downloaded files. This command lets you:
1. Drop PDFs, reports, presentations, or other files into `knowledge-base/topics/{topic}/documents/`
2. Run `/ingest {topic}` to read and extract structured source notes from them

The structured source notes go into `sources/` alongside web-researched sources, so `/analyze` and `/synthesize` work seamlessly with both.

## Process

1. **Verify topic exists**:
   - Check that `knowledge-base/topics/{topic}/` exists
   - If not, create it with `_index.md`, `documents/`, `sources/`, and `insights/` directories

2. **Scan for new documents**:
   - List all files in `knowledge-base/topics/{topic}/documents/`
   - Read existing source notes in `sources/` to find which documents have already been ingested (check the `document:` frontmatter field)
   - Identify unprocessed documents

3. **Process each document**:
   For each unprocessed document, launch a document-analyst agent with focus "ingest":
   - Read the document (PDF, text, image, etc.)
   - Extract metadata: title, author, date, type
   - Extract key takeaways, notable quotes, data points
   - Write a structured source note to `sources/source-NNN.md`
   - The source note's `document:` field links back to the original file

4. **Update topic metadata**:
   - Update `source_count` in `_index.md`
   - Update the `updated` date

5. **Present results**:
   For each processed document, show:
   - Filename → source note created
   - Extracted title and author
   - Relevance score
   - Top 2-3 takeaways

6. **Suggest next steps**:
   - "Drop more documents into `documents/` and run `/ingest {topic}` again"
   - "Run `/analyze {topic}` to extract insights from all sources"

## Supported File Types

- **PDF** (`.pdf`) — Read tool extracts text and structure
- **Images** (`.png`, `.jpg`) — Read tool extracts visible text and diagrams
- **Text/Markdown** (`.txt`, `.md`) — Direct text extraction
- **Other formats** — Best-effort extraction; may need manual notes

## Example

```
# 1. Drop files into the topic's documents folder
#    (manually copy PDFs to knowledge-base/topics/ai-agents-enterprise/documents/)

# 2. Process them
/ingest ai-agents-enterprise
```

Reads each new document, extracts structured source notes, and makes them available for `/analyze`.
