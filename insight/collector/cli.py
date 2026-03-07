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
import os
import re
import sys

from insight.graph import InsightGraph
from insight.collector.discovery import check_urls, detect_source_type
from insight.collector.baseline import (
    load_baseline, save_baseline, baseline_path,
    record_run, add_sources, SourceRecord,
)


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
        filepath = args.file
        if not os.path.isfile(filepath):
            print(f"File not found: {filepath}")
            sys.exit(1)

        source_id = f"{topic}:source-{_next_source_number(graph, topic):03d}"
        print(f"\n{'='*60}")
        print(f"[{source_id}] file: {filepath}")
        print(f"{'='*60}")

        try:
            from insight.collector.pdf import extract_pdf_source
            result = extract_pdf_source(
                filepath, topic, source_id, graph,
                title=args.title or "",
                author=args.author or "",
                publication_date=args.date or "",
            )
            print(f"  Title: {result['title']}")
            print(f"  Author: {result['author']}")
            print(f"  Blocks: {result['block_count']}")
            print(f"  Pages: {result['pages']}")
            print(f"  Content: {result['content_length']:,} chars")
        except Exception as e:
            print(f"  [ERROR] {e}")

        graph.close()
        return

    if not urls:
        print("No URLs provided. Use --urls or --file.")
        sys.exit(1)

    # Check registry — filter out already-collected URLs (with full normalization)
    discovery = check_urls(urls, topic, graph)
    new_urls = discovery.new
    skipped = discovery.existing

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
    collected_sources = []

    for url in new_urls:
        source_id = f"{topic}:source-{next_num:03d}"
        source_type = detect_source_type(url)

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

            elif source_type == "pdf":
                from insight.collector.pdf import extract_pdf_source
                result = extract_pdf_source(url, topic, source_id, graph, url=url)
                print(f"  Title: {result['title']}")
                print(f"  Author: {result['author']}")
                print(f"  Blocks: {result['block_count']}")
                print(f"  Pages: {result['pages']}")

            else:
                print(f"  Extractor not yet implemented for: {source_type}")
                failed += 1
                continue

            print(f"  Content: {result['content_length']:,} chars")
            collected_sources.append(SourceRecord(
                url=url, title=result.get("title", ""),
                source_type=source_type, source_id=source_id,
            ))
            succeeded += 1
            next_num += 1

        except Exception as e:
            print(f"  [ERROR] {e}")
            failed += 1

    print(f"\n{'='*60}")
    print(f"Done. {succeeded} collected, {failed} failed, {len(skipped)} already existed.")
    graph.close()

    # Update baseline with newly extracted sources
    if collected_sources:
        try:
            bl = load_baseline(topic)
            added = add_sources(bl, collected_sources)
            save_baseline(bl)
            if added:
                print(f"Baseline updated: {added} source(s) added.")
        except FileNotFoundError:
            pass


def cmd_discover(args):
    """Check URLs against the source registry."""
    topic = args.topic

    if args.from_baseline:
        try:
            bl = load_baseline(topic)
        except FileNotFoundError:
            print(f"No baseline found for topic '{topic}'.")
            print(f"Create one: python -m insight.collector baseline --topic {topic}")
            sys.exit(1)

        print(f"Baseline: {bl.title}")
        print(f"Question: {bl.question}")

        if bl.keywords:
            print(f"\nWeb search keywords:")
            for kw in bl.keywords:
                print(f"  - {kw}")

        if bl.youtube_keywords:
            print(f"\nYouTube search keywords:")
            for kw in bl.youtube_keywords:
                print(f"  - {kw}")

        print(f"\nTracked sources: {len(bl.sources)}")
        if bl.runs:
            last = bl.runs[-1]
            print(f"Last run: {last.date} — found {last.found}, {last.new} new")

        print(f"\nUse these keywords to search, then run:")
        print(f"  python -m insight.collector discover --urls <URLs> --topic {topic}")
        print(f"  python -m insight.collector extract --urls <URLs> --topic {topic}")
        return

    graph = InsightGraph()
    graph.init_schema()

    urls = args.urls or []

    if not urls:
        print("No URLs provided. Use --urls or --from-baseline.")
        sys.exit(1)

    discovery = check_urls(urls, topic, graph)

    print(f"Results for topic '{topic}': {discovery.total} URLs checked")
    print(f"  New: {len(discovery.new)}")
    print(f"  Already collected: {len(discovery.existing)}")

    if discovery.new:
        print(f"\nNew URLs:")
        for url in discovery.new:
            print(f"  + {url}")

    if discovery.existing:
        print(f"\nAlready collected:")
        for url in discovery.existing:
            print(f"  - {url}")

    graph.close()

    # Record this run in the baseline if one exists
    try:
        bl = load_baseline(topic)
        record_run(bl, keywords_used=[], found=discovery.total,
                   new=len(discovery.new), already_collected=len(discovery.existing))
        # Add newly discovered URLs as unextracted source records
        new_records = [
            SourceRecord(url=url, title="", source_type=detect_source_type(url), source_id="")
            for url in discovery.new
        ]
        added = add_sources(bl, new_records)
        save_baseline(bl)
        if added:
            print(f"\nBaseline updated: {added} new URL(s) tracked.")
    except FileNotFoundError:
        pass


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


