# Component: Collector

Parent: [v2 Architecture](v2-architecture.md)
Status: **Design**

---

## Purpose

The Collector gets content into the system. It has two sub-components with distinct responsibilities:

1. **Discovery** — find candidate sources (web search, YouTube search, manual URLs, citation following). Checks the source registry to filter out already-collected sources. Outputs a list of new candidates.
2. **Extraction** — take a URL or file, fetch the content, parse it into structured content blocks, write Source + ContentBlock nodes to the graph.

The Collector performs no analysis — its job is faithful extraction with provenance metadata, so that every piece of content is traceable back to its exact origin.

## Principles

- **Extract once, analyze many times.** Content blocks can be re-processed by the Analyzer without re-fetching the original source.
- **Discovery and extraction are separate.** Discovery can fail (bad search) independently from extraction (page won't render). The source registry sits between them.

```
Discovery                Registry Check              Extraction
─────────               ──────────────              ──────────
web search    ─┐                                    ┌─→ web extractor
YouTube search ├─→ candidate URLs ─→ filter known ──├─→ YouTube extractor
manual URLs   ─┤                                    ├─→ PDF extractor
citation refs ─┘         ↕                          └─→ ...
                    graph lookup                         ↓
                                                    Source + ContentBlock
                                                    nodes in graph
```

---

## Supported Source Types

| Source type | Extraction tool | Output format | Location anchor |
|---|---|---|---|
| Web pages | Playwright + BeautifulSoup | Structured text with DOM hierarchy | URL + heading path |
| PDFs | Docling (structural) + Claude vision (figures) | Text blocks with layout | Page + bounding box |
| YouTube | `youtube-transcript-api` | Timestamped transcript segments | Video URL + timestamp |
| Audio/Podcasts | Whisper (local or API) | Timestamped transcript segments | File + timestamp |
| PowerPoint | `python-pptx` | Slide text + speaker notes | Slide number |
| Word docs | `python-docx` | Structured text with headings | Section + paragraph index |
| Academic papers | Docling + Semantic Scholar API | Text + structured metadata | DOI + section + page |
| Images/diagrams | Claude vision | Extracted description + data | File path + region |

### Extraction Strategy: Two-Stage

For complex formats (PDF, web), extraction happens in two stages:

1. **Structural extraction** (deterministic, no LLM) — parse the document into positioned text blocks using format-specific tools. Fast, cheap, reproducible.
2. **Semantic extraction** (LLM, only when needed) — interpret figures, resolve ambiguous layouts, extract meaning from scanned images. Called only for content the structural pass can't handle.

This keeps costs down and ensures the majority of extraction is deterministic.

---

## Data Model

The Collector writes two node types to the graph:

### Source Node

Represents one ingested document/page/video.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `source_id` | string | yes | Unique identifier (e.g., `source-001`) |
| `source_type` | enum | yes | `web`, `pdf`, `youtube`, `audio`, `pptx`, `docx`, `image` |
| `url` | string | no | Original URL (web, YouTube) or file path (local) |
| `title` | string | yes | Document/page title |
| `author` | string | no | Author or organization |
| `date` | date | no | Publication date |
| `retrieved_date` | date | yes | When the content was collected |
| `content_hash` | string | yes | SHA-256 of extracted content (for change detection) |
| `language` | string | no | Content language (ISO 639-1) |
| `metadata` | JSON | no | Format-specific metadata (page count, video duration, etc.) |

### Content Block Node

A positioned unit of content within a source. Granularity: roughly paragraph-level for prose, one row per table row, one entry per list item, one segment per transcript chunk.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `block_id` | string | yes | Unique within source (e.g., `block-001`) |
| `text` | string | yes | The extracted text content |
| `position` | int | yes | Sequential order within the source |
| `location_type` | enum | yes | `page`, `timestamp`, `slide`, `heading_path`, `paragraph` |
| `location_value` | string | yes | Location-specific value (e.g., `"page:14,para:3"`, `"t:125.4"`, `"slide:7"`) |
| `format` | enum | yes | `prose`, `heading`, `bullet`, `table_row`, `figure`, `caption`, `speaker_note`, `quote`, `code` |
| `section_path` | string | no | Hierarchical heading context (e.g., `"Introduction > Background"`) |
| `metadata` | JSON | no | Format-specific extras (table headers, image path, timestamp duration) |

### Edges

| Edge | From | To | Properties |
|------|------|----|------------|
| `CONTAINS` | Source | Content Block | `position` (redundant but useful for ordered traversal) |

---

## Extraction Details Per Format

### Web Pages

**Current state (v1):** Playwright renders JS, BeautifulSoup extracts text, output is a flat markdown file.

**v2 improvements:**
- Preserve DOM hierarchy as `section_path` (track heading nesting during traversal)
- Extract tables as structured data — each row becomes a content block with `format: table_row` and table headers in metadata
- Extract `<figure>` and `<img>` elements — store image URL, alt text, caption
- Capture page metadata: `<meta>` tags (author, date, description), `<time>` elements, JSON-LD structured data
- Store the heading path for each block, enabling "Introduction > Background > AI Adoption" style anchoring

**Fallback option:** Jina Reader API (`r.jina.ai`) for simple pages where Playwright is overkill. Returns clean markdown. Use when: no JS interaction needed, no table extraction needed.

### PDFs

**Tool: Docling** (IBM, open source)

Why Docling over PyMuPDF:
- Layout-aware: understands columns, headers, footers
- Table detection and extraction built in
- Figure detection with bounding boxes
- Academic paper structure recognition (abstract, sections, references)
- Outputs structured document model, not just text

**Process:**
1. Docling extracts text blocks with page numbers + bounding boxes
2. Tables extracted as structured data
3. Figures: store bounding box + run Claude vision to describe content and extract data points
4. Academic papers: Semantic Scholar API lookup by DOI/title for structured metadata (citations, abstract, venue)

**Location anchor:** `page:N,bbox:x1,y1,x2,y2` — enables linking back to exact location in PDF.

### YouTube

**Tool: `youtube-transcript-api`**

**Process:**
1. Fetch transcript (prefer manual captions over auto-generated)
2. Each transcript segment becomes a content block with `location_type: timestamp`
3. Group consecutive segments into paragraph-level blocks (configurable window, e.g., 30-second chunks)
4. Capture video metadata: title, channel, upload date, duration, description

**Location anchor:** `t:125` — generates `youtu.be/VIDEO_ID?t=125` links.

**Fallback:** For videos without transcripts, download audio and run Whisper.

### Audio / Podcasts

**Tool: Whisper** (local via `whisper.cpp`, or OpenAI API)

**Process:**
1. Transcribe with timestamps
2. Segment into blocks (sentence-level with timestamps, or paragraph-level by grouping)
3. Speaker diarization if available (identifies who is speaking)

**Location anchor:** `t:125` — timestamp in seconds.

### PowerPoint

**Tool: `python-pptx`**

**Process:**
1. Iterate slides in order
2. Per slide: extract title, text boxes (in reading order), speaker notes
3. Each text element becomes a content block; speaker notes get `format: speaker_note`
4. Embedded images: extract and describe via Claude vision

**Location anchor:** `slide:N`

### Word Documents

**Tool: `python-docx`**

**Process:**
1. Iterate paragraphs, tracking heading hierarchy
2. Each paragraph becomes a content block with its heading path as `section_path`
3. Tables: each row becomes a block
4. Embedded images: extract and describe

**Location anchor:** `heading_path` + `paragraph:N`

---

## Source Registry & Deduplication

The Collector maintains awareness of all previously collected sources. This is critical for repeat research — when `/research` runs a new web search on an existing topic, the Collector must know what it already has.

### Source Registry

Every collected source is tracked in the graph by URL (for web/YouTube) or file hash (for local files). Before collecting, the Collector queries the graph:

```
Web search returns 15 candidate URLs
  → 5 already in graph (skip)
  → 2 are duplicates of each other (collect once)
  → 8 genuinely new (collect)
  → Report: "15 results: 8 new, 5 already collected, 2 duplicates"
```

This check is cheap (URL lookup in the graph) and prevents wasted scraping and re-extraction.

### Deduplication

Two levels:

1. **URL/path dedup** — if a source with the same URL or file path already exists in the graph, skip it. Report to the user that the source is already collected.
2. **Content dedup** — hash each content block's text. If two different URLs produce identical blocks (syndicated content, reprints), link them via a `DUPLICATE_OF` edge rather than duplicating content.

No source versioning for now. If a source needs to be re-collected (e.g., content has changed significantly), the user can explicitly remove the old source and re-collect.

---

## Visual Content Extraction

Images, diagrams, charts, and infographics require special handling. The Collector stores both the original image and a structured interpretation.

### Storage Model

```
[Image File]  ←──── on disk (documents/)
      │                binary, gitignored
      │
[Content Block]  ←── in graph
      format: figure
      image_path: "documents/report-fig3.png"
      location: "page:14,figure:3"
      │
      │  EXTRACTED_FROM
      ▼
[Visual Extraction]  ←── in graph
      visual_type: bar_chart
      description: "AI adoption by sector, 2020-2025"
      extracted_data: [{label: "Finance", value: 82}, ...]
      extraction_method: claude-vision
```

- **Image file** lives on disk in `documents/`. Not stored in the graph — binary blobs don't belong in a graph database.
- **Content Block** with `format: figure` is created by the Collector during structural extraction. It carries the `image_path` reference and the location anchor. This is the provenance link.
- **Visual Extraction** is created by the Collector's semantic pass (Claude vision). It contains the structured interpretation — data points, relationships, descriptions. This is what the Analyzer works with downstream.

### Extraction by Visual Type

| Visual type | What Claude vision extracts | Output structure |
|---|---|---|
| Bar/line/pie charts | Data points, axis labels, trends, title | `extracted_data`: array of `{label, value, unit}` + narrative summary |
| Architecture/flow diagrams | Components, relationships, direction | `extracted_data`: array of `{from, to, relationship}` + description |
| Infographics | Key statistics, categories, hierarchy | `extracted_data`: structured data points + organizational logic |
| Tables (as images) | Row/column data | `extracted_data`: array of row objects with column headers |
| Screenshots | Visible text, layout context | `extracted_text` + layout description |
| Photos | Description, context, visible text | Narrative description |

The extraction prompt is tailored per `visual_type` — a generic "describe this image" loses too much structure.

### Visual Type Detection

The Collector uses a two-step approach:
1. **Heuristic detection** — Docling/BeautifulSoup can often identify charts vs diagrams vs photos from context (alt text, caption, surrounding text, file naming conventions)
2. **Claude vision classification** — if heuristics are inconclusive, ask Claude to classify the visual type before running the type-specific extraction prompt

---

## Optimizations

1. **Parallel collection** — sources are independent. Scrape/extract multiple concurrently. Rate-limit per domain (respect `robots.txt`).
2. **Tiered extraction** — structural pass first (fast, free), LLM only for hard cases (figures, scanned pages).
3. **Caching** — store raw fetched content (HTML, PDF bytes) locally so re-extraction doesn't require re-fetching.
4. **Incremental processing** — only process new/changed sources. Use `content_hash` to detect changes.

---

## Error Handling

| Failure | Behavior |
|---------|----------|
| URL returns 404/5xx | Log error, mark source as `failed`, skip |
| Page requires authentication | Log, mark as `auth_required`, skip |
| PDF is scanned/image-only | Fall back to Claude vision for full-page OCR |
| YouTube has no transcript | Fall back to Whisper audio transcription |
| Extraction produces no content | Log warning, create source node with `empty` status |
| Rate limited | Back off exponentially, retry up to 3 times |

---

## CLI Interface

The Collector is invoked through Claude Code commands but can also run standalone:

```bash
# --- Discovery ---

# Search the web for sources on a topic, filter against registry
python -m insight.collector discover --web "Enterprise Architecture AI" --topic ea-for-ai

# Search YouTube
python -m insight.collector discover --youtube "enterprise architecture AI" --topic ea-for-ai

# Check a list of URLs against the registry (which are new?)
python -m insight.collector discover --urls "https://..." "https://..." --topic ea-for-ai

# --- Extraction ---

# Extract from URLs (skips any already in graph)
python -m insight.collector extract --urls "https://..." "https://..." --topic ea-for-ai

# Extract a local file
python -m insight.collector extract --file report.pdf --topic ea-for-ai

# Extract a YouTube video
python -m insight.collector extract --urls "https://youtube.com/watch?v=..." --topic ea-for-ai

# --- Status ---

# Show what's collected for a topic
python -m insight.collector status --topic ea-for-ai
```

The `/research` command calls discovery + extraction. The `/ingest` command calls extraction directly for local files.

---

## Decisions Made

1. **Content block granularity** — paragraph-level from the Collector, sentence-level segmentation from the Analyzer.
2. **Image/figure storage** — image files on disk (`documents/`), referenced from Content Block nodes via `image_path`. Structured interpretation stored as Visual Extraction nodes in the graph.
3. **Source versioning** — not needed. Source registry tracks what's collected. User can manually remove and re-collect if needed.

## Open Questions

1. **Authentication support** — support cookies/auth headers for paywalled sources (Gartner, HBR)? Or out of scope for v2?
2. **Raw content caching** — store fetched HTML/PDF bytes for re-extraction? Useful but adds storage.
3. **Jina Reader vs Playwright** — use Jina as primary (simpler, cleaner output) with Playwright as fallback for JS-heavy sites? Or always Playwright?
