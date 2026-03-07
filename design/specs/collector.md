# Spec: Collector

Parent: [Architecture](../v2-architecture.md) | Design: [Collector](../collector.md)

---

## 1. Overview

The Collector gets content into the knowledge graph. It has two sub-components:

1. **Discovery** — find candidate sources, check them against the source registry, report what's new vs already collected.
2. **Extraction** — fetch content from a URL or file, parse into structured content blocks, write Source + ContentBlock nodes to the graph.

The Collector performs no analysis (no segmentation, no claim extraction). Its job is faithful, structured extraction with provenance metadata.

---

## 2. Discovery (`insight.collector.discovery`)

### 2.1 Source Registry Check

```python
def check_urls(urls: list[str], topic: str, graph: InsightGraph) -> DiscoveryResult
```

**Input:** List of candidate URLs, topic slug, graph instance.

**Output:**
```python
@dataclass
class DiscoveryResult:
    new: list[str]           # URLs not in the graph
    existing: list[str]      # URLs already collected
    total: int               # len(new) + len(existing)
```

**Behavior:**
- Queries the graph for all existing URLs in the topic via `graph.get_existing_urls(topic)`.
- URL comparison is case-insensitive, trailing-slash-normalized.
- Normalizes common URL variants: strips `www.`, normalizes `http` vs `https`, removes tracking parameters (`utm_*`, `ref`, `source`).
- Does not fetch any URLs — this is a graph lookup only.

### 2.2 URL Normalization

```python
def normalize_url(url: str) -> str
```

Normalizes a URL for deduplication comparison:
- Lowercase the scheme and hostname
- Strip `www.` prefix
- Remove trailing slash
- Remove known tracking parameters (`utm_source`, `utm_medium`, `utm_campaign`, `utm_content`, `utm_term`, `ref`, `source`)
- Preserve path, query (minus tracking), and fragment

---

## 3. Extraction

### 3.1 Web Extractor (`insight.collector.web`)

```python
def extract_web_source(url: str, topic: str, source_id: str, graph: InsightGraph) -> ExtractionResult
```

**Input:** URL to fetch, topic slug, pre-assigned source_id, graph instance.

**Output:**
```python
@dataclass
class ExtractionResult:
    source_id: str
    title: str
    author: str
    date: str
    block_count: int
    content_length: int       # total chars across all blocks
```

**Behavior:**
1. Fetch page HTML via Playwright (headless Chromium, networkidle wait + 2s).
2. Parse HTML with BeautifulSoup.
3. Extract metadata: title (og:title > title tag), author (meta author > og:site_name > domain lookup), date (article:published_time > meta date > JSON-LD), description.
4. Extract content blocks with heading path tracking (see 3.1.1).
5. Compute content hash (SHA-256 of concatenated block texts).
6. Write Source node to graph.
7. Write ContentBlock nodes to graph, each linked via CONTAINS edge.
8. Return ExtractionResult.

**Error conditions:**
- Page returns HTTP error → raise `ExtractionError`
- Page renders but produces < 3 content blocks → raise `ExtractionError("Insufficient content")`
- Playwright timeout → raise `ExtractionError`

#### 3.1.1 Content Block Extraction

```python
def extract_content_blocks(soup: BeautifulSoup) -> list[dict]
```

Walks the DOM of the best content container, tracking heading hierarchy.

**Container selection:** Largest text content among `<article>`, `<main>`, `div[role=main]`, `div.article|content|post|entry`. Falls back to `<body>` if no candidate exceeds 500 chars.

**Element processing order:** `h1-h6`, `p`, `li`, `blockquote`, `td`, `th`, `figcaption` — in document order.

**Heading path tracking:**
- Maintain a stack of `(level, text)` tuples.
- On encountering `h{N}`, pop all entries with level >= N, push new entry.
- Every non-heading block gets the current stack as its `section_path` (joined with ` > `).

**Format detection:**
| Element | Format |
|---|---|
| `h1`-`h6` | `heading` |
| `p` | `prose` |
| `li` | `bullet` |
| `blockquote` | `quote` |
| `td`, `th` | `table_cell` |
| `figcaption` | `caption` |

