"""CLI entry point: python3 -m insight.exporter"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from insight.graph import InsightGraph
from insight.exporter.export import export_all, export_stats, export_sources, export_topics


def main():
    parser = argparse.ArgumentParser(description="Export graph data to JSON for the static site")
    parser.add_argument("--output", default=str(ROOT / "docs" / "data"), help="Output directory")
    parser.add_argument("--topic", help="Export only this topic (default: all)")
    parser.add_argument("--db", default=str(ROOT / "data" / "insight.db"), help="Database path")
    args = parser.parse_args()

    graph = InsightGraph(args.db)
    graph.init_schema()

    kb_path = str(ROOT / "knowledge-base")

    if args.topic:
        export_topics(graph, args.output, kb_path=kb_path)
        export_stats(args.topic, graph, args.output)
        export_sources(args.topic, graph, args.output)
        print(f"Exported topic: {args.topic}")
    else:
        result = export_all(graph, args.output, kb_path=kb_path)
        print(f"Exported {result['topics']} topics, {result['sources']} sources → {args.output}")

    graph.close()


if __name__ == "__main__":
    main()
