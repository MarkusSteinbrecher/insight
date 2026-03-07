"""
Fresh extraction of all sources for a topic.

Wipes ALL existing graph data (sources, blocks, segments, claims)
and re-extracts everything from scratch using the proper collectors.

Sources are read from the knowledge-base markdown files. Source type
is determined by:
  1. Local PDF file referenced in frontmatter → pdf
  2. YouTube URL → youtube
  3. Everything else → web

Usage:
    python3 scripts/fresh-extract.py --topic ea-for-ai
    python3 scripts/fresh-extract.py --topic ea-for-ai --dry-run
    python3 scripts/fresh-extract.py --topic ea-for-ai --source-id ea-for-ai:source-005
"""

import sys
import os
import json
import re
import yaml
import traceback
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from insight.graph import InsightGraph

ROOT = Path(__file__).parent.parent
KB_DIR = ROOT / "knowledge-base" / "topics"
LOG_FILE = ROOT / "data" / "extraction-log.json"


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


def read_source_markdown(md_path):
    """Read a source markdown file and return frontmatter + body."""
    with open(md_path) as f:
        text = f.read()
    if not text.startswith("---"):
        return {}, text
    end = text.find("---", 3)
    if end == -1:
        return {}, text
    front = yaml.safe_load(text[3:end])
    body = text[end + 3:].strip()
    return front or {}, body


def determine_source_type(frontmatter, topic_dir):
    """Determine the correct source_type based on URL and local files."""
    url = frontmatter.get("url", "")

    # Check for local PDF document
    doc_path = frontmatter.get("document", "")
    if doc_path:
        full_path = topic_dir / doc_path
        if full_path.exists():
            return "pdf", str(full_path)

    # YouTube
    if re.search(r"(youtube\.com/watch|youtu\.be/)", url):
        return "youtube", url

    # URL ending in .pdf — treat as web-downloadable PDF
    if url.lower().endswith(".pdf"):
        return "pdf_url", url

    # Everything else is web
    return "web", url


def find_local_pdf(source_id, frontmatter, topic_dir):
    """Try to find a local PDF for a source that doesn't have one in frontmatter."""
    # Map known sources to their local PDFs
    known_mappings = {
        "ea-for-ai:source-056": "documents/Prompt-Engineering-AI-Playbook_AL.pdf",
    }
    if source_id in known_mappings:
        path = topic_dir / known_mappings[source_id]
        if path.exists():
            return str(path)
    return None


def wipe_topic(graph, topic):
    """Delete ALL graph data for a topic."""
    # Get all source IDs
    sources = graph.get_sources_by_topic(topic)
    if not sources:
        print("  No existing data to wipe.")
        return 0

    count = len(sources)

    # Delete in order: Claims, Segments, VisualExtractions, ContentBlocks, Sources
    # Claims and their edges
    graph.conn.execute(
        """
        MATCH (s:Source)-[:CONTAINS]->(b:ContentBlock)<-[:SEGMENTED_FROM]-(sg:Segment)-[:SUPPORTS]->(c:Claim)
        WHERE s.topic = $topic
        DETACH DELETE c
        """,
        parameters={"topic": topic}
    )

    # Segments
    graph.conn.execute(
        """
        MATCH (s:Source)-[:CONTAINS]->(b:ContentBlock)<-[:SEGMENTED_FROM]-(sg:Segment)
        WHERE s.topic = $topic
        DETACH DELETE sg
        """,
        parameters={"topic": topic}
    )

    # VisualExtractions
    graph.conn.execute(
        """
        MATCH (s:Source)-[:CONTAINS]->(b:ContentBlock)<-[:EXTRACTED_FROM]-(v:VisualExtraction)
        WHERE s.topic = $topic
        DETACH DELETE v
        """,
        parameters={"topic": topic}
    )

    # ContentBlocks
    graph.conn.execute(
        """
        MATCH (s:Source)-[:CONTAINS]->(b:ContentBlock)
        WHERE s.topic = $topic
        DETACH DELETE b
        """,
        parameters={"topic": topic}
    )

    # Sources
    graph.conn.execute(
        "MATCH (s:Source) WHERE s.topic = $topic DETACH DELETE s",
        parameters={"topic": topic}
    )

    print(f"  Wiped {count} sources and all related data.")
    return count


