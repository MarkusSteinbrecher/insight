#!/usr/bin/env python3
"""Link Extract nodes to Claim nodes using claim-alignment.yaml references.

Reads claim-alignment.yaml, matches source_segments references to Extract nodes
by finding extracts whose text matches the segment text.

Usage:
    python3 scripts/link-extracts-to-claims.py ea-for-ai
    python3 scripts/link-extracts-to-claims.py ea-for-ai --dry-run
"""

import argparse
import os
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


def find_extract_for_segment(graph, source_id, seg_text):
    """Find the Extract that best matches a segment's text."""
    extracts = graph.get_extracts(source_id)
    if not extracts:
        return None

    # Try exact text containment (first 100 chars)
    seg_clean = seg_text[:100].strip()
    for e in extracts:
        if seg_clean in e.get("text", ""):
            return e["extract_id"]

    # Try first 50 chars
    seg_short = seg_text[:50].strip()
    for e in extracts:
        if seg_short in e.get("text", ""):
            return e["extract_id"]

    return None


def main():
    parser = argparse.ArgumentParser(description="Link extracts to claims")
    parser.add_argument("topic", help="Topic slug")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    from insight.graph import InsightGraph

    topic_dir = find_topic_dir(args.topic)
    if not topic_dir:
        print(f"Topic not found: {args.topic}")
        sys.exit(1)

    alignment_path = os.path.join(topic_dir, "extractions", "claim-alignment.yaml")
    if not os.path.exists(alignment_path):
        print(f"No claim-alignment.yaml found at {alignment_path}")
        sys.exit(1)

    with open(alignment_path) as f:
        data = yaml.safe_load(f)

    graph = InsightGraph()
    graph.init_schema()

    # Load segment text from raw files to match against extracts
    raw_dir = os.path.join(topic_dir, "raw")
    seg_text_map = {}  # (source_id, seg_id) → text
    if os.path.isdir(raw_dir):
        for fname in os.listdir(raw_dir):
            if not fname.endswith("-raw.yaml"):
                continue
            with open(os.path.join(raw_dir, fname)) as f:
                raw = yaml.safe_load(f)
            if not raw:
                continue
            raw_sid = raw.get("source_id", "")
            for seg in raw.get("segments", []):
                seg_text_map[(raw_sid, seg["id"])] = seg.get("text", "")

    canonical = data.get("canonical_claims", [])
    total_links = 0
    failed_links = 0

    for claim in canonical:
        claim_id = f"{args.topic}:{claim['id']}"

        for seg_ref in claim.get("source_segments", []):
            src_id = seg_ref.get("source_id", "")
            seg_id = seg_ref.get("seg_id", "")

            # Get the segment text from raw files
            seg_text = seg_text_map.get((src_id, seg_id), "")
            if not seg_text:
                # Try with topic prefix
                seg_text = seg_text_map.get((f"{args.topic}:{src_id}", seg_id), "")

            if not seg_text:
                failed_links += 1
                continue

            # Find matching extract
            extract_id = find_extract_for_segment(graph, src_id, seg_text)
            if not extract_id:
                failed_links += 1
                continue

            if args.dry_run:
                print(f"  {claim['id']} ← {extract_id}")
                total_links += 1
            else:
                try:
                    graph.link_extract_to_claim(extract_id, claim_id)
                    total_links += 1
                except Exception:
                    failed_links += 1

    print(f"Links created: {total_links}")
    print(f"Failed matches: {failed_links}")

    graph.close()
    prefix = "DRY RUN — " if args.dry_run else ""
    print(f"\n{prefix}Done.")


if __name__ == "__main__":
    main()
