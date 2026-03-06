"""
Claim alignment helpers for the Analyzer.

Provides graph operations for writing claim alignment results.
Claude Code performs the actual alignment — these functions handle graph writes.
"""

from __future__ import annotations


# Default segment types relevant for claim alignment
CLAIM_TYPES = ["claim", "recommendation", "statistic", "evidence"]


def get_claim_segments(topic: str, graph, types: list[str] = None) -> list[dict]:
    """
    Return segments of specified types across all sources in a topic, grouped by source.

    Default types: claim, recommendation, statistic, evidence.
    """
    if types is None:
        types = CLAIM_TYPES

    sources = graph.get_sources_by_topic(topic)
    result = []

    for source in sources:
        sid = source["source_id"]
        source_segments = []
        for t in types:
            segs = graph.get_segments_by_type(sid, t)
            source_segments.extend(segs)

        if source_segments:
            # Sort by position
            source_segments.sort(key=lambda s: s["position"])
            result.append({
                "source_id": sid,
                "title": source["title"],
                "author": source["author"],
                "segments": [
                    {
                        "segment_id": s["segment_id"],
                        "text": s["text"],
                        "segment_type": s["segment_type"],
                        "section": s["section"],
                    }
                    for s in source_segments
                ],
            })

    return result


def write_claims(topic: str, claims: list[dict], graph) -> int:
    """
    Batch-write claims and link supporting segments.

    Each claim dict must have: claim_id, claim_category, theme, summary.
    Optional: claim_type, strength, description, segment_ids, metadata.

    Returns count of claims written.
    """
    for claim in claims:
        graph.add_claim(
            claim_id=claim["claim_id"],
            topic=topic,
            claim_category=claim["claim_category"],
            theme=claim["theme"],
            summary=claim["summary"],
            claim_type=claim.get("claim_type", ""),
            strength=claim.get("strength", ""),
            description=claim.get("description", ""),
            metadata=claim.get("metadata"),
        )

        for seg_id in claim.get("segment_ids", []):
            graph.link_segment_to_claim(seg_id, claim["claim_id"])

    return len(claims)


def write_contradictions(contradictions: list[dict], graph) -> int:
    """
    Link pairs of claims that contradict each other.

    Each dict must have: claim_id_1, claim_id_2, description.
    Returns count of contradictions written.
    """
    for ct in contradictions:
        graph.link_contradiction(
            ct["claim_id_1"],
            ct["claim_id_2"],
            description=ct.get("description", ""),
        )
    return len(contradictions)


def get_alignment_stats(topic: str, graph) -> dict:
    """Return claim alignment statistics for a topic."""
    claims = graph.get_claims_by_topic(topic)

    canonical = sum(1 for c in claims if c["claim_category"] == "canonical")
    unique = sum(1 for c in claims if c["claim_category"] == "unique")
    contradiction = sum(1 for c in claims if c["claim_category"] == "contradiction")

    # Count linked segments
    total_linked = 0
    source_ids = set()
    for claim in claims:
        supporting = graph.get_supporting_segments(claim["claim_id"])
        total_linked += len(supporting)
        for seg in supporting:
            # Extract source_id from segment_id (format: source_id:seg-NNN)
            parts = seg["segment_id"].rsplit(":seg-", 1)
            if parts:
                source_ids.add(parts[0])

    return {
        "total_claims": len(claims),
        "canonical": canonical,
        "unique": unique,
        "contradiction": contradiction,
        "total_segments_linked": total_linked,
        "sources_covered": len(source_ids),
    }
