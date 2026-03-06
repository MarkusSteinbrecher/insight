# Spec: Knowledge Graph Schema

Parent: [Architecture](../v2-architecture.md) | Design: [Knowledge Graph](../knowledge-graph.md)

---

## 1. Overview

The knowledge graph is the central data store for Insight. All components read from and write to it. It is backed by KuzuDB (embedded graph database) and accessed through a Python module (`insight.graph.InsightGraph`).

The graph stores the full traceability chain:

```
Source → ContentBlock → Segment → Claim → Finding → Recommendation
```

This spec covers the MVP schema:
- **Collector-facing:** Source, ContentBlock, VisualExtraction
- **Analyzer-facing (MVP):** Segment, Claim

MLP additions (Finding, Recommendation, Concept) will be specified later.

---

## 2. Node Tables

### 2.1 Source

Represents one ingested document, web page, or video.

| Property | Type | Required | Description |
|---|---|---|---|
| `source_id` | STRING | PK | Globally unique. Format: `{topic}:source-{NNN}` |
| `topic` | STRING | yes | Topic slug (e.g., `ea-for-ai`) |
| `source_type` | STRING | yes | One of: `web`, `pdf`, `youtube`, `audio`, `pptx`, `docx`, `image` |
| `url` | STRING | no | Original URL or file path. Empty string if not applicable. |
| `title` | STRING | yes | Document/page/video title |
| `author` | STRING | no | Author or organization. Empty string if unknown. |
| `publication_date` | STRING | no | ISO format `YYYY-MM-DD` or partial. Empty string if unknown. |
| `retrieved_date` | STRING | yes | ISO format `YYYY-MM-DD`. Date when content was collected. |
| `content_hash` | STRING | yes | SHA-256 hex digest of all extracted text content. |
| `language` | STRING | no | ISO 639-1 code. Default: `en`. |
| `metadata` | STRING | no | JSON-encoded dict for format-specific extras. Default: `{}`. |

**Constraints:**
- `source_id` is the primary key
- `url` should be unique per topic (enforced at application level, not database level)

### 2.2 ContentBlock

A positioned unit of content within a source. Paragraph-level granularity for prose, one item per list entry, one row per table row, one chunk per transcript segment.

| Property | Type | Required | Description |
|---|---|---|---|
| `block_id` | STRING | PK | Globally unique. Format: `{source_id}:block-{NNN}` |
| `text` | STRING | yes | The extracted text content |
| `position` | INT64 | yes | Sequential order within the source (1-indexed) |
| `location_type` | STRING | yes | One of: `page`, `timestamp`, `slide`, `heading_path`, `paragraph` |
| `location_value` | STRING | yes | Location-specific value. See Location Formats below. |
| `format` | STRING | yes | One of: `prose`, `heading`, `bullet`, `table_row`, `table_cell`, `figure`, `caption`, `speaker_note`, `quote`, `code` |
| `section_path` | STRING | no | Hierarchical heading context (e.g., `"Introduction > Background"`). Default: `""`. |
| `image_path` | STRING | no | Relative path to image file on disk (for `format: figure`). Default: `""`. |
| `metadata` | STRING | no | JSON-encoded dict for format-specific extras. Default: `{}`. |

**Location formats by `location_type`:**
- `page`: `"page:14,para:3"` or `"page:14,bbox:x1,y1,x2,y2"`
- `timestamp`: `"t:125"` (seconds from start)
- `slide`: `"slide:7"`
- `heading_path`: Same as `section_path` (the heading hierarchy is the location)
- `paragraph`: `"para:42"`

### 2.3 VisualExtraction

Structured interpretation of a visual element (chart, diagram, infographic).

| Property | Type | Required | Description |
|---|---|---|---|
| `extraction_id` | STRING | PK | Globally unique. Format: `{block_id}:visual` |
| `visual_type` | STRING | yes | One of: `bar_chart`, `line_chart`, `pie_chart`, `diagram`, `infographic`, `table_image`, `screenshot`, `photo` |
| `visual_description` | STRING | yes | Natural language description of the visual. Column named `visual_description` to avoid KuzuDB reserved word `description`. |
| `extracted_data` | STRING | no | JSON-encoded array of structured data points. Default: `[]`. |
| `extraction_method` | STRING | no | How the extraction was done. Default: `claude-vision`. |
| `metadata` | STRING | no | JSON-encoded dict. Default: `{}`. |

### 2.4 Segment

