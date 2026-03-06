"""
Segmentation helpers for the Analyzer.

Provides graph operations for segmenting content blocks into typed segments.
Claude Code performs the actual analysis — these functions handle reading and writing.
"""

from __future__ import annotations

import json


def get_unsegmented_sources(topic: str, graph) -> list[dict]:
    """Return sources in a topic that have content blocks but no segments yet."""
    sources = graph.get_sources_by_topic(topic)
    unsegmented = []
    for source in sources:
        sid = source["source_id"]
        seg_count = graph.count_segments(source_id=sid)
        if seg_count == 0:
            unsegmented.append(source)
    return unsegmented


def get_source_content(source_id: str, graph) -> dict:
    """Return a source's metadata and content blocks for analysis."""
    source = graph.get_source(source_id)
    if not source:
        return None

    blocks = graph.get_content_blocks(source_id)
    return {
        "source_id": source["source_id"],
        "title": source["title"],
        "author": source["author"],
        "source_type": source["source_type"],
        "blocks": [
            {
                "block_id": b["block_id"],
                "text": b["text"],
                "format": b["format"],
                "section_path": b["section_path"],
                "position": b["position"],
            }
            for b in blocks
        ],
    }


def write_segments(source_id: str, segments: list[dict], graph) -> int:
    """
    Batch-write segments to the graph.

    Each segment dict must have: block_id, text, segment_type, position,
    section, source_format. Optional: metadata.

    Auto-generates segment IDs as {source_id}:seg-{NNN}.
    Returns count of segments written.
    """
    for i, seg in enumerate(segments, 1):
        segment_id = f"{source_id}:seg-{i:03d}"
        graph.add_segment(
            segment_id=segment_id,
            block_id=seg["block_id"],
            text=seg["text"],
            segment_type=seg["segment_type"],
            position=seg.get("position", i),
            section=seg.get("section", ""),
            source_format=seg.get("source_format", "prose"),
            metadata=seg.get("metadata"),
        )
    return len(segments)


def get_segmentation_stats(source_id: str, graph) -> dict:
    """Return composition breakdown for a segmented source."""
    segments = graph.get_segments(source_id)
    total = len(segments)
    if total == 0:
        return {"total_segments": 0, "composition": {}, "signal_ratio": 0.0}

    counts = {}
    for seg in segments:
        t = seg["segment_type"]
        counts[t] = counts.get(t, 0) + 1

    composition = {}
    for t, c in sorted(counts.items()):
        composition[t] = {"count": c, "pct": round(100.0 * c / total, 1)}

    noise_count = counts.get("noise", 0)
    signal_ratio = round(100.0 * (total - noise_count) / total, 1)

    return {
        "total_segments": total,
        "composition": composition,
        "signal_ratio": signal_ratio,
    }
