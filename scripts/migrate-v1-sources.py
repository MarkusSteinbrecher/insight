"""
Migrate v1 source markdown files into the v2 knowledge graph.

Reads source-NNN.md files from a topic's sources/ directory,
parses frontmatter + body, creates Source nodes and ContentBlock nodes.

Usage:
    python3 scripts/migrate-v1-sources.py "EA for AI"
    python3 scripts/migrate-v1-sources.py --all
"""

import sys
import os
import re
import yaml
import hashlib
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from insight.graph import InsightGraph

TOPICS_DIR = Path(__file__).parent.parent / "knowledge-base" / "topics"


def parse_source_file(filepath):
    """Parse a v1 source markdown file into frontmatter dict + body sections."""
    text = filepath.read_text(encoding="utf-8")

    # Split frontmatter
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, None
    frontmatter = yaml.safe_load(parts[1])
    body = parts[2].strip()

    # Parse body into sections
    sections = {}
    current_section = "_preamble"
    current_lines = []

    for line in body.split("\n"):
        heading_match = re.match(r"^##\s+(.+)$", line)
        if heading_match:
            if current_lines:
                sections[current_section] = "\n".join(current_lines).strip()
            current_section = heading_match.group(1).strip()
            current_lines = []
        else:
            current_lines.append(line)
    if current_lines:
        sections[current_section] = "\n".join(current_lines).strip()

    return frontmatter, sections


def split_into_blocks(sections):
    """Split section content into paragraph-level blocks."""
    blocks = []
    for section_name, content in sections.items():
        if section_name == "_preamble" and not content:
            continue

        paragraphs = re.split(r"\n\n+", content)
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # Detect format
            if para.startswith(">"):
                fmt = "quote"
            elif para.startswith("- ") or para.startswith("* ") or re.match(r"^\d+\.\s", para):
                # Split list items into individual blocks
                items = re.split(r"\n(?=[-*]|\d+\.)", para)
                for item in items:
                    item = item.strip()
                    if item:
                        blocks.append({
                            "text": re.sub(r"^[-*]\s+|\d+\.\s+", "", item).strip(),
                            "format": "bullet",
                            "section": section_name,
                        })
                continue
            else:
                fmt = "prose"

            blocks.append({
                "text": para.lstrip("> ").strip(),
                "format": fmt,
                "section": section_name,
            })

    return blocks


def source_type_from_v1(v1_type):
    """Map v1 type field to v2 source_type."""
    mapping = {
        "article": "web",
        "paper": "pdf",
        "whitepaper": "pdf",
        "report": "pdf",
        "blog": "web",
        "video": "youtube",
    }
    return mapping.get(v1_type, "web")


def topic_slug(topic_name):
    """Convert topic directory name to a slug."""
    return topic_name.lower().replace(" ", "-")


def migrate_topic(graph, topic_dir):
    """Migrate all sources from a v1 topic directory."""
    topic_name = topic_dir.name
    slug = topic_slug(topic_name)
    sources_dir = topic_dir / "sources"

    if not sources_dir.exists():
        print(f"  No sources/ directory found, skipping")
        return 0

    source_files = sorted(sources_dir.glob("source-*.md"))
    if not source_files:
        print(f"  No source files found, skipping")
        return 0

    migrated = 0
    skipped = 0

    for filepath in source_files:
        source_id = filepath.stem  # e.g., "source-001"
        full_id = f"{slug}:{source_id}"  # e.g., "ea-for-ai:source-001"

        # Skip if already migrated
        if graph.source_exists(source_id=full_id):
            skipped += 1
            continue

        frontmatter, sections = parse_source_file(filepath)
        if frontmatter is None:
            print(f"  WARNING: Could not parse {filepath.name}, skipping")
            continue

        # Build full text for content hash
        full_text = filepath.read_text(encoding="utf-8")
        content_hash = hashlib.sha256(full_text.encode("utf-8")).hexdigest()

        # Create Source node
        graph.add_source(
            source_id=full_id,
            topic=slug,
            source_type=source_type_from_v1(frontmatter.get("type", "article")),
            title=frontmatter.get("title", filepath.stem),
            url=frontmatter.get("url", ""),
            author=frontmatter.get("author", ""),
            publication_date=str(frontmatter.get("date", "")),
            content_hash=content_hash,
            metadata={
                "v1_file": str(filepath.relative_to(TOPICS_DIR.parent.parent)),
                "relevance": frontmatter.get("relevance", 0),
                "tags": frontmatter.get("tags", []),
                "document": frontmatter.get("document", ""),
            }
        )

        # Create ContentBlock nodes
        blocks = split_into_blocks(sections)
        for i, block in enumerate(blocks):
            block_id = f"{full_id}:block-{i+1:03d}"
            graph.add_content_block(
                block_id=block_id,
                source_id=full_id,
                text=block["text"],
                position=i + 1,
                location_type="heading_path",
                location_value=block["section"],
                format=block["format"],
                section_path=block["section"],
            )

        migrated += 1
        block_count = len(blocks)
        print(f"  {source_id}: {frontmatter.get('title', '?')[:60]} ({block_count} blocks)")

    if skipped:
        print(f"  ({skipped} sources already in graph, skipped)")
    return migrated


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/migrate-v1-sources.py <topic-name|--all>")
        sys.exit(1)

    graph = InsightGraph()
    graph.init_schema()

    if sys.argv[1] == "--all":
        topic_dirs = sorted(d for d in TOPICS_DIR.iterdir() if d.is_dir())
    else:
        topic_name = sys.argv[1]
        topic_dir = TOPICS_DIR / topic_name
        if not topic_dir.exists():
            # Try case-insensitive match
            for d in TOPICS_DIR.iterdir():
                if d.is_dir() and d.name.lower() == topic_name.lower():
                    topic_dir = d
                    break
        if not topic_dir.exists():
            print(f"Topic directory not found: {topic_name}")
            sys.exit(1)
        topic_dirs = [topic_dir]

    total_migrated = 0
    for topic_dir in topic_dirs:
        print(f"\nMigrating: {topic_dir.name}")
        count = migrate_topic(graph, topic_dir)
        total_migrated += count

    # Summary
    print(f"\n--- Migration complete ---")
    for topic_dir in topic_dirs:
        slug = topic_slug(topic_dir.name)
        src_count = graph.count_sources(topic=slug)
        if src_count > 0:
            # Count blocks for this topic
            sources = graph.get_sources_by_topic(slug)
            block_count = sum(graph.count_content_blocks(s["source_id"]) for s in sources)
            print(f"  {slug}: {src_count} sources, {block_count} content blocks")

    graph.close()


if __name__ == "__main__":
    main()
