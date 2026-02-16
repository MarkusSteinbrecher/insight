#!/usr/bin/env python3
"""Build insights.json from critical analysis YAML files.

Reads knowledge-base/topics/*/extractions/critical-analysis.yaml (preferred)
or critical-analysis-part*.yaml (legacy) and produces a unified JSON structure
for the insights page.

Usage:
  python3 scripts/build-insights-data.py                # Process all topics
  python3 scripts/build-insights-data.py ea-for-ai      # Process one topic

Output: docs/data/{topic-slug}/insights.json
"""

import glob
import json
import os
import re
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOPICS_DIR = os.path.join(ROOT, "knowledge-base", "topics")
OUTPUT_BASE = os.path.join(ROOT, "docs", "data")


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


def parse_frontmatter_yaml(filepath):
    """Parse YAML frontmatter from a markdown file using yaml.safe_load."""
    with open(filepath, "r") as f:
        content = f.read()

    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return {}

    try:
        return yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        return {}


def get_topic_slug(topic_dir):
    """Get the topic slug from _index.md frontmatter or directory name."""
    index_path = os.path.join(topic_dir, "_index.md")
    if os.path.exists(index_path):
        fm = parse_frontmatter_yaml(index_path)
        slug = fm.get("slug", "")
        if slug:
            return slug
    return os.path.basename(topic_dir).lower().replace(" ", "-")


def load_source_meta(topic_dir):
    """Load source metadata keyed by source_id."""
    from urllib.parse import quote_plus
    sources = {}
    for filepath in sorted(glob.glob(os.path.join(topic_dir, "sources", "source-*.md"))):
        source_id = os.path.basename(filepath).replace(".md", "")
        fm = parse_frontmatter(filepath)
        title = fm.get("title", source_id)
        url = fm.get("url", "")
        if not url:
            url = f"https://www.google.com/search?q={quote_plus(title)}"
        sources[source_id] = {
            "id": source_id,
            "title": title,
            "author": fm.get("author", "Unknown"),
            "url": url,
        }
    return sources


def load_raw_segments(topic_dir):
    """Load all raw segments keyed by 'source_id:seg_id'."""
    segments = {}
    for filepath in sorted(glob.glob(os.path.join(topic_dir, "raw", "source-*-raw.yaml"))):
        with open(filepath, "r") as f:
            data = yaml.safe_load(f)
        if not data or "segments" not in data:
            continue
        src_id = data.get("source_id", "")
        for seg in data["segments"]:
            seg_id = seg.get("id", "")
            if src_id and seg_id:
                segments[f"{src_id}:{seg_id}"] = seg.get("text", "")
    return segments


def load_claim_source_data(topic_dir):
    """Load claim -> sources with segment quotes from claim-alignment + raw files for a single topic."""
    claim_sources = {}
    path = os.path.join(topic_dir, "extractions", "claim-alignment.yaml")
    if not os.path.exists(path):
        return claim_sources
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    if not data or "canonical_claims" not in data:
        return claim_sources

    source_meta = load_source_meta(topic_dir)
    raw_segments = load_raw_segments(topic_dir)

    for claim in data["canonical_claims"]:
        claim_id = claim.get("id", "")
        if not claim_id:
            continue
        # Group segments by source
        by_source = {}
        for s in claim.get("supporting_sources", []):
            sid = s.get("source_id", "")
            seg_id = s.get("seg_id", "")
            if not sid:
                continue
            if sid not in by_source:
                by_source[sid] = []
            seg_text = raw_segments.get(f"{sid}:{seg_id}", "")
            if seg_text:
                by_source[sid].append(seg_text)

        sources = []
        for sid, quotes in by_source.items():
            meta = source_meta.get(sid, {
                "id": sid, "title": sid, "author": "Unknown", "url": ""
            })
            sources.append({
                "id": meta["id"],
                "title": meta["title"],
                "author": meta["author"],
                "url": meta["url"],
                "quotes": quotes,
            })
        claim_sources[claim_id] = sources
    return claim_sources


