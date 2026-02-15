#!/usr/bin/env python3
"""Build insights.json from critical analysis YAML files.

Reads all knowledge-base/topics/*/extractions/critical-analysis-part*.yaml files
and produces a unified JSON structure for the insights page.

Output: docs/data/insights.json
"""

import glob
import json
import os
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOPICS_DIR = os.path.join(ROOT, "knowledge-base", "topics")
ANALYSIS_GLOB = os.path.join(
    TOPICS_DIR, "*", "extractions", "critical-analysis-part*.yaml"
)
OUTPUT_DIR = os.path.join(ROOT, "docs", "data")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "insights.json")


def parse_frontmatter(filepath):
    """Parse YAML frontmatter from a markdown file."""
    import re
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


def load_claim_source_data():
    """Load claim → sources with segment quotes from claim-alignment + raw files."""
    claim_sources = {}
    for topic_dir in glob.glob(os.path.join(TOPICS_DIR, "*")):
        path = os.path.join(topic_dir, "extractions", "claim-alignment.yaml")
        if not os.path.exists(path):
            continue
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        if not data or "canonical_claims" not in data:
            continue

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


def load_baseline_evaluations():
    """Load baseline evaluations keyed by claim ID from all topics."""
    evals = {}
    for topic_dir in glob.glob(os.path.join(TOPICS_DIR, "*")):
        path = os.path.join(topic_dir, "extractions", "baseline-evaluation.yaml")
        if not os.path.exists(path):
            continue
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        if data and "evaluations" in data:
            for e in data["evaluations"]:
                eid = e.get("id", "")
                if eid:
                    evals[eid] = e.get("category", "")
    return evals


def build_insights_data():
    yaml_files = sorted(glob.glob(ANALYSIS_GLOB))
    if not yaml_files:
        print("No critical analysis YAML files found.", file=sys.stderr)
        sys.exit(1)

    # Load source attribution with segment quotes
    claim_sources = load_claim_source_data()

    # Load baseline evaluations if available
    baseline_evals = load_baseline_evaluations()

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
        "generated": "2026-02-15",
        "total_findings": len(all_analyses),
        "total_contradictions": len(all_contradictions),
        "analyses": all_analyses,
        "contradiction_analyses": all_contradictions,
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(insights, f, indent=2, default=str)

    print(f"Insights data written to {OUTPUT_FILE}")
    print(f"  Claims analyzed: {len(all_analyses)}")
    print(f"  Contradictions analyzed: {len(all_contradictions)}")


if __name__ == "__main__":
    build_insights_data()
