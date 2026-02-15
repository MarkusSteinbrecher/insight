#!/usr/bin/env python3
"""Build stats.json from knowledge base files.

Consolidates all page-level statistics into a single JSON file
so the site can inject them dynamically instead of hardcoding.

Output: docs/data/stats.json
"""

import glob
import json
import os
import re
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOPICS_DIR = os.path.join(ROOT, "knowledge-base", "topics")
OUTPUT_DIR = os.path.join(ROOT, "docs", "data")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "stats.json")


def parse_frontmatter(filepath):
    """Parse YAML frontmatter from a markdown file."""
    with open(filepath, "r") as f:
        content = f.read()

    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return {}

    fm = {}
    for line in match.group(1).split("\n"):
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("- "):
            continue
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if val:
                fm[key] = val
    return fm


def count_sources(topic_dir):
    """Count source files and extract year range from frontmatter dates."""
    source_files = sorted(glob.glob(os.path.join(topic_dir, "sources", "source-*.md")))
    years = []
    for f in source_files:
        fm = parse_frontmatter(f)
        date_str = fm.get("date", "")
        if date_str and len(date_str) >= 4:
            try:
                years.append(int(date_str[:4]))
            except ValueError:
                pass
    return len(source_files), min(years) if years else None, max(years) if years else None


def sum_segments(topic_dir):
    """Sum total_segments from all raw YAML files."""
    raw_files = glob.glob(os.path.join(topic_dir, "raw", "source-*-raw.yaml"))
    total = 0
    for f in raw_files:
        with open(f, "r") as fh:
            data = yaml.safe_load(fh)
        if data and "total_segments" in data:
            total += data["total_segments"]
    return total


def read_claim_alignment(topic_dir):
    """Read meta block from claim-alignment.yaml."""
    path = os.path.join(topic_dir, "extractions", "claim-alignment.yaml")
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    if data and "meta" in data:
        return data["meta"]
    return {}


def count_findings(topic_dir):
    """Count findings from findings.yaml (source of truth)."""
    findings_path = os.path.join(topic_dir, "findings.yaml")
    if os.path.exists(findings_path):
        with open(findings_path, "r") as f:
            data = yaml.safe_load(f)
        if data and "findings" in data:
            return len(data["findings"])
    return 0


def read_baseline_evaluation(topic_dir):
    """Read baseline evaluation counts if available."""
    path = os.path.join(topic_dir, "extractions", "baseline-evaluation.yaml")
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    if data and "meta" in data:
        meta = data["meta"]
        return {
            "baseline_common": meta.get("common", 0),
            "baseline_additional": meta.get("additional", 0),
            "baseline_new": meta.get("new", 0),
        }
    return {}


def read_baseline_sources(topic_dir):
    """Parse baseline.md into summary bullets and a list of {title, url, summary} entries."""
    path = os.path.join(topic_dir, "baseline.md")
    if not os.path.exists(path):
        return None, None
    with open(path, "r") as f:
        content = f.read()

    # Strip frontmatter
    content = re.sub(r"^---.*?---\s*", "", content, flags=re.DOTALL)

    # Extract summary bullets (## Key themes ... section)
    summary_bullets = []
    summary_match = re.search(
        r"^## Key themes.*?\n(.*?)(?=^## \d+\.|\Z)",
        content, re.DOTALL | re.MULTILINE
    )
    if summary_match:
        for line in summary_match.group(1).strip().split("\n"):
            line = line.strip()
            if line.startswith("- "):
                # Strip bold markers for clean display
                bullet = line[2:].strip()
                summary_bullets.append(bullet)

    # Extract numbered source entries
    entries = []
    parts = re.split(r"^## \d+\.\s+", content, flags=re.MULTILINE)
    for part in parts[1:]:  # skip content before first numbered ##
        lines = part.strip().split("\n", 1)
        if not lines:
            continue
        heading = lines[0].strip()
        summary = lines[1].strip() if len(lines) > 1 else ""

        # Extract [title](url) from heading
        link_match = re.match(r"\[(.+?)\]\((.+?)\)", heading)
        if link_match:
            title = link_match.group(1)
            url = link_match.group(2)
        else:
            title = heading
            url = ""

        entries.append({"title": title, "url": url, "summary": summary})

    return summary_bullets, entries


def build_stats():
    # Find the first (currently only) topic
    topic_dirs = [
        d for d in glob.glob(os.path.join(TOPICS_DIR, "*"))
        if os.path.isdir(d) and os.path.exists(os.path.join(d, "_index.md"))
    ]
    if not topic_dirs:
        print("No topic directories found.", file=sys.stderr)
        sys.exit(1)

    topic_dir = topic_dirs[0]

    # Gather stats
    sources, year_min, year_max = count_sources(topic_dir)
    total_segments = sum_segments(topic_dir)
    claim_meta = read_claim_alignment(topic_dir)
    key_findings = count_findings(topic_dir)
    baseline_stats = read_baseline_evaluation(topic_dir)
    baseline_summary, baseline_sources = read_baseline_sources(topic_dir)

    stats = {
        "generated": "2026-02-15",
        "sources": sources,
        "source_year_min": year_min,
        "source_year_max": year_max,
        "total_segments": total_segments,
        "canonical_claims": claim_meta.get("canonical_claims", 0),
        "unique_claims": claim_meta.get("unique_claims", 0),
        "contradictions": claim_meta.get("contradictions", 0),
        "key_findings": key_findings,
    }
    stats.update(baseline_stats)
    if baseline_summary:
        stats["baseline_summary"] = baseline_summary
    if baseline_sources is not None:
        stats["baseline_sources"] = baseline_sources

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(stats, f, indent=2, default=str)

    print(f"Stats data written to {OUTPUT_FILE}")
    print(f"  Sources: {sources} ({year_min}\u2013{year_max})")
    print(f"  Total segments: {total_segments:,}")
    print(f"  Canonical claims: {stats['canonical_claims']}")
    print(f"  Unique claims: {stats['unique_claims']}")
    print(f"  Contradictions: {stats['contradictions']}")
    print(f"  Key findings: {key_findings}")


if __name__ == "__main__":
    build_stats()
