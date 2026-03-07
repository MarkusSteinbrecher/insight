#!/usr/bin/env python3
"""Load analysis results (segments, claims) into the knowledge graph.

Reads raw YAML files (segments) and claim-alignment.yaml (claims),
creates Segment and Claim nodes in KuzuDB with proper edges:
  ContentBlock ← SEGMENTED_FROM ← Segment → SUPPORTS → Claim

This bridges the file-based analysis pipeline with the graph database,
enabling traceability queries like "which claims does this block support?"

Usage:
    python3 scripts/load-analysis-to-graph.py ea-for-ai
    python3 scripts/load-analysis-to-graph.py ea-for-ai --dry-run
"""

import argparse
import glob
import os
import re
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOPICS_DIR = os.path.join(ROOT, "knowledge-base", "topics")


def find_topic_dir(slug):
    for name in os.listdir(TOPICS_DIR):
        path = os.path.join(TOPICS_DIR, name)
        if not os.path.isdir(path):
            continue
        index_path = os.path.join(path, "_index.md")
        if os.path.exists(index_path):
            with open(index_path) as f:
                for line in f:
                    if line.startswith("slug:") and slug in line:
                        return path
    return None


def clear_analysis_data(graph, topic):
    """Remove existing Segment and Claim nodes for a topic."""
    # Delete claims
    graph.conn.execute(
        "MATCH (c:Claim) WHERE c.topic = $topic DETACH DELETE c",
        parameters={"topic": topic}
    )
    # Delete segments linked to this topic's sources
    graph.conn.execute(
        """
        MATCH (s:Source)-[:CONTAINS]->(b:ContentBlock)<-[:SEGMENTED_FROM]-(sg:Segment)
        WHERE s.topic = $topic
        DETACH DELETE sg
        """,
        parameters={"topic": topic}
    )


def find_block_for_segment(graph, topic, source_num, seg_position, seg_text):
    """Find the ContentBlock that best matches a segment.

    Strategy: segments were created from blocks. A segment at position P
    in source-NNN came from one of that source's content blocks.
    We match by finding the block whose text contains the segment text,
    or by position mapping.
    """
    source_id = f"{topic}:source-{source_num}"
    blocks = graph.get_content_blocks(source_id)
    if not blocks:
        return None

    # Try exact text containment
    seg_clean = seg_text[:100].strip()
    for b in blocks:
        if seg_clean in b.get("text", ""):
            return b["block_id"]

    # Try first 50 chars
    seg_short = seg_text[:50].strip()
    for b in blocks:
        if seg_short in b.get("text", ""):
            return b["block_id"]

    # Fallback: map by rough position ratio
    if blocks:
        ratio = seg_position / max(seg_position, 1)
        idx = min(int(ratio * len(blocks)), len(blocks) - 1)
        return blocks[idx]["block_id"]

    return None


def load_segments(graph, topic, raw_dir, dry_run=False):
    """Load segments from raw YAML files into the graph."""
    raw_files = sorted(glob.glob(os.path.join(raw_dir, "source-*-raw.yaml")))
    total = 0
    linked = 0

    for filepath in raw_files:
        with open(filepath) as f:
            data = yaml.safe_load(f)
        if not data:
            continue

        source_id_raw = data.get("source_id", "")
        # source_id in raw files is like "source-001", need full "ea-for-ai:source-001"
        num_match = re.search(r"source-(\d+)", source_id_raw)
        if not num_match:
            continue
        source_num = num_match.group(1)
        full_source_id = f"{topic}:source-{source_num}"

        segments = data.get("segments", [])
        if not segments:
            continue

        for seg in segments:
            seg_id = f"{full_source_id}:{seg['id']}"
            seg_type = seg.get("type", "context")
            seg_text = seg.get("text", "")
            seg_section = seg.get("section", "")
            seg_position = seg.get("position", 0)
            seg_format = seg.get("source_format", "prose")

            # Skip noise segments
            if seg_type == "noise":
                continue

            # Find matching block
            block_id = find_block_for_segment(
                graph, topic, source_num, seg_position, seg_text
            )

            if dry_run:
                total += 1
                if block_id:
                    linked += 1
                continue

            if block_id:
                try:
                    graph.add_segment(
                        segment_id=seg_id,
                        block_id=block_id,
                        text=seg_text,
                        segment_type=seg_type,
                        position=seg_position,
                        section=seg_section,
                        source_format=seg_format,
                    )
                    total += 1
                    linked += 1
                except Exception:
                    # Duplicate or other error — skip
                    pass

    return total, linked


def load_claims(graph, topic, extractions_dir, dry_run=False):
    """Load claims from claim-alignment.yaml into the graph."""
    alignment_path = os.path.join(extractions_dir, "claim-alignment.yaml")
    if not os.path.exists(alignment_path):
        print("  No claim-alignment.yaml found")
        return 0, 0

    with open(alignment_path) as f:
        data = yaml.safe_load(f)

    canonical = data.get("canonical_claims", [])
    total_claims = 0
    total_links = 0

    for claim in canonical:
        claim_id = f"{topic}:{claim['id']}"
        theme = claim.get("theme", "")
        summary = claim.get("summary", "")
        claim_type = claim.get("claim_type", "")
        strength = claim.get("strength", "")

        if dry_run:
            total_claims += 1
            total_links += len(claim.get("source_segments", []))
            continue

        try:
            graph.add_claim(
                claim_id=claim_id,
                topic=topic,
                claim_category=theme,
                theme=theme,
                summary=summary,
                claim_type=claim_type,
                strength=strength,
            )
            total_claims += 1
        except Exception:
            continue

        # Link segments to claims
        for seg_ref in claim.get("source_segments", []):
            src_id = seg_ref.get("source_id", "")
            seg_id_short = seg_ref.get("seg_id", "")
            if src_id and seg_id_short:
                full_seg_id = f"{src_id}:{seg_id_short}"
                try:
                    graph.link_segment_to_claim(full_seg_id, claim_id)
                    total_links += 1
                except Exception:
                    pass

    return total_claims, total_links


def main():
    parser = argparse.ArgumentParser(description="Load analysis into graph")
    parser.add_argument("topic", help="Topic slug")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    from insight.graph import InsightGraph

    topic_dir = find_topic_dir(args.topic)
    if not topic_dir:
        print(f"Topic not found: {args.topic}")
        sys.exit(1)

    raw_dir = os.path.join(topic_dir, "raw")
    extractions_dir = os.path.join(topic_dir, "extractions")

    graph = InsightGraph()
    graph.init_schema()

    if not args.dry_run:
        print("Clearing existing analysis data...")
        clear_analysis_data(graph, args.topic)

    print("Loading segments...")
    seg_total, seg_linked = load_segments(graph, args.topic, raw_dir, args.dry_run)
    print(f"  Segments: {seg_total} created, {seg_linked} linked to blocks")

    print("Loading claims...")
    claim_total, claim_links = load_claims(graph, args.topic, extractions_dir, args.dry_run)
    print(f"  Claims: {claim_total} created, {claim_links} segment-claim links")

    if not args.dry_run:
        # Verify
        print(f"\nGraph totals:")
        print(f"  Segments: {graph.count_segments()}")
        print(f"  Claims: {graph.count_claims(args.topic)}")

    graph.close()
    prefix = "DRY RUN — " if args.dry_run else ""
    print(f"\n{prefix}Done.")


if __name__ == "__main__":
    main()
