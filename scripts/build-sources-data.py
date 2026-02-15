#!/usr/bin/env python3
"""Build sources.json from source markdown files.

Reads all knowledge-base/topics/*/sources/source-*.md files and produces
a unified JSON structure for the sources page.

Output: docs/data/sources.json
"""

import glob
import json
import os
import re
import sys

import markdown

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES_GLOB = os.path.join(
    ROOT, "knowledge-base", "topics", "*", "sources", "source-*.md"
)
INDEX_GLOB = os.path.join(ROOT, "knowledge-base", "topics", "*", "_index.md")
OUTPUT_DIR = os.path.join(ROOT, "docs", "data")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "sources.json")


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


def body_to_html(body):
    """Convert markdown body to HTML, excluding the Full Text section."""
    # Strip the "## Full Text" section (raw scraped content, too large for the site)
    body = re.sub(r"^## Full Text\s*\n.*", "", body, flags=re.DOTALL | re.MULTILINE)
    body = body.strip()
    if not body:
        return ""
    return markdown.markdown(body)


def get_topic_meta():
    """Read topic _index.md files to get topic metadata."""
    topics = {}
    for index_path in glob.glob(INDEX_GLOB):
        fm, _ = parse_frontmatter(index_path)
        parts = index_path.split(os.sep)
        topic_idx = parts.index("topics") + 1
        topic_slug = parts[topic_idx]
        topics[topic_slug] = {
            "title": fm.get("title", topic_slug),
            "status": fm.get("status", "unknown"),
            "updated": fm.get("updated", ""),
        }
    return topics


def build_sources_data():
    source_files = sorted(glob.glob(SOURCES_GLOB))
    if not source_files:
        print("No source markdown files found.", file=sys.stderr)
        sys.exit(1)

    topics = get_topic_meta()
    sources_by_topic = {}

    for filepath in source_files:
        parts = filepath.split(os.sep)
        topic_idx = parts.index("topics") + 1
        topic_slug = parts[topic_idx]

        if topic_slug not in sources_by_topic:
            sources_by_topic[topic_slug] = []

        fm, body = parse_frontmatter(filepath)
        source_id = os.path.basename(filepath).replace(".md", "")
        html = body_to_html(body)

        sources_by_topic[topic_slug].append({
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

    # For now, output the first (or only) topic
    # In future, could support multi-topic sources.json
    for topic_slug, sources in sources_by_topic.items():
        meta = topics.get(topic_slug, {})
        output = {
            "topic": meta.get("title", topic_slug),
            "status": meta.get("status", "unknown"),
            "updated": meta.get("updated", ""),
            "sources": sources,
        }

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(OUTPUT_FILE, "w") as f:
            json.dump(output, f, indent=2, default=str)

        print(f"Sources data written to {OUTPUT_FILE}")
        print(f"  Topic: {meta.get('title', topic_slug)}")
        print(f"  Sources: {len(sources)}")


if __name__ == "__main__":
    build_sources_data()
