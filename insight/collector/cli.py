"""
Collector CLI — discovery, extraction, and status.

Usage:
    python -m insight.collector extract --urls URL [URL ...] --topic TOPIC
    python -m insight.collector extract --file PATH --topic TOPIC
    python -m insight.collector status --topic TOPIC
    python -m insight.collector discover --urls URL [URL ...] --topic TOPIC
"""

from __future__ import annotations

import argparse
import re
import sys

from insight.graph import InsightGraph


def _detect_source_type(url: str) -> str:
    """Detect source type from URL pattern."""
    if re.search(r"(youtube\.com/watch|youtu\.be/)", url):
        return "youtube"
    if url.lower().endswith(".pdf"):
        return "pdf"
    return "web"


def _next_source_number(graph: InsightGraph, topic: str) -> int:
    """Determine the next source number for a topic."""
    sources = graph.get_sources_by_topic(topic)
    max_num = 0
    for s in sources:
        match = re.search(r"source-(\d+)$", s["source_id"])
        if match:
            max_num = max(max_num, int(match.group(1)))
    return max_num + 1


def cmd_extract(args):
    """Extract sources from URLs or files into the graph."""
    graph = InsightGraph()
    graph.init_schema()

    topic = args.topic
    urls = args.urls or []

    if args.file:
        print(f"File extraction not yet implemented: {args.file}")
        sys.exit(1)

    if not urls:
        print("No URLs provided. Use --urls or --file.")
        sys.exit(1)

    # Check registry — filter out already-collected URLs
    existing_urls = graph.get_existing_urls(topic)
    new_urls = []
    skipped = []
    for url in urls:
        # Normalize URL for comparison
        url_clean = url.rstrip("/")
        if any(existing.rstrip("/") == url_clean for existing in existing_urls):
            skipped.append(url)
        else:
            new_urls.append(url)

    if skipped:
        print(f"Already collected ({len(skipped)}):")
        for url in skipped:
            print(f"  [skip] {url}")

    if not new_urls:
        print("\nNo new sources to collect.")
        graph.close()
        return

    print(f"\nCollecting {len(new_urls)} new source(s):")
    next_num = _next_source_number(graph, topic)

    succeeded = 0
    failed = 0

    for url in new_urls:
        source_id = f"{topic}:source-{next_num:03d}"
        source_type = _detect_source_type(url)

        print(f"\n{'='*60}")
        print(f"[{source_id}] {source_type}: {url}")
        print(f"{'='*60}")

        try:
            if source_type == "youtube":
                from insight.collector.youtube import extract_youtube_source
                result = extract_youtube_source(url, topic, source_id, graph)
                print(f"  Title: {result['title']}")
                print(f"  Channel: {result['author']}")
                print(f"  Duration: {result['duration']}")
                print(f"  Blocks: {result['block_count']} ({result['transcript_segments']} transcript segments)")

            elif source_type == "web":
                from insight.collector.web import extract_web_source
                result = extract_web_source(url, topic, source_id, graph)
                print(f"  Title: {result['title']}")
                print(f"  Author: {result['author']}")
                print(f"  Blocks: {result['block_count']}")

            else:
                print(f"  Extractor not yet implemented for: {source_type}")
                failed += 1
                continue

            print(f"  Content: {result['content_length']:,} chars")
            succeeded += 1
            next_num += 1

        except Exception as e:
            print(f"  [ERROR] {e}")
            failed += 1

    print(f"\n{'='*60}")
    print(f"Done. {succeeded} collected, {failed} failed, {len(skipped)} already existed.")
    graph.close()


def cmd_discover(args):
    """Check URLs against the source registry."""
    graph = InsightGraph()
    graph.init_schema()

    topic = args.topic
    urls = args.urls or []

    if not urls:
        print("No URLs provided.")
        sys.exit(1)

    existing_urls = graph.get_existing_urls(topic)

    new_urls = []
    known_urls = []
    for url in urls:
        url_clean = url.rstrip("/")
        if any(existing.rstrip("/") == url_clean for existing in existing_urls):
            known_urls.append(url)
        else:
            new_urls.append(url)

    print(f"Results for topic '{topic}': {len(urls)} URLs checked")
    print(f"  New: {len(new_urls)}")
    print(f"  Already collected: {len(known_urls)}")

    if new_urls:
        print(f"\nNew URLs:")
        for url in new_urls:
            print(f"  + {url}")

    if known_urls:
        print(f"\nAlready collected:")
        for url in known_urls:
            print(f"  - {url}")

    graph.close()


def cmd_status(args):
    """Show collection status for a topic."""
    graph = InsightGraph()
    graph.init_schema()

    topic = args.topic
    sources = graph.get_sources_by_topic(topic)

    if not sources:
        print(f"No sources collected for topic '{topic}'.")
        graph.close()
        return

    # Group by source type
    by_type = {}
    for s in sources:
        st = s.get("source_type", "unknown")
        by_type.setdefault(st, []).append(s)

    print(f"Topic: {topic}")
    print(f"Total sources: {len(sources)}")
    print()

    for stype, type_sources in sorted(by_type.items()):
        print(f"  {stype}: {len(type_sources)}")

    print()
    total_blocks = 0
    for s in sources:
        block_count = graph.count_content_blocks(s["source_id"])
        total_blocks += block_count
        title = s.get("title", "?")
        if len(title) > 55:
            title = title[:52] + "..."
        print(f"  {s['source_id']:30s}  {s['source_type']:8s}  {block_count:4d} blocks  {title}")

    print(f"\nTotal content blocks: {total_blocks}")
    graph.close()


def main():
    parser = argparse.ArgumentParser(prog="insight.collector", description="Insight Collector")
    subparsers = parser.add_subparsers(dest="command")

    # extract
    p_extract = subparsers.add_parser("extract", help="Extract sources into the graph")
    p_extract.add_argument("--urls", nargs="+", help="URLs to extract")
    p_extract.add_argument("--file", help="Local file to extract")
    p_extract.add_argument("--topic", required=True, help="Topic slug")

    # discover
    p_discover = subparsers.add_parser("discover", help="Check URLs against source registry")
    p_discover.add_argument("--urls", nargs="+", help="URLs to check")
    p_discover.add_argument("--topic", required=True, help="Topic slug")

    # status
    p_status = subparsers.add_parser("status", help="Show collection status")
    p_status.add_argument("--topic", required=True, help="Topic slug")

    args = parser.parse_args()

    if args.command == "extract":
        cmd_extract(args)
    elif args.command == "discover":
        cmd_discover(args)
    elif args.command == "status":
        cmd_status(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