A typed unit of meaning extracted from a ContentBlock by the Analyzer. Sentence-level granularity. Each segment is classified by type.

| Property | Type | Required | Description |
|---|---|---|---|
| `segment_id` | STRING | PK | Globally unique. Format: `{source_id}:seg-{NNN}` |
| `text` | STRING | yes | The segment text |
| `segment_type` | STRING | yes | One of: `claim`, `statistic`, `evidence`, `definition`, `recommendation`, `context`, `methodology`, `example`, `attribution`, `noise` |
| `section` | STRING | no | Section heading where this segment appears. Default: `""`. |
| `position` | INT64 | yes | Sequential order within the source (1-indexed) |
| `source_format` | STRING | no | Original format: `prose`, `bullet`, `heading`, `table`, `figure`, `quote`, `caption`. Default: `prose`. |
| `metadata` | STRING | no | JSON-encoded dict for type-specific enrichment (e.g., metric/value/unit for statistics). Default: `{}`. |

**Segment type taxonomy (10 types):**

| Type | Description |
|---|---|
| `claim` | An assertion or argument (normative, empirical, predictive, or definitional) |
| `statistic` | A quantified data point with numbers |
| `evidence` | Data or example supporting a claim |
| `definition` | Defining or explaining a term/concept |
| `recommendation` | Prescriptive/actionable statement |
| `context` | Background information, scene-setting |
| `methodology` | How something was studied or done |
| `example` | Illustrative case or anecdote |
| `attribution` | Citing or referencing another source |
| `noise` | Filler, transitions, marketing language, boilerplate |

### 2.5 Claim

An aligned claim that may be supported by segments from one or more sources. Created by the Analyzer during claim alignment.

| Property | Type | Required | Description |
|---|---|---|---|
| `claim_id` | STRING | PK | Globally unique. Format: `{topic}:cc-{NNN}` (canonical), `{topic}:uc-{NNN}` (unique), `{topic}:ct-{NNN}` (contradiction) |
| `topic` | STRING | yes | Topic slug |
| `claim_category` | STRING | yes | One of: `canonical`, `unique`, `contradiction` |
| `theme` | STRING | yes | Short theme label (e.g., "AI governance gap") |
| `summary` | STRING | yes | One-sentence summary of the claim |
| `claim_type` | STRING | no | One of: `normative`, `empirical`, `predictive`, `definitional`. Default: `""`. |
| `strength` | STRING | no | One of: `strongly-supported`, `supported`. For canonical claims only. Default: `""`. |
| `claim_description` | STRING | no | Extended description. For contradictions: describes the disagreement. Default: `""`. Column named `claim_description` to avoid KuzuDB reserved word `description`. |
| `metadata` | STRING | no | JSON-encoded dict. Default: `{}`. |

**Claim categories:**
- **canonical** (`cc-NNN`): Themes where 2+ sources agree. The mainstream position.
- **unique** (`uc-NNN`): Positions held by only one source. May be novel or niche.
- **contradiction** (`ct-NNN`): Where sources disagree. Contains description of the disagreement.

---

## 3. Edge Tables

### 3.1 CONTAINS

Links a Source to its ContentBlocks.

| Direction | Properties |
|---|---|
| Source → ContentBlock | `position: INT64` |

**Cardinality:** One Source to many ContentBlocks. Each ContentBlock belongs to exactly one Source.

### 3.2 EXTRACTED_FROM

Links a VisualExtraction to the ContentBlock it interprets.

| Direction | Properties |
|---|---|
| VisualExtraction → ContentBlock | (none) |

**Cardinality:** One VisualExtraction per ContentBlock (for figure blocks). Not all ContentBlocks have a VisualExtraction.

### 3.3 SEGMENTED_FROM

Links a Segment to the ContentBlock it was extracted from.

| Direction | Properties |
|---|---|
| Segment → ContentBlock | (none) |

**Cardinality:** Many Segments per ContentBlock (a paragraph may contain multiple sentences/claims). Each Segment comes from exactly one ContentBlock.

### 3.4 SUPPORTS

Links a Segment to a Claim it provides evidence for.

| Direction | Properties |
|---|---|
| Segment → Claim | `representative: BOOLEAN` |

**Properties:**
- `representative`: Whether this segment is the best representative quote for this claim from its source. Used for display/citation.

**Cardinality:** Many Segments can support one Claim (cross-source agreement). One Segment can support multiple Claims (rare but possible).

