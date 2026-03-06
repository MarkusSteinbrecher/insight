# Spec: Presenter (MVP)

Parent: [Architecture](../v2-architecture.md) | Design: [Presenter](../presenter.md)

---

## 1. Overview

The Presenter exports data from the knowledge graph to JSON files that the static site renders. For MVP, the exporter replaces the v1 build scripts with graph-backed versions.

**MVP scope:**
- `topics.json` — topic list with metadata
- `{topic}/stats.json` — aggregated statistics
- `{topic}/sources.json` — source list with metadata

The existing site frontend (`docs/index.html`, `docs/js/app.js`, `docs/css/style.css`) is unchanged. It already handles missing data files gracefully.

---

## 2. Exporter (`insight/exporter/`)

### 2.1 Export All

```python
def export_all(graph: InsightGraph, output_dir: str) -> dict
```

Exports all topic data to the output directory. Returns a summary of what was exported.

**Behavior:**
1. Get all topics from graph (distinct `topic` values from Source nodes)
2. Export `topics.json`
3. For each topic, export `stats.json` and `sources.json`
4. Return `{"topics": N, "sources": N}`

### 2.2 Export Topics Manifest

```python
def export_topics(graph: InsightGraph, output_dir: str) -> list[dict]
```

Writes `{output_dir}/topics.json`.

**Output format:**
```json
{
    "topics": [
        {
            "slug": "ea-for-ai",
            "title": "EA for AI",
            "phase": 1,
            "source_count": 56
        }
    ],
    "default_topic": "ea-for-ai"
}
```

**Topic title:** derived from slug (replace hyphens with spaces, title case). Can be overridden by `_index.md` if it exists locally.

**Phase:** determined from graph state:
- Has claims → phase 3
- Has segments but no claims → phase 1
- Has sources only → phase 0

**Default topic:** the topic with the most sources.

### 2.3 Export Stats

```python
def export_stats(topic: str, graph: InsightGraph, output_dir: str) -> dict
```

Writes `{output_dir}/{topic}/stats.json`.

**Output format:**
```json
{
    "generated": "2026-03-06",
    "sources": 56,
    "source_types": {"web": 34, "pdf": 22},
    "total_segments": 5448,
    "canonical_claims": 164,
    "unique_claims": 112,
    "contradictions": 24
}
```

### 2.4 Export Sources

```python
def export_sources(topic: str, graph: InsightGraph, output_dir: str) -> list[dict]
```

Writes `{output_dir}/{topic}/sources.json`.

**Output format:**
```json
{
    "topic": "ea-for-ai",
    "updated": "2026-03-06",
    "sources": [
        {
            "id": "ea-for-ai:source-001",
            "title": "Enterprise AI Architecture Report",
            "url": "https://...",
            "author": "McKinsey",
            "date": "2025-06-15",
            "type": "web",
            "block_count": 45,
            "segment_count": 120
        }
    ]
}
```

### 2.5 CLI

```
python3 -m insight.exporter [--output docs/data] [--topic TOPIC]
```

- Default output: `docs/data/`
- If `--topic` specified, export only that topic
- Otherwise export all topics

---

## 3. Build Script Update

Replace `scripts/build.sh` to use the graph exporter:

```bash
python3 -m insight.exporter --output docs/data
```

The v1 build scripts remain in `scripts/` for backward compatibility but are no longer the primary build path.

---

## 4. Acceptance Criteria

### Exporter

- **AC-P1**: `export_topics()` produces a valid `topics.json` with all topics from the graph.
- **AC-P2**: `export_topics()` sets `default_topic` to the topic with the most sources.
- **AC-P3**: `export_topics()` determines phase from graph state (sources only → 0, segments → 1, claims → 3).
- **AC-P4**: `export_stats()` produces correct source count and type breakdown.
- **AC-P5**: `export_stats()` produces correct segment and claim counts (zero when not yet analyzed).
- **AC-P6**: `export_sources()` lists all sources with metadata.
- **AC-P7**: `export_sources()` includes `block_count` and `segment_count` per source.
- **AC-P8**: `export_all()` creates topic subdirectories and writes all files.
- **AC-P9**: Exported JSON is valid and parseable.

### Site Integration

- **AC-P10**: The existing site loads and renders correctly with graph-exported JSON.

---

## 5. Test Plan

### Unit Tests (`tests/unit/test_exporter.py`)

| Test | Acceptance Criteria |
|------|-------------------|
| Topics manifest shape | AC-P1, AC-P2 |
| Phase detection | AC-P3 |
| Stats counts | AC-P4, AC-P5 |
| Sources list | AC-P6, AC-P7 |
| Export all creates files | AC-P8, AC-P9 |
