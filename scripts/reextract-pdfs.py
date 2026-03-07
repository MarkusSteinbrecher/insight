"""
Re-extract PDF sources from actual documents using the new PDF collector.

Replaces the v1 migration data (which only extracted source notes markdown)
with full content extraction from the actual PDFs.

Usage:
    python3 scripts/reextract-pdfs.py
    python3 scripts/reextract-pdfs.py --source-id ea-for-ai:source-001
    python3 scripts/reextract-pdfs.py --dry-run
"""

import sys
import os
import json
import yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from pathlib import Path
from insight.graph import InsightGraph
from insight.collector.pdf import extract_pdf_blocks, _split_compound_blocks

ROOT = Path(__file__).parent.parent
KB_DIR = ROOT / "knowledge-base" / "topics"


def find_topic_dir(topic_slug):
    """Find actual directory name for a topic slug."""
    for d in KB_DIR.iterdir():
        if d.is_dir():
            index = d / "_index.md"
            if index.exists():
                with open(index) as f:
                    for line in f:
                        if line.startswith("slug:") and topic_slug in line:
                            return d
    return None


def get_document_path(source_id, graph, topic_dir):
    """Find the PDF file path for a source."""
    source = graph.get_source(source_id)
    if not source:
        return None

    # Check metadata for document_path
    meta = {}
    if source.get("metadata"):
        try:
            meta = json.loads(source["metadata"]) if isinstance(source["metadata"], str) else source["metadata"]
        except (json.JSONDecodeError, TypeError):
            pass

    doc_path = meta.get("document", meta.get("document_path", ""))
    if doc_path:
        # Resolve relative to topic dir
        full_path = topic_dir / doc_path
        if full_path.exists():
            return str(full_path)

    # Also check the source markdown file for document field
    file_part = source_id.split(":")[-1]  # "source-001"
    md_path = topic_dir / "sources" / f"{file_part}.md"
    if md_path.exists():
        with open(md_path) as f:
            text = f.read()
        if text.startswith("---"):
            end = text.find("---", 3)
            if end != -1:
                front = yaml.safe_load(text[3:end])
                if front and front.get("document"):
                    full_path = topic_dir / front["document"]
                    if full_path.exists():
                        return str(full_path)

    return None


def delete_blocks(source_id, graph):
    """Delete all ContentBlocks (and connected edges) for a source."""
    graph.conn.execute(
        "MATCH (b:ContentBlock) WHERE b.block_id STARTS WITH $prefix DETACH DELETE b",
        parameters={"prefix": f"{source_id}:block-"}
    )


def reextract_source(source_id, graph, topic_dir, dry_run=False):
    """Re-extract a single PDF source."""
    source = graph.get_source(source_id)
    if not source:
        print(f"  Source not found: {source_id}")
        return False

    if source["source_type"] != "pdf":
        return False

    doc_path = get_document_path(source_id, graph, topic_dir)
    if not doc_path:
        print(f"  No PDF found for {source_id} ({source['title'][:50]})")
        return False

    if dry_run:
        # Just test extraction without writing
        blocks, meta = extract_pdf_blocks(doc_path)
        blocks = _split_compound_blocks([b for b in blocks if b["format"] != "figure"])
        figures = [b for b in blocks if b["format"] == "figure"]
        old_count = graph.count_content_blocks(source_id)
        print(f"  {source_id}: {old_count} old blocks → {len(blocks)} text + {len(figures)} images from PDF")
        return True

    # Image output directory
    image_dir = str(ROOT / "data" / "images" / source_id.replace(":", "/"))

    # Extract from actual PDF
    blocks, meta = extract_pdf_blocks(doc_path, image_dir=image_dir)
    text_blocks = [b for b in blocks if b["format"] != "figure"]
    figure_blocks = [b for b in blocks if b["format"] == "figure"]
    text_blocks = _split_compound_blocks(text_blocks)
    all_blocks = text_blocks + figure_blocks

    if not all_blocks:
        print(f"  No content extracted from {doc_path}")
        return False

    # Delete old blocks
    old_count = graph.count_content_blocks(source_id)
    delete_blocks(source_id, graph)

    # Write new blocks
    for i, block in enumerate(all_blocks):
        block_id = f"{source_id}:block-{i+1:03d}"
        graph.add_content_block(
            block_id=block_id,
            source_id=source_id,
            text=block["text"],
            position=i + 1,
            location_type="heading_path" if block["format"] != "figure" else "page",
            location_value=block.get("section_path", ""),
            format=block["format"],
            section_path=block.get("section_path", ""),
            image_path=block.get("image_path", ""),
        )

    # Update source metadata with document_path
    import hashlib
    all_text = "\n".join(b["text"] for b in all_blocks)
    new_hash = hashlib.sha256(all_text.encode("utf-8")).hexdigest()
    graph.conn.execute(
        "MATCH (s:Source) WHERE s.source_id = $sid "
        "SET s.content_hash = $hash",
        parameters={"sid": source_id, "hash": new_hash}
    )

    print(f"  {source_id}: {old_count} → {len(text_blocks)} text + {len(figure_blocks)} images ({sum(len(b['text']) for b in all_blocks):,} chars)")
    return True


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Re-extract PDF sources from actual documents")
    parser.add_argument("--source-id", help="Re-extract a single source")
    parser.add_argument("--topic", default="ea-for-ai", help="Topic slug")
    parser.add_argument("--dry-run", action="store_true", help="Show what would change without writing")
    args = parser.parse_args()

    graph = InsightGraph()
    graph.init_schema()

    topic_dir = find_topic_dir(args.topic)
    if not topic_dir:
        print(f"Topic directory not found for: {args.topic}")
        sys.exit(1)

    print(f"Topic: {args.topic} ({topic_dir.name})")
    if args.dry_run:
        print("DRY RUN — no changes will be made\n")

    if args.source_id:
        reextract_source(args.source_id, graph, topic_dir, dry_run=args.dry_run)
    else:
        sources = graph.get_sources_by_topic(args.topic)
        pdf_sources = [s for s in sources if s["source_type"] == "pdf"]
        print(f"PDF sources: {len(pdf_sources)}\n")

        success = 0
        skipped = 0
        for s in pdf_sources:
            result = reextract_source(s["source_id"], graph, topic_dir, dry_run=args.dry_run)
            if result:
                success += 1
            else:
                skipped += 1

        print(f"\nDone. {success} re-extracted, {skipped} skipped.")

    graph.close()


if __name__ == "__main__":
    main()