### 3.5 CONTRADICTS

Links two Claims that are in disagreement.

| Direction | Properties |
|---|---|
| Claim → Claim | `claim_description: STRING` |

**Properties:**
- `claim_description`: Describes the nature of the disagreement. Named to avoid KuzuDB reserved word.

**Cardinality:** Many-to-many. A claim can contradict multiple other claims.

---

## 4. Python API (`insight.graph.InsightGraph`)

### 4.1 Lifecycle

```python
graph = InsightGraph(db_path=None)  # Default: data/insight.db
graph.init_schema()                  # Create tables if not exist
# ... operations ...
graph.close()                        # Release resources
```

### 4.2 Source Operations

```python
# Create
graph.add_source(source_id, topic, source_type, title, url="", author="",
                 publication_date="", retrieved_date=None, content_hash="",
                 language="en", metadata=None) -> str

# Query
graph.source_exists(url=None, source_id=None) -> bool
graph.get_source(source_id) -> dict | None
graph.get_sources_by_topic(topic) -> list[dict]
graph.get_existing_urls(topic) -> set[str]
```

### 4.3 ContentBlock Operations

```python
# Create (also creates CONTAINS edge)
graph.add_content_block(block_id, source_id, text, position,
                        location_type, location_value, format,
                        section_path="", image_path="",
                        metadata=None) -> str

# Query
graph.get_content_blocks(source_id) -> list[dict]  # ordered by position
```

### 4.4 VisualExtraction Operations

```python
# Create (also creates EXTRACTED_FROM edge)
graph.add_visual_extraction(extraction_id, block_id, visual_type,
                            description, extracted_data=None,
                            extraction_method="claude-vision",
                            metadata=None) -> str
```

### 4.5 Segment Operations

```python
# Create (also creates SEGMENTED_FROM edge)
graph.add_segment(segment_id, block_id, text, segment_type, position,
                  section="", source_format="prose", metadata=None) -> str

# Query
graph.get_segments(source_id) -> list[dict]         # all segments for a source, ordered by position
graph.get_segments_by_type(source_id, segment_type) -> list[dict]
graph.get_segments_for_block(block_id) -> list[dict]
```

### 4.6 Claim Operations

```python
# Create
graph.add_claim(claim_id, topic, claim_category, theme, summary,
                claim_type="", strength="", description="",
                metadata=None) -> str

# Link segment to claim (creates SUPPORTS edge)
graph.link_segment_to_claim(segment_id, claim_id, representative=False) -> None

# Link contradicting claims (creates CONTRADICTS edge)
graph.link_contradiction(claim_id_1, claim_id_2, description="") -> None

# Query
graph.get_claim(claim_id) -> dict | None
graph.get_claims_by_topic(topic, category=None) -> list[dict]
graph.get_supporting_segments(claim_id) -> list[dict]  # segments that support this claim
graph.get_claims_for_segment(segment_id) -> list[dict]  # claims a segment supports
graph.get_contradictions(claim_id) -> list[dict]         # claims that contradict this one
```

### 4.7 Traceability Queries

```python
# Follow the chain: claim → segments → content blocks → sources
graph.get_evidence_chain(claim_id) -> list[dict]
# Returns: [{claim, segment, block, source}, ...] for each supporting segment

# Get all claims for a source (via its segments)
graph.get_claims_for_source(source_id) -> list[dict]
```

### 4.8 Aggregate Operations

```python
graph.count_sources(topic=None) -> int
graph.count_content_blocks(source_id=None) -> int
graph.count_segments(source_id=None) -> int
graph.count_claims(topic=None, category=None) -> int
```

### 4.9 Utility

```python
InsightGraph.content_hash(text: str) -> str  # SHA-256 hex digest (static method)
```

---

## 5. Acceptance Criteria

### Schema

- **AC-S1**: Calling `init_schema()` on a fresh database creates all node and edge tables without error.
- **AC-S2**: Calling `init_schema()` on an existing database with tables already present is idempotent (no error, no data loss).

### Source CRUD

- **AC-SC1**: `add_source()` creates a Source node retrievable by `get_source()` with all properties matching.
- **AC-SC2**: `add_source()` with `retrieved_date=None` defaults to today's date.
- **AC-SC3**: `add_source()` with `metadata` dict stores it as JSON string, retrievable and parseable.
- **AC-SC4**: `source_exists(url=...)` returns `True` for a known URL, `False` for unknown.
- **AC-SC5**: `source_exists(source_id=...)` returns `True` for a known ID, `False` for unknown.
- **AC-SC6**: `get_sources_by_topic()` returns only sources matching the given topic, ordered by `source_id`.
- **AC-SC7**: `get_existing_urls()` returns all non-empty URLs for a topic as a set.
- **AC-SC8**: `get_source()` returns `None` for a non-existent `source_id`.

