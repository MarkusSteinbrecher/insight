#!/usr/bin/env python3
"""Build findings.json by joining findings -> claims -> sources.

Reads:
  - findings.yaml (finding -> claim IDs, plus body/bottom_line/practitioner text)
  - critical-analysis.yaml or critical-analysis-part*.yaml (claim statement, critique, bottom_line)
  - claim-alignment.yaml (claim -> supporting sources with segment IDs)
  - sources/source-NNN.md (source title, author, url)

Usage:
  python3 scripts/build-findings-data.py                # Process all topics
  python3 scripts/build-findings-data.py ea-for-ai      # Process one topic

Output: docs/data/{topic-slug}/findings.json
"""

import glob
import json
import os
import re
import sys

import markdown as md_lib
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


def build_findings_for_topic(topic_dir):
    """Build findings JSON for a single topic directory. Returns True if output was written."""
    slug = get_topic_slug(topic_dir)
    findings_path = os.path.join(topic_dir, "findings.yaml")

    if not os.path.exists(findings_path):
        return False

    # Load all data sources
    with open(findings_path, "r") as f:
        findings_data = yaml.safe_load(f)

    if not findings_data or "findings" not in findings_data:
        return False

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

            if not analysis and not alignment:
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

            # Use critical analysis when available, fall back to claim-alignment
            statement = ""
            bottom_line = ""
            if analysis:
                statement = analysis.get("statement", "")
                bottom_line = analysis.get("bottom_line", "")
            elif alignment:
                statement = alignment.get("statement", "")

            claim_out = {
                "id": claim_id,
                "statement": statement,
                "source_count": len(sources),
                "bottom_line": bottom_line,
                "sources": sources,
            }
            if claim_id in baseline_evals:
                claim_out["baseline_category"] = baseline_evals[claim_id]
            output_claims.append(claim_out)
            total_claims += 1

        # Build finding-level output with new fields
        finding_out = {
            "id": finding_id,
            "title": finding_title,
            "claim_count": len(output_claims),
            "claims": output_claims,
        }

        # Include bottom_line from finding if present
        if finding.get("bottom_line"):
            finding_out["bottom_line"] = finding["bottom_line"]

        # Convert body markdown to HTML if present
        if finding.get("body"):
            finding_out["body_html"] = md_lib.markdown(finding["body"])

        # Include practitioner text if present
        if finding.get("practitioner"):
            finding_out["practitioner_text"] = finding["practitioner"]

        output_findings.append(finding_out)

    output = {
        "generated": "2026-02-16",
        "total_findings": len(output_findings),
        "total_claims_linked": total_claims,
        "findings": output_findings,
    }

    output_dir = os.path.join(OUTPUT_BASE, slug)
    output_file = os.path.join(output_dir, "findings.json")
    os.makedirs(output_dir, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2, default=str)

    print(f"  {output_file}")
    print(f"    Findings: {len(output_findings)}")
    print(f"    Claims linked: {total_claims}")
    if missing_claims:
        print(f"    Warning -- claims not found in critical analysis: {missing_claims}")
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


def build_findings_data():
    slug = sys.argv[1] if len(sys.argv) > 1 else None
    topic_dirs = find_topic_dirs(slug)

    if not topic_dirs:
        print("No topic directories found.", file=sys.stderr)
        sys.exit(1)

    print("Building findings data...")
    processed = 0
    for topic_dir in topic_dirs:
        topic_slug = get_topic_slug(topic_dir)
        findings_path = os.path.join(topic_dir, "findings.yaml")
        if not os.path.exists(findings_path):
            print(f"  Skipping {topic_slug} (no findings.yaml)")
            continue
        print(f"  Topic: {topic_slug}")
        if build_findings_for_topic(topic_dir):
            processed += 1

    if processed == 0:
        print("No topics with findings.yaml found.", file=sys.stderr)


if __name__ == "__main__":
    build_findings_data()