def cmd_baseline(args):
    """Show baseline configuration for a topic."""
    topic = args.topic

    path = baseline_path(topic)
    try:
        bl = load_baseline(topic)
    except FileNotFoundError:
        print(f"No baseline found for topic '{topic}'.")
        print(f"Expected at: {os.path.abspath(path)}")
        print(f"\nCreate a YAML file with this structure:")
        print(f"  topic: {topic}")
        print(f"  title: Your Topic Title")
        print(f"  question: What is the core research question?")
        print(f"  keywords:")
        print(f"    - \"keyword one\"")
        print(f"    - \"keyword two\"")
        print(f"  youtube_keywords:")
        print(f"    - \"youtube search term\"")
        print(f"  sources: []")
        print(f"  runs: []")
        sys.exit(1)

    print(f"Baseline: {bl.title}")
    print(f"  Topic: {bl.topic}")
    print(f"  Question: {bl.question}")

    if bl.keywords:
        print(f"\nWeb keywords ({len(bl.keywords)}):")
        for kw in bl.keywords:
            print(f"  - {kw}")

    if bl.youtube_keywords:
        print(f"\nYouTube keywords ({len(bl.youtube_keywords)}):")
        for kw in bl.youtube_keywords:
            print(f"  - {kw}")

    # Sources
    collected = [s for s in bl.sources if s.source_id]
    pending = [s for s in bl.sources if not s.source_id]
    print(f"\nSources: {len(bl.sources)} tracked ({len(collected)} collected, {len(pending)} pending)")
    for s in bl.sources:
        status = s.source_id if s.source_id else "pending"
        title = s.title or s.url
        if len(title) > 60:
            title = title[:57] + "..."
        print(f"  [{status}] {title}")

    # Run history
    if bl.runs:
        print(f"\nRun history ({len(bl.runs)}):")
        for r in bl.runs:
            print(f"  {r.date}: found {r.found}, {r.new} new, {r.already_collected} existing")
    else:
        print(f"\nNo discovery runs recorded yet.")


def main():
    parser = argparse.ArgumentParser(prog="insight.collector", description="Insight Collector")
    subparsers = parser.add_subparsers(dest="command")

    # extract
    p_extract = subparsers.add_parser("extract", help="Extract sources into the graph")
    p_extract.add_argument("--urls", nargs="+", help="URLs to extract")
    p_extract.add_argument("--file", help="Local file to extract (PDF)")
    p_extract.add_argument("--title", help="Override source title")
    p_extract.add_argument("--author", help="Override source author")
    p_extract.add_argument("--date", help="Override publication date")
    p_extract.add_argument("--topic", required=True, help="Topic slug")

    # discover
    p_discover = subparsers.add_parser("discover", help="Check URLs against source registry")
    p_discover.add_argument("--urls", nargs="+", help="URLs to check")
    p_discover.add_argument("--from-baseline", action="store_true",
                           help="Show keywords from baseline for manual search")
    p_discover.add_argument("--topic", required=True, help="Topic slug")

    # status
    p_status = subparsers.add_parser("status", help="Show collection status")
    p_status.add_argument("--topic", required=True, help="Topic slug")

    # baseline
    p_baseline = subparsers.add_parser("baseline", help="Show topic baseline configuration")
    p_baseline.add_argument("--topic", required=True, help="Topic slug")

    args = parser.parse_args()

    if args.command == "extract":
        cmd_extract(args)
    elif args.command == "discover":
        cmd_discover(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "baseline":
        cmd_baseline(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