**Boilerplate removal:**
- Stop extraction when a heading matches boilerplate patterns (Contact us, Newsletter, Subscribe, Footer, Legal, Privacy, etc.).
- Skip elements with < 20 chars that match navigation noise patterns (Menu, Featured, Loading, Skip to).
- Deduplicate: track seen text, skip elements whose text was already captured (handles nested `<li><p>` duplication).

**Output per block:**
```python
{
    "text": str,           # Extracted text, whitespace-normalized
    "format": str,         # One of the format values above
    "section_path": str,   # Heading hierarchy (e.g., "Introduction > Background")
    "location_value": str, # Same as section_path for web sources
}
```

#### 3.1.2 Metadata Extraction

```python
def extract_metadata(soup: BeautifulSoup, url: str) -> dict
```

**Title resolution order:**
1. `<meta property="og:title">` content
2. `<title>` tag text
3. `"Untitled"`

Post-processing: strip trailing site names (` | Gartner`, ` - McKinsey`).

**Author resolution order:**
1. `<meta name="author">` content
2. `<meta property="og:site_name">` content
3. Domain-based lookup (hardcoded mapping for major publishers)
4. Cleaned domain name

**Date resolution order:**
1. `<meta property="article:published_time">` content
2. `<meta name="date">` content
3. JSON-LD `datePublished` field
4. Empty string (not today's date — unknown is better than wrong)

**Output:**
```python
{
    "title": str,
    "author": str,
    "date": str,          # "YYYY-MM-DD" or "" if unknown
    "description": str,   # og:description or meta description
}
```

### 3.2 YouTube Extractor (`insight.collector.youtube`)

```python
def extract_youtube_source(url: str, topic: str, source_id: str, graph: InsightGraph) -> ExtractionResult
```

**Behavior:**
1. Parse video ID from URL (supports youtube.com/watch, youtu.be, embed, /v/ formats).
2. Fetch video metadata via oEmbed API (title, author/channel name).
3. Fetch transcript via `youtube-transcript-api` (prefer manual captions over auto-generated).
4. Group transcript segments into paragraph-level blocks (see 3.2.1).
5. Compute content hash.
6. Write Source node (source_type: `youtube`, url: canonical `youtube.com/watch?v=` format).
7. Write ContentBlock nodes with timestamp locations.
8. Return ExtractionResult.

**Source metadata stored:**
```python
metadata = {
    "video_id": str,
    "channel_url": str,
    "duration_seconds": int,
    "transcript_segments": int,   # raw segment count before grouping
}
```

**Error conditions:**
- Invalid URL / no video ID → raise `ExtractionError`
- No transcript available → raise `ExtractionError("No transcript available")`
- oEmbed fails → continue with empty metadata (title from video ID)

#### 3.2.1 Transcript Grouping

```python
def group_transcript_segments(segments: list[dict], max_gap: float = 5.0, max_duration: float = 60.0) -> list[dict]
```

Groups consecutive transcript segments into paragraph-level blocks.

**Grouping rules:**
- Start a new block when gap between segments > `max_gap` seconds (default: 5.0)
- Start a new block when accumulated duration > `max_duration` seconds (default: 60.0)
- Concatenate segment texts with spaces

**Output per block:**
```python
{
    "text": str,     # Concatenated segment texts
    "start": float,  # Start time in seconds
    "end": float,    # End time in seconds
}
```

**ContentBlock properties for YouTube:**
- `location_type`: `"timestamp"`
- `location_value`: `"t:{seconds}"` (integer seconds)
- `section_path`: `"[M:SS]"` or `"[H:MM:SS]"` formatted timestamp
- `format`: `"prose"`
- `metadata`: `{"start": float, "end": float, "timestamp_url": "https://youtube.com/watch?v=ID&t=N"}`

#### 3.2.2 Video ID Extraction

```python
def extract_video_id(url: str) -> str | None
```

Supported URL formats:
- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://www.youtube.com/embed/VIDEO_ID`
- `https://www.youtube.com/v/VIDEO_ID`
- `https://m.youtube.com/watch?v=VIDEO_ID`

Returns `None` for unrecognized formats.

### 3.3 PDF Extractor (`insight.collector.pdf`)

Implemented using PyMuPDF. Font-aware extraction with heading detection, image extraction (raster + vector page renders), boilerplate stripping, and sentence-boundary processing via shared `blocks.py` module.

### 3.4 Content Block Post-Processing (`insight.collector.blocks`)

All extractors apply shared post-processing to ensure clean block boundaries:

1. **`merge_incomplete_blocks()`** — joins prose blocks that end mid-sentence with the following prose block. Detects incomplete blocks by checking for missing sentence-ending punctuation (`.!?"')`) at the end of text.

2. **`split_long_blocks(max_len=800)`** — splits prose blocks exceeding `max_len` at sentence boundaries. Protects abbreviations (Dr., U.S., e.g., etc.) from false splits. Never drops content.

3. **`clean_blocks()`** — runs merge then split in sequence. Called by all extractors after initial block extraction.

YouTube uses a variant (`_merge_incomplete_transcript_blocks`) that preserves start/end timestamps during merging.

### 3.5 Visual Extraction

Images and figures are extracted during the collection process:

1. **PDF**: Raster images extracted via PyMuPDF, vector-heavy pages rendered as PNGs. Creates `format: "figure"` ContentBlocks with `image_path`.

2. **Web**: (Planned) `<img>` elements inside `<figure>` or above size threshold downloaded to `data/images/{topic}/{source_id}/`.

3. **Semantic extraction**: The extraction agent (Claude Code) reads each figure image and creates `VisualExtraction` nodes via `graph.add_visual_extraction()`. This happens during the extraction process, not as a separate command.

### 3.6 Source Type Detection

```python
def detect_source_type(url: str) -> str
```

| URL pattern | Returns |
|---|---|
| Contains `youtube.com/watch` or `youtu.be/` | `"youtube"` |
| Ends with `.pdf` | `"pdf"` |
| Everything else | `"web"` |

---

## 4. CLI (`insight.collector.cli`)

Entry point: `python -m insight.collector <command> [options]`

### 4.1 Commands

#### `extract`

Collect sources from URLs into the graph.

```
python -m insight.collector extract --urls URL [URL ...] --topic TOPIC
python -m insight.collector extract --file PATH --topic TOPIC
```

**Behavior:**
1. Initialize graph, ensure schema exists.
2. Get existing URLs for topic from registry.
3. For each URL: check if already collected. If yes, skip and report. If no, detect source type and run appropriate extractor.
4. Auto-assign source IDs: `{topic}:source-{NNN}` where NNN is next sequential number for that topic.
5. Print per-source result (title, block count, content length).
6. Print summary: collected N, failed N, skipped N (already existed).

**Exit codes:**
- 0: success (even if some sources were skipped)
- 1: all sources failed

#### `discover`

Check URLs against the source registry without fetching.

```
python -m insight.collector discover --urls URL [URL ...] --topic TOPIC
```

**Behavior:**
1. Initialize graph.
2. Check each URL against registry.
3. Print: N URLs checked, M new, K already collected.
4. List new URLs (prefixed with `+`) and existing URLs (prefixed with `-`).

#### `status`

Show collection status for a topic.

```
python -m insight.collector status --topic TOPIC
```

**Output:**
- Topic name, total source count
- Breakdown by source type (web: N, youtube: N, pdf: N)
- Per-source listing: source_id, source_type, block count, title (truncated to 55 chars)
- Total content block count

---

## 5. Acceptance Criteria

### Discovery

- **AC-D1**: `check_urls()` correctly identifies URLs already in the graph as `existing`.
- **AC-D2**: `check_urls()` correctly identifies new URLs as `new`.
- **AC-D3**: URL normalization treats `http://www.example.com/` and `https://example.com` as the same URL.
- **AC-D4**: URL normalization strips `utm_*` tracking parameters.
- **AC-D5**: `check_urls()` with an empty graph returns all URLs as `new`.

### Web Extraction

- **AC-W1**: Given a sample HTML page with headings and paragraphs, `extract_content_blocks()` produces blocks with correct `format` values.
- **AC-W2**: Section paths correctly track nested heading hierarchy (e.g., H2 "Intro" > H3 "Background" → `"Intro > Background"`).
- **AC-W3**: When a deeper heading follows (e.g., H3 after H2), the stack pops correctly and section path updates.
- **AC-W4**: When a same-level heading follows (e.g., H2 after H2), the previous H2 is popped and replaced.
- **AC-W5**: Boilerplate headings ("Contact us", "Newsletter") cause extraction to stop — no blocks after that point.
- **AC-W6**: Duplicate text from nested elements (e.g., `<li><p>same text</p></li>`) produces only one block.
- **AC-W7**: Metadata extraction finds title from `og:title` when present.
- **AC-W8**: Metadata extraction falls back through the resolution chain (og:title → title tag → "Untitled").
- **AC-W9**: Date extraction produces `YYYY-MM-DD` format or empty string.
- **AC-W10**: `extract_web_source()` writes one Source node and N ContentBlock nodes to the graph.
- **AC-W11**: All ContentBlock nodes are linked to the Source via CONTAINS edges.
- **AC-W12**: Content hash is deterministic — same content produces same hash.

### YouTube Extraction

- **AC-Y1**: `extract_video_id()` correctly parses all supported URL formats.
- **AC-Y2**: `extract_video_id()` returns `None` for non-YouTube URLs.
- **AC-Y3**: `group_transcript_segments()` groups segments within `max_gap` into a single block.
- **AC-Y4**: `group_transcript_segments()` splits when gap exceeds `max_gap`.
- **AC-Y5**: `group_transcript_segments()` splits when accumulated duration exceeds `max_duration`.
- **AC-Y6**: `group_transcript_segments()` with empty input returns empty list.
- **AC-Y7**: ContentBlock `location_value` is formatted as `"t:{seconds}"`.
- **AC-Y8**: ContentBlock `metadata` includes `timestamp_url` with correct YouTube link.
- **AC-Y9**: `extract_youtube_source()` writes one Source node with `source_type: youtube`.
- **AC-Y10**: Source metadata includes `video_id` and `duration_seconds`.

### CLI

- **AC-CLI1**: `extract --urls` with a new URL collects it and reports success.
- **AC-CLI2**: `extract --urls` with an already-collected URL skips it and reports "already existed".
- **AC-CLI3**: `extract --urls` with a mix of new and existing URLs collects only the new ones.
- **AC-CLI4**: `discover --urls` reports correct counts without fetching any URLs.
- **AC-CLI5**: `status --topic` shows source count, type breakdown, and per-source block counts.

### Source Registry

- **AC-SR1**: Collecting a source then checking its URL via `discover` shows it as existing.
- **AC-SR2**: Collecting sources from two different topics does not cross-contaminate the registry.
- **AC-SR3**: Auto-assigned source IDs are sequential within a topic.
- **AC-SR4**: Source IDs follow the format `{topic}:source-{NNN}` with zero-padded numbers.

---

## 6. Test Plan

### Unit Tests (`tests/unit/`)

| Test file | Tests | Fixtures needed |
|---|---|---|
| `test_web_extractor.py` | AC-W1 through AC-W9 | `sample_article.html` — HTML with headings, paragraphs, lists, boilerplate footer |
| `test_youtube_extractor.py` | AC-Y1 through AC-Y6 | None (pure logic) |
| `test_discovery.py` | AC-D1 through AC-D5 | None (uses graph in tmp dir) |

### Integration Tests (`tests/integration/`)

| Test file | Tests | Notes |
|---|---|---|
| `test_web_pipeline.py` | AC-W10, AC-W11, AC-W12, AC-CLI1 | Needs network or recorded HTML |
| `test_youtube_pipeline.py` | AC-Y7 through AC-Y10 | Needs network or recorded transcript |
| `test_source_registry.py` | AC-SR1 through AC-SR4 | End-to-end with real graph |