def extract_source(source_id, frontmatter, topic, topic_dir, graph, log):
    """Extract a single source. Returns success boolean."""
    url = frontmatter.get("url", "")
    title = frontmatter.get("title", "Untitled")
    author = frontmatter.get("author", "")
    pub_date = frontmatter.get("date", "")

    # Determine source type
    stype, location = determine_source_type(frontmatter, topic_dir)

    # Check for local PDF override
    local_pdf = find_local_pdf(source_id, frontmatter, topic_dir)
    if local_pdf:
        stype = "pdf"
        location = local_pdf

    entry = {
        "source_id": source_id,
        "title": title[:80],
        "source_type": stype,
        "url": url,
        "status": "pending",
    }

    try:
        if stype == "pdf":
            from insight.collector.pdf import extract_pdf_source
            image_dir = str(ROOT / "data" / "images" / source_id.replace(":", "/"))
            result = extract_pdf_source(
                location, topic, source_id, graph,
                title=title, author=author, publication_date=pub_date,
                image_dir=image_dir,
            )
            entry["status"] = "ok"
            entry["blocks"] = result["block_count"]
            entry["chars"] = result["content_length"]
            entry["pages"] = result.get("pages", 0)
            print(f"  [pdf]  {source_id}: {result['block_count']} blocks, {result['content_length']:,} chars")

        elif stype == "youtube":
            from insight.collector.youtube import extract_youtube_source
            result = extract_youtube_source(url, topic, source_id, graph)
            entry["status"] = "ok"
            entry["blocks"] = result["block_count"]
            entry["chars"] = result["content_length"]
            print(f"  [yt]   {source_id}: {result['block_count']} blocks, {result['content_length']:,} chars")

        elif stype == "web":
            from insight.collector.web import extract_web_source
            result = extract_web_source(url, topic, source_id, graph)
            entry["status"] = "ok"
            entry["blocks"] = result["block_count"]
            entry["chars"] = result["content_length"]
            print(f"  [web]  {source_id}: {result['block_count']} blocks, {result['content_length']:,} chars")

        elif stype == "pdf_url":
            # Try web extraction for PDF URLs (landing pages)
            from insight.collector.web import extract_web_source
            result = extract_web_source(url, topic, source_id, graph)
            entry["status"] = "ok"
            entry["source_type"] = "web"
            entry["blocks"] = result["block_count"]
            entry["chars"] = result["content_length"]
            print(f"  [web*] {source_id}: {result['block_count']} blocks, {result['content_length']:,} chars")

        else:
            entry["status"] = "skip"
            entry["error"] = f"Unknown source type: {stype}"
            print(f"  [skip] {source_id}: unknown type {stype}")
            return False

    except Exception as e:
        entry["status"] = "error"
        entry["error"] = str(e)
        entry["traceback"] = traceback.format_exc()
        print(f"  [FAIL] {source_id}: {e}")
        return False

    finally:
        log.append(entry)

    return True


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Fresh extraction of all sources")
    parser.add_argument("--topic", default="ea-for-ai", help="Topic slug")
    parser.add_argument("--source-id", help="Extract only a single source")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without executing")
    args = parser.parse_args()

    topic_dir = find_topic_dir(args.topic)
    if not topic_dir:
        print(f"Topic directory not found for: {args.topic}")
        sys.exit(1)

    # Read all source markdown files
    sources_dir = topic_dir / "sources"
    source_files = sorted(sources_dir.glob("source-*.md"))

    sources = []
    seen_ids = set()
    for sf in source_files:
        front, body = read_source_markdown(sf)
        num = re.search(r"source-(\d+)", sf.stem)
        if not num:
            continue
        source_id = f"{args.topic}:source-{int(num.group(1)):03d}"
        seen_ids.add(source_id)
        stype, location = determine_source_type(front, topic_dir)
        local_pdf = find_local_pdf(source_id, front, topic_dir)
        if local_pdf:
            stype = "pdf"
            location = local_pdf
        sources.append({
            "source_id": source_id,
            "frontmatter": front,
            "type": stype,
            "location": location,
            "file": str(sf),
        })

    # Also include sources that exist only in the graph (e.g. added via CLI)
    graph_tmp = InsightGraph()
    graph_tmp.init_schema()
    existing = graph_tmp.get_sources_by_topic(args.topic)
    for s in existing:
        if s["source_id"] not in seen_ids:
            front = {
                "title": s["title"],
                "url": s["url"],
                "author": s["author"],
                "date": s.get("publication_date", ""),
            }
            stype = s["source_type"]
            location = s["url"]
            sources.append({
                "source_id": s["source_id"],
                "frontmatter": front,
                "type": stype,
                "location": location,
                "file": "(graph-only)",
            })
    graph_tmp.close()

    if args.source_id:
        sources = [s for s in sources if s["source_id"] == args.source_id]
        if not sources:
            print(f"Source not found: {args.source_id}")
            sys.exit(1)

    # Show plan
    by_type = {}
    for s in sources:
        by_type.setdefault(s["type"], []).append(s)

    print(f"Topic: {args.topic} ({topic_dir.name})")
    print(f"Sources: {len(sources)}")
    for t, ss in sorted(by_type.items()):
        print(f"  {t}: {len(ss)}")
        for s in ss:
            title = s["frontmatter"].get("title", "?")[:60]
            print(f"    {s['source_id']}: {title}")

    if args.dry_run:
        print("\nDRY RUN — no changes will be made.")
        return

    # Execute
    graph = InsightGraph()
    graph.init_schema()

    if not args.source_id:
        print(f"\n--- Wiping existing data for {args.topic} ---")
        wipe_topic(graph, args.topic)

    print(f"\n--- Extracting {len(sources)} sources ---\n")

    log = []
    ok = 0
    fail = 0

    for s in sources:
        success = extract_source(
            s["source_id"], s["frontmatter"],
            args.topic, topic_dir, graph, log
        )
        if success:
            ok += 1
        else:
            fail += 1

    # Write log
    os.makedirs(LOG_FILE.parent, exist_ok=True)
    log_data = {
        "topic": args.topic,
        "timestamp": datetime.now().isoformat(),
        "total": len(sources),
        "succeeded": ok,
        "failed": fail,
        "sources": log,
    }
    with open(LOG_FILE, "w") as f:
        json.dump(log_data, f, indent=2)

    print(f"\n{'='*60}")
    print(f"Done. {ok} extracted, {fail} failed.")
    print(f"Log: {LOG_FILE}")

    # Show failures
    failures = [e for e in log if e["status"] == "error"]
    if failures:
        print(f"\nFailed sources:")
        for e in failures:
            print(f"  {e['source_id']}: {e.get('error', '?')}")

    graph.close()


if __name__ == "__main__":
    main()
