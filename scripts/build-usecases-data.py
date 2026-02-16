#!/usr/bin/env python3
"""Build use-cases.json from use-case-inventory.yaml.

Reads:
  - extractions/use-case-inventory.yaml

Usage:
  python3 scripts/build-usecases-data.py                # Process all topics
  python3 scripts/build-usecases-data.py ea-for-ai      # Process one topic

Output: docs/data/{topic-slug}/use-cases.json
"""

import glob
import json
import os
import re
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOPICS_DIR = os.path.join(ROOT, "knowledge-base", "topics")
OUTPUT_BASE = os.path.join(ROOT, "docs", "data")


def get_topic_slug(topic_dir):
    """Get the topic slug from _index.md frontmatter or directory name."""
    index_path = os.path.join(topic_dir, "_index.md")
    if os.path.exists(index_path):
        with open(index_path, "r") as f:
            content = f.read()
        match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        if match:
            try:
                fm = yaml.safe_load(match.group(1)) or {}
                slug = fm.get("slug", "")
                if slug:
                    return slug
            except yaml.YAMLError:
                pass
    return os.path.basename(topic_dir).lower().replace(" ", "-")


def build_usecases_for_topic(topic_dir):
    """Build use-cases JSON for a single topic. Returns True if output written."""
    slug = get_topic_slug(topic_dir)
    inventory_path = os.path.join(topic_dir, "extractions", "use-case-inventory.yaml")

    if not os.path.exists(inventory_path):
        return False

    with open(inventory_path, "r") as f:
        data = yaml.safe_load(f)

    if not data or "use_cases" not in data:
        return False

    use_cases = data["use_cases"]
    meta = data.get("meta", {})

    # Build category summary
    categories = {}
    maturity_counts = {"deployed": 0, "emerging": 0, "conceptual": 0}
    for uc in use_cases:
        cat = uc.get("category", "other")
        categories[cat] = categories.get(cat, 0) + 1
        mat = uc.get("maturity", "emerging")
        if mat in maturity_counts:
            maturity_counts[mat] += 1

    output = {
        "generated": "2026-02-16",
        "total_use_cases": len(use_cases),
        "sources_scanned": meta.get("sources_scanned", 0),
        "categories": categories,
        "maturity": maturity_counts,
        "use_cases": use_cases,
    }

    output_dir = os.path.join(OUTPUT_BASE, slug)
    output_file = os.path.join(output_dir, "use-cases.json")
    os.makedirs(output_dir, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2, default=str)

    print(f"  {output_file}")
    print(f"    Use cases: {len(use_cases)}")
    print(f"    Deployed: {maturity_counts['deployed']}, Emerging: {maturity_counts['emerging']}, Conceptual: {maturity_counts['conceptual']}")
    return True


def find_topic_dirs(slug=None):
    all_dirs = [
        d for d in glob.glob(os.path.join(TOPICS_DIR, "*"))
        if os.path.isdir(d) and os.path.exists(os.path.join(d, "_index.md"))
    ]
    if slug:
        matching = [d for d in all_dirs if get_topic_slug(d) == slug]
        if not matching:
            print(f"Topic '{slug}' not found.", file=sys.stderr)
            sys.exit(1)
        return matching
    return sorted(all_dirs)


def main():
    slug = sys.argv[1] if len(sys.argv) > 1 else None
    topic_dirs = find_topic_dirs(slug)

    if not topic_dirs:
        print("No topic directories found.", file=sys.stderr)
        sys.exit(1)

    print("Building use-cases data...")
    processed = 0
    for topic_dir in topic_dirs:
        topic_slug = get_topic_slug(topic_dir)
        inv_path = os.path.join(topic_dir, "extractions", "use-case-inventory.yaml")
        if not os.path.exists(inv_path):
            print(f"  Skipping {topic_slug} (no use-case-inventory.yaml)")
            continue
        print(f"  Topic: {topic_slug}")
        if build_usecases_for_topic(topic_dir):
            processed += 1

    if processed == 0:
        print("No topics with use-case-inventory.yaml found.", file=sys.stderr)


if __name__ == "__main__":
    main()
