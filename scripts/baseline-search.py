#!/usr/bin/env python3
"""Search the web for common knowledge on a topic and write a baseline markdown file.

Usage: python3 scripts/baseline-search.py "EA for AI" "How does Enterprise Architecture change because of AI?"
Args: <topic-slug> <search-question>
Dependency: pip install ddgs
"""

import os
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOPICS_DIR = os.path.join(ROOT, "knowledge-base", "topics")


def search_and_extract(question, max_results=15):
    """Search DuckDuckGo and return results with extracted text."""
    from ddgs import DDGS

    ddgs = DDGS()
    raw = ddgs.text(question, max_results=max_results)
    results = []
    for r in raw:
        results.append({
            "title": r.get("title", "Untitled"),
            "url": r.get("href", ""),
            "body": r.get("body", ""),
        })
    return results


def write_baseline(topic_slug, question, results):
    """Write baseline.md for the topic."""
    topic_dir = os.path.join(TOPICS_DIR, topic_slug)
    if not os.path.isdir(topic_dir):
        print(f"Error: topic directory not found: {topic_dir}", file=sys.stderr)
        sys.exit(1)

    output_path = os.path.join(topic_dir, "baseline.md")
    today = date.today().isoformat()

    lines = [
        "---",
        f'question: "{question}"',
        f"created: {today}",
        f"source_count: {len(results)}",
        "search_engine: duckduckgo",
        "---",
        "",
        f"# Topic Baseline: {topic_slug}",
        "",
        f'Search question: "{question}"',
        "",
    ]

    for i, r in enumerate(results, 1):
        title = r["title"]
        url = r["url"]
        body = r["body"]
        lines.append(f"## {i}. [{title}]({url})")
        lines.append("")
        if body:
            lines.append(body)
            lines.append("")

    with open(output_path, "w") as f:
        f.write("\n".join(lines))

    return output_path


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 scripts/baseline-search.py <topic-slug> <search-question>",
              file=sys.stderr)
        sys.exit(1)

    topic_slug = sys.argv[1]
    question = sys.argv[2]

    print(f"Searching for: {question}")
    results = search_and_extract(question)
    print(f"Found {len(results)} results")

    output_path = write_baseline(topic_slug, question, results)
    print(f"Baseline written to {output_path}")


if __name__ == "__main__":
    main()
