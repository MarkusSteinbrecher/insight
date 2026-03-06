# Spec: Analyzer

Parent: [Architecture](../v2-architecture.md) | Design: [Analyzer](../analyzer.md)

---

## 1. Overview

The Analyzer provides graph helper functions for the analysis pipeline. Claude Code performs all intelligence (segmentation, claim alignment, etc.) during command execution. The Python module handles graph operations only — no Claude API calls.

**How it works:**
1. Claude Code reads content blocks from the graph via query helpers
2. Claude Code performs analysis (segmentation, classification, alignment)
3. Claude Code writes results to the graph via write helpers

The module is in `insight/analyzer/`.

---

## 2. Segmentation Helpers (`insight.analyzer.segmentation`)

### 2.1 Get Unsegmented Sources

```python
def get_unsegmented_sources(topic: str, graph: InsightGraph) -> list[dict]
```

Returns sources in a topic that have content blocks but no segments yet.

**Logic:**
- Get all sources for the topic
- For each source, check if any segments exist (via `graph.count_segments(source_id=sid)`)
- Return sources with zero segments

### 2.2 Get Source Content for Segmentation

```python
def get_source_content(source_id: str, graph: InsightGraph) -> dict
```

Returns a source's metadata and content blocks, formatted for Claude Code to analyze.

**Output:**
```python
{
    "source_id": str,
    "title": str,
    "author": str,
    "source_type": str,
    "blocks": [
        {"block_id": str, "text": str, "format": str, "section_path": str, "position": int},
        ...
    ]
}
```

### 2.3 Write Segments

```python
def write_segments(source_id: str, segments: list[dict], graph: InsightGraph) -> int
```

Batch-writes segments to the graph. Each segment dict must have:

```python
{
    "block_id": str,        # Which content block this segment comes from
    "text": str,            # Segment text
    "segment_type": str,    # One of the 10 taxonomy types
    "position": int,        # Order within the source
    "section": str,         # Section path (from block)
    "source_format": str,   # prose, bullet, heading, etc.
    "metadata": dict,       # Optional type-specific metadata
}
```

**Behavior:**
- Auto-generates segment IDs: `{source_id}:seg-{NNN}`
- Creates Segment nodes and SEGMENTED_FROM edges
- Returns count of segments written

### 2.4 Get Segmentation Stats

```python
def get_segmentation_stats(source_id: str, graph: InsightGraph) -> dict
```

Returns composition breakdown for a segmented source.

**Output:**
```python
{
    "total_segments": int,
    "composition": {
        "claim": {"count": int, "pct": float},
        "statistic": {"count": int, "pct": float},
        ...
    },
    "signal_ratio": float,  # percentage of non-noise segments
}
```

---

## 3. Claim Alignment Helpers (`insight.analyzer.alignment`)

### 3.1 Get Segments for Alignment

```python
def get_claim_segments(topic: str, graph: InsightGraph, types: list[str] = None) -> list[dict]
```

Returns all segments of specified types across all sources in a topic, grouped by source.

**Default types:** `["claim", "recommendation", "statistic", "evidence"]`

**Output:**
```python
[
    {
        "source_id": str,
        "title": str,
        "author": str,
        "segments": [
            {"segment_id": str, "text": str, "segment_type": str, "section": str},
            ...
        ]
    },
    ...
]
```

### 3.2 Write Claims

```python
def write_claims(topic: str, claims: list[dict], graph: InsightGraph) -> int
```

Batch-writes claims and links supporting segments. Each claim dict:

```python
{
    "claim_id": str,            # e.g., "ea-for-ai:cc-001"
    "claim_category": str,      # "canonical", "unique", or "contradiction"
    "theme": str,               # Short theme label
    "summary": str,             # One-sentence summary
    "claim_type": str,          # "normative", "empirical", "predictive", "definitional"
    "strength": str,            # "strongly-supported" or "supported" (canonical only)
    "description": str,         # Extended description
    "segment_ids": list[str],   # Segments that support this claim
    "metadata": dict,           # Optional
}
```

**Behavior:**
- Creates Claim nodes
- Creates SUPPORTS edges from each segment to the claim
- Returns count of claims written

### 3.3 Write Contradictions

```python
def write_contradictions(contradictions: list[dict], graph: InsightGraph) -> int
```

Links pairs of claims that contradict each other. Each dict:

```python
{
    "claim_id_1": str,
    "claim_id_2": str,
    "description": str,    # Nature of the disagreement
}
```

### 3.4 Get Alignment Stats

```python
def get_alignment_stats(topic: str, graph: InsightGraph) -> dict
```

Returns claim alignment statistics for a topic.

**Output:**
```python
{
    "total_claims": int,
    "canonical": int,
    "unique": int,
    "contradiction": int,
    "total_segments_linked": int,
    "sources_covered": int,
}
```

---

## 4. Query Helpers (`insight.analyzer.queries`)

### 4.1 Topic Summary

```python
def get_topic_summary(topic: str, graph: InsightGraph) -> dict
```

Returns a high-level summary of a topic's analysis state.

**Output:**
```python
{
    "topic": str,
    "sources": int,
    "content_blocks": int,
    "segments": int,
    "claims": int,
    "segmented_sources": int,       # Sources with segments
    "unsegmented_sources": int,     # Sources without segments
}
```

---

## 5. Acceptance Criteria

### Segmentation

- **AC-AN1**: `get_unsegmented_sources()` returns only sources with zero segments.
- **AC-AN2**: `get_unsegmented_sources()` returns empty list when all sources are segmented.
- **AC-AN3**: `get_source_content()` returns blocks ordered by position.
- **AC-AN4**: `write_segments()` creates Segment nodes and SEGMENTED_FROM edges.
- **AC-AN5**: `write_segments()` auto-generates sequential segment IDs.
- **AC-AN6**: `get_segmentation_stats()` returns correct composition breakdown.
- **AC-AN7**: `get_segmentation_stats()` calculates signal_ratio excluding noise.

### Claim Alignment

- **AC-AN8**: `get_claim_segments()` returns only segments of specified types.
- **AC-AN9**: `get_claim_segments()` groups segments by source.
- **AC-AN10**: `write_claims()` creates Claim nodes and SUPPORTS edges.
- **AC-AN11**: `write_claims()` links each segment_id to the claim.
- **AC-AN12**: `write_contradictions()` creates CONTRADICTS edges between claim pairs.
- **AC-AN13**: `get_alignment_stats()` returns correct counts per category.

### Queries

- **AC-AN14**: `get_topic_summary()` returns correct counts for all node types.
- **AC-AN15**: `get_topic_summary()` correctly counts segmented vs unsegmented sources.

---

## 6. Test Plan

### Unit Tests (`tests/unit/test_analyzer.py`)

All tests use an in-memory graph with pre-populated test data. No network access.

| Test | Acceptance Criteria |
|------|-------------------|
| Unsegmented sources returned | AC-AN1 |
| All segmented returns empty | AC-AN2 |
| Source content ordered | AC-AN3 |
| Write segments creates nodes | AC-AN4, AC-AN5 |
| Segmentation stats | AC-AN6, AC-AN7 |
| Claim segments filtered | AC-AN8, AC-AN9 |
| Write claims with links | AC-AN10, AC-AN11 |
| Write contradictions | AC-AN12 |
| Alignment stats | AC-AN13 |
| Topic summary | AC-AN14, AC-AN15 |
