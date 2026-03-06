"""
Graph → JSON exporter for the static site.

Reads from the knowledge graph and writes JSON files that the
docs/ site renders. Replaces the v1 build scripts.
"""

from __future__ import annotations

import json
import os
from datetime import date


def _get_all_topics(graph) -> list[str]:
    """Get distinct topic slugs from Source nodes."""
    result = graph.conn.execute(
        "MATCH (s:Source) RETURN DISTINCT s.topic ORDER BY s.topic"
    )
    topics = []
    while result.has_next():
        topics.append(result.get_next()[0])
    return topics


def _determine_phase(topic: str, graph) -> int:
    """Determine topic phase from graph state."""
    claims = graph.count_claims(topic=topic)
    if claims > 0:
        return 3

    segments = graph.count_segments()
    # Check if any segments belong to sources in this topic
    sources = graph.get_sources_by_topic(topic)
    for s in sources:
        if graph.count_segments(source_id=s["source_id"]) > 0:
            return 1

    return 0


def _topic_title(slug: str, kb_path: str = None) -> str:
    """Derive a display title from a topic slug or _index.md."""
    if kb_path:
        # Search for matching topic directory
        kb = os.path.join(kb_path, "topics")
        if os.path.isdir(kb):
            for d in os.listdir(kb):
                index_path = os.path.join(kb, d, "_index.md")
                if os.path.isfile(index_path):
                    with open(index_path) as f:
                        for line in f:
                            if line.startswith("slug:") and slug in line:
                                # Found the right topic, look for title
                                f.seek(0)
                                for l2 in f:
                                    if l2.startswith("title:"):
                                        return l2.split(":", 1)[1].strip().strip('"')
                                break
    return slug.replace("-", " ").title()


def export_topics(graph, output_dir: str, kb_path: str = None) -> list[dict]:
    """Export topics.json manifest."""
    topics = _get_all_topics(graph)
    topic_list = []
    max_sources = 0
    default_topic = None

    for slug in topics:
        source_count = graph.count_sources(topic=slug)
        phase = _determine_phase(slug, graph)
        topic_list.append({
            "slug": slug,
            "title": _topic_title(slug, kb_path),
            "phase": phase,
            "source_count": source_count,
        })
        if source_count > max_sources:
            max_sources = source_count
            default_topic = slug

    manifest = {
        "topics": topic_list,
        "default_topic": default_topic or (topics[0] if topics else ""),
    }

    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, "topics.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    return topic_list


def export_stats(topic: str, graph, output_dir: str) -> dict:
    """Export {topic}/stats.json with aggregated statistics."""
    sources = graph.get_sources_by_topic(topic)
    type_counts = {}
    for s in sources:
        t = s["source_type"]
        type_counts[t] = type_counts.get(t, 0) + 1

    total_segments = 0
    for s in sources:
        total_segments += graph.count_segments(source_id=s["source_id"])

    claims = graph.get_claims_by_topic(topic)
    canonical = sum(1 for c in claims if c["claim_category"] == "canonical")
    unique = sum(1 for c in claims if c["claim_category"] == "unique")
    contradiction = sum(1 for c in claims if c["claim_category"] == "contradiction")

    stats = {
        "generated": str(date.today()),
        "sources": len(sources),
        "source_types": type_counts,
        "total_segments": total_segments,
        "canonical_claims": canonical,
        "unique_claims": unique,
        "contradictions": contradiction,
    }

    topic_dir = os.path.join(output_dir, topic)
    os.makedirs(topic_dir, exist_ok=True)
    with open(os.path.join(topic_dir, "stats.json"), "w") as f:
        json.dump(stats, f, indent=2)

    return stats


def export_sources(topic: str, graph, output_dir: str) -> list[dict]:
    """Export {topic}/sources.json with source list and metadata."""
    sources = graph.get_sources_by_topic(topic)
    source_list = []

    for s in sources:
        sid = s["source_id"]
        block_count = graph.count_content_blocks(source_id=sid)
        segment_count = graph.count_segments(source_id=sid)

        source_list.append({
            "id": sid,
            "title": s["title"],
            "url": s["url"],
            "author": s["author"],
            "date": s.get("publication_date", ""),
            "type": s["source_type"],
            "block_count": block_count,
            "segment_count": segment_count,
        })

    output = {
        "topic": topic,
        "updated": str(date.today()),
        "sources": source_list,
    }

    topic_dir = os.path.join(output_dir, topic)
    os.makedirs(topic_dir, exist_ok=True)
    with open(os.path.join(topic_dir, "sources.json"), "w") as f:
        json.dump(output, f, indent=2)

    return source_list


def export_all(graph, output_dir: str, kb_path: str = None) -> dict:
    """Export all topic data to the output directory."""
    topic_list = export_topics(graph, output_dir, kb_path=kb_path)
    total_sources = 0

    for topic_info in topic_list:
        slug = topic_info["slug"]
        export_stats(slug, graph, output_dir)
        sources = export_sources(slug, graph, output_dir)
        total_sources += len(sources)

    return {
        "topics": len(topic_list),
        "sources": total_sources,
    }
