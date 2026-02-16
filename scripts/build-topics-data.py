#!/usr/bin/env python3
"""Build topics.json from knowledge base topic directories.

Scans all topic directories under knowledge-base/topics/ and produces a
unified JSON structure listing each topic with key metadata.

Output: docs/data/topics.json
"""

import glob
import json
import os
import re
import sys
from datetime import date

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOPICS_DIR = os.path.join(ROOT, "knowledge-base", "topics")
OUTPUT_DIR = os.path.join(ROOT, "docs", "data")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "topics.json")


def parse_frontmatter_yaml(filepath):
    """Parse YAML frontmatter from a markdown file using yaml.safe_load."""
    with open(filepath, "r") as f:
        content = f.read()

    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return {}

    try:
        return yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        return {}


def count_sources(topic_dir):
    """Count source-*.md files in the sources/ subdirectory."""
    return len(glob.glob(os.path.join(topic_dir, "sources", "source-*.md")))


def count_insights(topic_dir):
    """Count insight-*.md files in the insights/ subdirectory."""
    return len(glob.glob(os.path.join(topic_dir, "insights", "insight-*.md")))


def count_canonical_claims(topic_dir):
    """Read canonical claim count from claim-alignment.yaml meta block."""
    path = os.path.join(topic_dir, "extractions", "claim-alignment.yaml")
    if not os.path.exists(path):
        return 0
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    if data and "meta" in data:
        return data["meta"].get("canonical_claims", 0)
    return 0


def build_topics_data():
    topic_dirs = sorted([
        d for d in glob.glob(os.path.join(TOPICS_DIR, "*"))
        if os.path.isdir(d) and os.path.exists(os.path.join(d, "_index.md"))
    ])

    if not topic_dirs:
        print("No topic directories found.", file=sys.stderr)
        sys.exit(1)

    topics = []
    for topic_dir in topic_dirs:
        index_path = os.path.join(topic_dir, "_index.md")
        fm = parse_frontmatter_yaml(index_path)

        dir_name = os.path.basename(topic_dir)
        slug = fm.get("slug", dir_name.lower().replace(" ", "-"))
        title = fm.get("title", dir_name)
        status = fm.get("status", "phase-0")
        phase = fm.get("phase", 0)
        updated = fm.get("updated", "")

        # Prefer frontmatter counts, fall back to filesystem counts
        source_count = fm.get("source_count", count_sources(topic_dir))
        insight_count = fm.get("insight_count", count_insights(topic_dir))
        canonical_claims = fm.get("canonical_claims", count_canonical_claims(topic_dir))

        entry = {
            "slug": slug,
            "title": title,
            "status": status,
            "phase": phase,
            "source_count": source_count,
            "updated": str(updated) if updated else "",
        }

        # Only include non-zero optional counts
        if insight_count:
            entry["insight_count"] = insight_count
        if canonical_claims:
            entry["canonical_claims"] = canonical_claims

        topics.append(entry)

    # Determine default topic: highest phase first, then most sources
    default_topic = max(
        topics,
        key=lambda t: (t.get("phase", 0), t.get("source_count", 0))
    )

    output = {
        "topics": topics,
        "default_topic": default_topic["slug"],
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2, default=str)

    print(f"Topics data written to {OUTPUT_FILE}")
    for t in topics:
        print(f"  {t['slug']}: phase {t['phase']}, {t['source_count']} sources")


if __name__ == "__main__":
    build_topics_data()
