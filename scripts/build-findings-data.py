#!/usr/bin/env python3
"""Build findings.json by joining findings → claims → sources.

Reads:
  - findings.yaml (finding → claim IDs)
  - critical-analysis.yaml or critical-analysis-part*.yaml (claim statement, critique, bottom_line)
  - claim-alignment.yaml (claim → supporting sources with segment IDs)
  - sources/source-NNN.md (source title, author, url)

Output: docs/data/findings.json
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
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "findings.json")


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


def load_source_meta(topic_dir):
    """Load source metadata (title, author, url) keyed by source_id."""
    sources = {}
    for filepath in sorted(glob.glob(os.path.join(topic_dir, "sources", "source-*.md"))):
        source_id = os.path.basename(filepath).replace(".md", "")
        fm = parse_frontmatter(filepath)
        title = fm.get("title", source_id)
        url = fm.get("url", "")
        # For sources without a URL (e.g. local PDFs), create a Google search link
        if not url:
            from urllib.parse import quote_plus
            url = f"https://www.google.com/search?q={quote_plus(title)}"
        sources[source_id] = {
            "id": source_id,
            "title": title,
            "author": fm.get("author", "Unknown"),
            "url": url,
        }
    return sources


def load_raw_segments(topic_dir):
    """Load all raw segments keyed by 'source_id:seg_id' for quick lookup."""
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


def load_claim_alignment(topic_dir):
    """Load canonical claims from claim-alignment.yaml, keyed by claim ID."""
    path = os.path.join(topic_dir, "extractions", "claim-alignment.yaml")
    if not os.path.exists(path):
        return {}

    with open(path, "r") as f:
        data = yaml.safe_load(f)

    claims = {}
    if data and "canonical_claims" in data:
        for claim in data["canonical_claims"]:
            claim_id = claim.get("id", "")
            if claim_id:
                claims[claim_id] = claim
    return claims


def load_critical_analyses(topic_dir):
    """Load analyses from critical-analysis.yaml (or legacy part files), keyed by claim ID."""
    files = sorted(glob.glob(
        os.path.join(topic_dir, "extractions", "critical-analysis.yaml")
    )) or sorted(glob.glob(
        os.path.join(topic_dir, "extractions", "critical-analysis-part*.yaml")
    ))
    analyses = {}
    for filepath in files:
        with open(filepath, "r") as f:
            data = yaml.safe_load(f)
        if data and "analyses" in data:
            for a in data["analyses"]:
                aid = a.get("id", "")
                if aid:
                    analyses[aid] = a
    return analyses


def dedupe_sources(supporting_sources):
    """Deduplicate supporting sources — keep unique source_ids."""
    seen = set()
    unique = []
    for s in supporting_sources:
        sid = s.get("source_id", "")
        if sid and sid not in seen:
            seen.add(sid)
            unique.append(sid)
    return unique


def load_baseline_evaluations(topic_dir):
    """Load baseline evaluations keyed by claim ID."""
    path = os.path.join(topic_dir, "extractions", "baseline-evaluation.yaml")
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    evals = {}
    if data and "evaluations" in data:
        for e in data["evaluations"]:
            eid = e.get("id", "")
            if eid:
                evals[eid] = e.get("category", "")
    return evals


def build_findings_data():
    # Find topic directories with findings.yaml
    topic_dirs = [
        d for d in glob.glob(os.path.join(TOPICS_DIR, "*"))
        if os.path.isdir(d) and os.path.exists(os.path.join(d, "findings.yaml"))
    ]
    if not topic_dirs:
        print("No topic directories with findings.yaml found.", file=sys.stderr)
        sys.exit(1)

    topic_dir = topic_dirs[0]

    # Load all data sources
    with open(os.path.join(topic_dir, "findings.yaml"), "r") as f:
        findings_data = yaml.safe_load(f)

    source_meta = load_source_meta(topic_dir)
    raw_segments = load_raw_segments(topic_dir)
    claim_alignment = load_claim_alignment(topic_dir)
    critical_analyses = load_critical_analyses(topic_dir)
    baseline_evals = load_baseline_evaluations(topic_dir)

    # Join the graph
    output_findings = []
    total_claims = 0
    missing_claims = []

    for finding in findings_data.get("findings", []):
        finding_id = finding["id"]
        finding_title = finding["title"]
        claim_ids = finding.get("claims", [])

        output_claims = []
        for claim_id in claim_ids:
            analysis = critical_analyses.get(claim_id)
            alignment = claim_alignment.get(claim_id)

            if not analysis:
                missing_claims.append(claim_id)
                continue

            # Group supporting segments by source
            sources = []
            if alignment and "supporting_sources" in alignment:
                by_source = {}
                for s in alignment["supporting_sources"]:
                    sid = s.get("source_id", "")
                    seg_id = s.get("seg_id", "")
                    if not sid:
                        continue
                    if sid not in by_source:
                        by_source[sid] = []
                    seg_text = raw_segments.get(f"{sid}:{seg_id}", "")
                    if seg_text:
                        by_source[sid].append(seg_text)
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

            claim_out = {
                "id": claim_id,
                "statement": analysis.get("statement", ""),
                "source_count": len(sources),
                "bottom_line": analysis.get("bottom_line", ""),
                "sources": sources,
            }
            if claim_id in baseline_evals:
                claim_out["baseline_category"] = baseline_evals[claim_id]
            output_claims.append(claim_out)
            total_claims += 1

        output_findings.append({
            "id": finding_id,
            "title": finding_title,
            "claim_count": len(output_claims),
            "claims": output_claims,
        })

    output = {
        "generated": "2026-02-15",
        "total_findings": len(output_findings),
        "total_claims_linked": total_claims,
        "findings": output_findings,
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2, default=str)

    print(f"Findings data written to {OUTPUT_FILE}")
    print(f"  Findings: {len(output_findings)}")
    print(f"  Claims linked: {total_claims}")
    if missing_claims:
        print(f"  Warning — claims not found in critical analysis: {missing_claims}")


if __name__ == "__main__":
    build_findings_data()
