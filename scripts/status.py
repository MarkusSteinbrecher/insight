#!/usr/bin/env python3
"""Project status dashboard. Run: python3 scripts/status.py"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
DB_PATH = ROOT / "data" / "insight.db"
KB_PATH = ROOT / "knowledge-base" / "topics"
BACKLOG_PATH = ROOT / "backlog.md"


def graph_status():
    """Query the knowledge graph for counts."""
    if not DB_PATH.exists():
        return None

    try:
        from insight.graph import InsightGraph
        g = InsightGraph(str(DB_PATH))
        g.init_schema()

        # Sources by topic and type
        topics = {}
        result = g.conn.execute(
            "MATCH (s:Source) RETURN s.topic, s.source_type, count(*) ORDER BY s.topic"
        )
        while result.has_next():
            row = result.get_next()
            topic, stype, count = row[0], row[1], row[2]
            if topic not in topics:
                topics[topic] = {"total": 0, "types": {}}
            topics[topic]["total"] += count
            topics[topic]["types"][stype] = count

        blocks = g.conn.execute("MATCH (b:ContentBlock) RETURN count(*)").get_next()[0]
        segments = g.conn.execute("MATCH (s:Segment) RETURN count(*)").get_next()[0]
        claims = g.conn.execute("MATCH (c:Claim) RETURN count(*)").get_next()[0]
        g.close()

        return {"topics": topics, "blocks": blocks, "segments": segments, "claims": claims}
    except Exception as e:
        return {"error": str(e)}


def test_status():
    """Run pytest and return pass/fail counts."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--tb=no", "-q", str(ROOT / "tests")],
            capture_output=True, text=True, timeout=120, cwd=str(ROOT)
        )
        last_line = result.stdout.strip().split("\n")[-1]
        return last_line
    except Exception as e:
        return f"error: {e}"


def backlog_status():
    """Count open and done items from backlog.md."""
    if not BACKLOG_PATH.exists():
        return None
    text = BACKLOG_PATH.read_text()
    open_count = text.count("- [ ]")
    done_count = text.count("- [x]")
    return {"open": open_count, "done": done_count}


def research_topics():
    """Scan knowledge-base/topics for research status."""
    if not KB_PATH.exists():
        return []
    topics = []
    for d in sorted(KB_PATH.iterdir()):
        if not d.is_dir():
            continue
        index = d / "_index.md"
        phase = "unknown"
        source_count = 0
        if index.exists():
            for line in index.read_text().splitlines():
                if line.startswith("phase:"):
                    phase = line.split(":", 1)[1].strip()
                if line.startswith("source_count:"):
                    source_count = int(line.split(":", 1)[1].strip())
        # Count source files if not in frontmatter
        if source_count == 0:
            sources_dir = d / "sources"
            if sources_dir.exists():
                source_count = len([f for f in sources_dir.iterdir()
                                    if f.name.startswith("source-") and f.suffix == ".md"])
        topics.append({"name": d.name, "phase": phase, "sources": source_count})
    return topics


def milestone_status():
    """Parse backlog.md for milestone progress."""
    if not BACKLOG_PATH.exists():
        return []
    text = BACKLOG_PATH.read_text()
    milestones = []
    current = None
    for line in text.splitlines():
        if line.startswith("## MVP Milestone"):
            if current:
                milestones.append(current)
            name = line.replace("## ", "").strip()
            current = {"name": name, "done": 0, "open": 0}
        elif current:
            if "- [x]" in line:
                current["done"] += 1
            elif "- [ ]" in line:
                current["open"] += 1
        if line.startswith("## MLP") or line.startswith("## Project"):
            if current:
                milestones.append(current)
                current = None
    if current:
        milestones.append(current)
    return milestones


def main():
    quick = "--quick" in sys.argv or "-q" in sys.argv

    print(f"# Project Status — {date.today()}\n")

    # Engineering
    print("## Engineering\n")
    print("| Milestone | Status | Progress |")
    print("|-----------|--------|----------|")
    for m in milestone_status():
        total = m["done"] + m["open"]
        if m["open"] == 0 and m["done"] > 0:
            status = "Done"
        elif m["done"] > 0:
            status = "In progress"
        else:
            status = "Not started"
        print(f"| {m['name']} | {status} | {m['done']}/{total} |")

    # Tests
    print(f"\n## Tests\n")
    if quick:
        print("  (skipped — use without --quick to run)")
    else:
        print(f"  {test_status()}")

    # Graph
    gs = graph_status()
    print(f"\n## Knowledge Graph\n")
    if gs and "error" not in gs:
        total_sources = sum(t["total"] for t in gs["topics"].values())
        print(f"  Sources: {total_sources} | Blocks: {gs['blocks']} | Segments: {gs['segments']} | Claims: {gs['claims']}")
        for topic, data in gs["topics"].items():
            types = ", ".join(f"{k}: {v}" for k, v in data["types"].items())
            print(f"  - {topic}: {data['total']} sources ({types})")
    elif gs and "error" in gs:
        print(f"  Error: {gs['error']}")
    else:
        print("  No graph database found")

    # Research
    topics = research_topics()
    if topics:
        print(f"\n## Research Topics\n")
        print("| Topic | Phase | Sources |")
        print("|-------|-------|---------|")
        for t in topics:
            print(f"| {t['name']} | {t['phase']} | {t['sources']} |")

    # Backlog
    bl = backlog_status()
    if bl:
        print(f"\n## Backlog\n")
        print(f"  Done: {bl['done']} | Open: {bl['open']}")


if __name__ == "__main__":
    main()
