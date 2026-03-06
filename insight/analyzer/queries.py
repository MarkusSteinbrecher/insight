"""
Query helpers for the Analyzer.

High-level queries that combine multiple graph operations.
"""

from __future__ import annotations


def get_topic_summary(topic: str, graph) -> dict:
    """Return a high-level summary of a topic's analysis state."""
    sources = graph.get_sources_by_topic(topic)
    total_blocks = 0
    total_segments = 0
    segmented = 0
    unsegmented = 0

    for source in sources:
        sid = source["source_id"]
        total_blocks += graph.count_content_blocks(source_id=sid)
        seg_count = graph.count_segments(source_id=sid)
        total_segments += seg_count
        if seg_count > 0:
            segmented += 1
        else:
            unsegmented += 1

    total_claims = graph.count_claims(topic=topic)

    return {
        "topic": topic,
        "sources": len(sources),
        "content_blocks": total_blocks,
        "segments": total_segments,
        "claims": total_claims,
        "segmented_sources": segmented,
        "unsegmented_sources": unsegmented,
    }