def load_baseline_evaluations(topic_dir):
    """Load baseline evaluations keyed by claim ID for a single topic."""
    evals = {}
    path = os.path.join(topic_dir, "extractions", "baseline-evaluation.yaml")
    if not os.path.exists(path):
        return evals
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    if data and "evaluations" in data:
        for e in data["evaluations"]:
            eid = e.get("id", "")
            if eid:
                evals[eid] = e.get("category", "")
    return evals


def has_critical_analysis(topic_dir):
    """Check if a topic has critical analysis files."""
    single = glob.glob(os.path.join(topic_dir, "extractions", "critical-analysis.yaml"))
    parts = glob.glob(os.path.join(topic_dir, "extractions", "critical-analysis-part*.yaml"))
    return bool(single or parts)


def build_insights_for_topic(topic_dir):
    """Build insights JSON for a single topic directory. Returns True if output was written."""
    slug = get_topic_slug(topic_dir)

    # Find critical analysis files for this topic
    yaml_files = sorted(glob.glob(
        os.path.join(topic_dir, "extractions", "critical-analysis.yaml")
    )) or sorted(glob.glob(
        os.path.join(topic_dir, "extractions", "critical-analysis-part*.yaml")
    ))

    if not yaml_files:
        return False

    # Load source attribution with segment quotes
    claim_sources = load_claim_source_data(topic_dir)

    # Load baseline evaluations if available
    baseline_evals = load_baseline_evaluations(topic_dir)

    all_analyses = []
    all_contradictions = []

    for filepath in yaml_files:
        with open(filepath, "r") as f:
            data = yaml.safe_load(f)

        if data and "analyses" in data:
            for a in data["analyses"]:
                # Add source attribution with quotes from claim-alignment
                claim_id = a.get("id", "")
                if claim_id in claim_sources:
                    a["sources"] = claim_sources[claim_id]
                # Add baseline category if available
                if claim_id in baseline_evals:
                    a["baseline_category"] = baseline_evals[claim_id]
                all_analyses.append(a)
        if data and "contradiction_analyses" in data:
            all_contradictions.extend(data["contradiction_analyses"])

    # Sort by id
    all_analyses.sort(key=lambda x: x.get("id", ""))
    all_contradictions.sort(key=lambda x: x.get("id", ""))

    insights = {
        "generated": "2026-02-16",
        "total_findings": len(all_analyses),
        "total_contradictions": len(all_contradictions),
        "analyses": all_analyses,
        "contradiction_analyses": all_contradictions,
    }

    output_dir = os.path.join(OUTPUT_BASE, slug)
    output_file = os.path.join(output_dir, "insights.json")
    os.makedirs(output_dir, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(insights, f, indent=2, default=str)

    print(f"  {output_file}")
    print(f"    Claims analyzed: {len(all_analyses)}")
    print(f"    Contradictions analyzed: {len(all_contradictions)}")
    return True


def find_topic_dirs(slug=None):
    """Find topic directories, optionally filtering by slug."""
    all_dirs = [
        d for d in glob.glob(os.path.join(TOPICS_DIR, "*"))
        if os.path.isdir(d) and os.path.exists(os.path.join(d, "_index.md"))
    ]
    if slug:
        matching = [d for d in all_dirs if get_topic_slug(d) == slug]
        if not matching:
            print(f"Topic '{slug}' not found.", file=sys.stderr)
            sys.exit(1)
        return matching
    return sorted(all_dirs)


def build_insights_data():
    slug = sys.argv[1] if len(sys.argv) > 1 else None
    topic_dirs = find_topic_dirs(slug)

    if not topic_dirs:
        print("No topic directories found.", file=sys.stderr)
        sys.exit(1)

    print("Building insights data...")
    processed = 0
    for topic_dir in topic_dirs:
        topic_slug = get_topic_slug(topic_dir)
        if not has_critical_analysis(topic_dir):
            print(f"  Skipping {topic_slug} (no critical-analysis files)")
            continue
        print(f"  Topic: {topic_slug}")
        if build_insights_for_topic(topic_dir):
            processed += 1

    if processed == 0:
        print("No topics with critical analysis data found.", file=sys.stderr)


if __name__ == "__main__":
    build_insights_data()
