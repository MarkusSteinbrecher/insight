#!/usr/bin/env python3
"""Build sources.json from source markdown files.

Reads all knowledge-base/topics/*/sources/source-*.md files and produces
a unified JSON structure for the sources page.

Usage:
  python3 scripts/build-sources-data.py                # Process all topics
  python3 scripts/build-sources-data.py ea-for-ai      # Process one topic

Output: docs/data/{topic-slug}/sources.json
"""

import glob
import json
import os
import re
import sys

import markdown
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOPICS_DIR = os.path.join(ROOT, "knowledge-base", "topics")
OUTPUT_BASE = os.path.join(ROOT, "docs", "data")


def parse_frontmatter(filepath):
    """Parse YAML frontmatter from a markdown file."""
    with open(filepath, "r") as f:
        content = f.read()

    # Match YAML frontmatter between --- delimiters
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return {}, content

    fm = {}
    for line in match.group(1).split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("- "):
            # Part of a list — skip (handled below)
            continue
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if val:
                fm[key] = val

    # Parse tags list
    tags = []
    in_tags = False
    for line in match.group(1).split("\n"):
        stripped = line.strip()
        if stripped.startswith("tags:"):
            in_tags = True
            continue
        if in_tags:
            if stripped.startswith("- "):
                tags.append(stripped[2:].strip().strip('"').strip("'"))
            else:
                in_tags = False
    if tags:
        fm["tags"] = tags

    # Return frontmatter and body (everything after frontmatter)
    body = content[match.end():].strip()
    return fm, body


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


def get_topic_slug(topic_dir):
    """Get the topic slug from _index.md frontmatter or directory name."""
    index_path = os.path.join(topic_dir, "_index.md")
    if os.path.exists(index_path):
        fm = parse_frontmatter_yaml(index_path)
        slug = fm.get("slug", "")
        if slug:
            return slug
    return os.path.basename(topic_dir).lower().replace(" ", "-")


def body_to_html(body):
    """Convert markdown body to HTML, excluding the Full Text section."""
    # Strip the "## Full Text" section (raw scraped content, too large for the site)
    body = re.sub(r"^## Full Text\s*\n.*", "", body, flags=re.DOTALL | re.MULTILINE)
    body = body.strip()
    if not body:
        return ""
    return markdown.markdown(body)


def get_topic_meta(topic_dir):
    """Read topic _index.md to get topic metadata."""
    index_path = os.path.join(topic_dir, "_index.md")
    if not os.path.exists(index_path):
        return {}
    fm, _ = parse_frontmatter(index_path)
    return {
        "title": fm.get("title", os.path.basename(topic_dir)),
        "status": fm.get("status", "unknown"),
        "updated": fm.get("updated", ""),
    }


def build_sources_for_topic(topic_dir):
    """Build sources JSON for a single topic directory. Returns True if output was written."""
    slug = get_topic_slug(topic_dir)
    source_files = sorted(glob.glob(os.path.join(topic_dir, "sources", "source-*.md")))

    if not source_files:
        return False

    meta = get_topic_meta(topic_dir)
    sources = []

    for filepath in source_files:
        fm, body = parse_frontmatter(filepath)
        source_id = os.path.basename(filepath).replace(".md", "")
        html = body_to_html(body)

        sources.append({
            "id": source_id,
            "title": fm.get("title", source_id),
            "url": fm.get("url", ""),
            "author": fm.get("author", "Unknown"),
            "date": fm.get("date", ""),
            "type": fm.get("type", ""),
            "relevance": int(fm.get("relevance", 3)),
            "tags": fm.get("tags", []),
            "body_html": html,
        })

    output = {
        "topic": meta.get("title", slug),
        "status": meta.get("status", "unknown"),
        "updated": meta.get("updated", ""),
        "sources": sources,
    }

    output_dir = os.path.join(OUTPUT_BASE, slug)
    output_file = os.path.join(output_dir, "sources.json")
    os.makedirs(output_dir, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2, default=str)

    print(f"  {output_file}")
    print(f"    Topic: {meta.get('title', slug)}")
    print(f"    Sources: {len(sources)}")
    return True


def find_topic_dirs(slug=None):
    """Find topic directories, optionally filtering by slug."""
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


def build_sources_data():
    slug = sys.argv[1] if len(sys.argv) > 1 else None
    topic_dirs = find_topic_dirs(slug)

    if not topic_dirs:
        print("No topic directories found.", file=sys.stderr)
        sys.exit(1)

    print("Building sources data...")
    processed = 0
    for topic_dir in topic_dirs:
        topic_slug = get_topic_slug(topic_dir)
        print(f"  Topic: {topic_slug}")
        if build_sources_for_topic(topic_dir):
            processed += 1

    if processed == 0:
        print("No topics with source files found.", file=sys.stderr)


if __name__ == "__main__":
    build_sources_data()