### ContentBlock CRUD

- **AC-CB1**: `add_content_block()` creates a ContentBlock node and a CONTAINS edge to the specified Source.
- **AC-CB2**: `get_content_blocks(source_id)` returns all blocks for a source, ordered by `position`.
- **AC-CB3**: `get_content_blocks()` for a source with no blocks returns an empty list.
- **AC-CB4**: Block `metadata` round-trips correctly as JSON (dict in, JSON string stored, parseable back to dict).

### VisualExtraction CRUD

- **AC-VE1**: `add_visual_extraction()` creates a node and an EXTRACTED_FROM edge to the specified ContentBlock.
- **AC-VE2**: `extracted_data` round-trips correctly as JSON array.

### Aggregates

- **AC-AG1**: `count_sources()` without topic returns total count across all topics.
- **AC-AG2**: `count_sources(topic=...)` returns count for that topic only.
- **AC-AG3**: `count_content_blocks()` without source_id returns total count.
- **AC-AG4**: `count_content_blocks(source_id=...)` returns count for that source only.

### Utility

- **AC-UT1**: `content_hash()` returns consistent SHA-256 hex digest for the same input.
- **AC-UT2**: `content_hash()` returns different digests for different inputs.

### Segment CRUD

- **AC-SG1**: `add_segment()` creates a Segment node and a SEGMENTED_FROM edge to the specified ContentBlock.
- **AC-SG2**: `get_segments(source_id)` returns all segments for a source (via Source → ContentBlock → Segment), ordered by position.
- **AC-SG3**: `get_segments_by_type(source_id, "claim")` returns only segments of that type.
- **AC-SG4**: `get_segments_for_block(block_id)` returns all segments extracted from that block.
- **AC-SG5**: `get_segments()` for a source with no segments returns an empty list.
- **AC-SG6**: Segment `metadata` round-trips correctly as JSON.

### Claim CRUD

- **AC-CL1**: `add_claim()` creates a Claim node retrievable by `get_claim()` with all properties matching.
- **AC-CL2**: `get_claim()` returns `None` for a non-existent claim_id.
- **AC-CL3**: `get_claims_by_topic(topic)` returns all claims for a topic.
- **AC-CL4**: `get_claims_by_topic(topic, category="canonical")` returns only canonical claims.
- **AC-CL5**: `link_segment_to_claim()` creates a SUPPORTS edge between a segment and a claim.
- **AC-CL6**: `get_supporting_segments(claim_id)` returns all segments linked via SUPPORTS edges.
- **AC-CL7**: `get_claims_for_segment(segment_id)` returns all claims the segment supports.
- **AC-CL8**: `link_contradiction()` creates a CONTRADICTS edge between two claims.
- **AC-CL9**: `get_contradictions(claim_id)` returns claims linked via CONTRADICTS edges.

### Traceability

- **AC-TR1**: `get_evidence_chain(claim_id)` returns records with claim, segment, content block, and source information for each supporting segment.
- **AC-TR2**: Evidence chain includes segments from multiple sources when a claim is supported cross-source.
- **AC-TR3**: `get_claims_for_source(source_id)` returns all claims supported by segments from that source.

### Aggregates (extended)

- **AC-AG5**: `count_segments()` without source_id returns total count.
- **AC-AG6**: `count_segments(source_id=...)` returns count for that source only.
- **AC-AG7**: `count_claims()` without filters returns total count.
- **AC-AG8**: `count_claims(topic=..., category="canonical")` returns filtered count.

### Edge Cases

- **AC-EC1**: Adding a source with an empty `url` does not break `source_exists(url="")` (should not match empty strings as "existing").
- **AC-EC2**: ContentBlock `text` can contain unicode, newlines, and special characters without data loss.
- **AC-EC3**: Multiple sources can exist for the same topic without conflict.
- **AC-EC4**: A segment can support multiple claims without error.
- **AC-EC5**: A claim can be supported by segments from different sources.
- **AC-EC6**: Contradictions are queryable from both sides (if A contradicts B, querying contradictions for B returns A).
