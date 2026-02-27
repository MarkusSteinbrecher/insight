#!/usr/bin/env python3
"""Build conclusions.json by joining conclusions -> findings -> claims.

Reads:
  - extractions/conclusions.yaml (actionability, recommendations, angles)
  - findings.yaml (finding titles, claim IDs)
  - claim-alignment.yaml (claim statements)
  - critical-analysis.yaml (claim bottom_line)

Usage:
  python3 scripts/build-conclusions-data.py                # Process all topics
  python3 scripts/build-conclusions-data.py ea-for-ai      # Process one topic

Output: docs/data/{topic-slug}/conclusions.json
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


def load_findings(topic_dir):
    """Load findings keyed by finding ID."""
    path = os.path.join(topic_dir, "findings.yaml")
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    findings = {}
    if data and "findings" in data:
        for f_item in data["findings"]:
            fid = f_item.get("id", "")
            if fid:
                findings[fid] = f_item
    return findings


def load_critical_analyses(topic_dir):
    """Load analyses keyed by claim ID."""
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


def load_claim_alignment(topic_dir):
    """Load canonical claims keyed by claim ID."""
    path = os.path.join(topic_dir, "extractions", "claim-alignment.yaml")
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    claims = {}
    if data and "canonical_claims" in data:
        for claim in data["canonical_claims"]:
            cid = claim.get("id", "")
            if cid:
                claims[cid] = claim
    return claims


def build_conclusions_for_topic(topic_dir):
    """Build conclusions JSON for a single topic. Returns True if output was written."""
    slug = get_topic_slug(topic_dir)
    conclusions_path = os.path.join(topic_dir, "extractions", "conclusions.yaml")

    if not os.path.exists(conclusions_path):
        return False

    with open(conclusions_path, "r") as f:
        conclusions = yaml.safe_load(f)

    if not conclusions:
        return False

    findings = load_findings(topic_dir)
    analyses = load_critical_analyses(topic_dir)
    claims = load_claim_alignment(topic_dir)

    meta = conclusions.get("meta", {})

    # Build actionability section
    actionability_out = []
    for item in conclusions.get("actionability", []):
        finding_id = item.get("finding_id", "")
        finding = findings.get(finding_id, {})
        actionability_out.append({
            "finding_id": finding_id,
            "finding_title": finding.get("title", ""),
            "finding_bottom_line": finding.get("bottom_line", ""),
            "actionability": item.get("actionability", ""),
            "barriers": item.get("barriers", []),
            "missing_for_action": item.get("missing_for_action", ""),
        })

    # Build recommendations section
    recommendations_out = []
    for rec in conclusions.get("recommendations", []):
        related = []
        for fid in rec.get("related_findings", []):
            finding = findings.get(fid, {})
            related.append({
                "id": fid,
                "title": finding.get("title", ""),
            })
        recommendations_out.append({
            "id": rec.get("id", ""),
            "title": rec.get("title", ""),
            "description": rec.get("description", ""),
            "priority": rec.get("priority", ""),
            "effort": rec.get("effort", ""),
            "dependencies": rec.get("dependencies", []),
            "related_findings": related,
        })

    # Build angles section
    angles_out = []
    for angle in conclusions.get("angles", []):
        supporting = []
        for cid in angle.get("supporting_claims", []):
            analysis = analyses.get(cid, {})
            claim = claims.get(cid, {})
            supporting.append({
                "id": cid,
                "bottom_line": analysis.get("bottom_line", claim.get("statement", "")),
            })
        angles_out.append({
            "id": angle.get("id", ""),
            "title": angle.get("title", ""),
            "position": angle.get("position", ""),
            "why_novel": angle.get("why_novel", ""),
            "supporting_claims": supporting,
            "suggested_format": angle.get("suggested_format", ""),
        })

    output = {
        "generated": meta.get("generated", ""),
        "target_audience": meta.get("target_audience", ""),
        "total_recommendations": len(recommendations_out),
        "total_angles": len(angles_out),
        "actionability": actionability_out,
        "recommendations": recommendations_out,
        "angles": angles_out,
    }

    output_dir = os.path.join(OUTPUT_BASE, slug)
    output_file = os.path.join(output_dir, "conclusions.json")
    os.makedirs(output_dir, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2, default=str)

    print(f"  {output_file}")
    print(f"    Recommendations: {len(recommendations_out)}")
    print(f"    Angles: {len(angles_out)}")
    print(f"    Actionability assessments: {len(actionability_out)}")
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


def build_conclusions_data():
    slug = sys.argv[1] if len(sys.argv) > 1 else None
    topic_dirs = find_topic_dirs(slug)

    if not topic_dirs:
        print("No topic directories found.", file=sys.stderr)
        sys.exit(1)

    print("Building conclusions data...")
    processed = 0
    for topic_dir in topic_dirs:
        topic_slug = get_topic_slug(topic_dir)
        conclusions_path = os.path.join(topic_dir, "extractions", "conclusions.yaml")
        if not os.path.exists(conclusions_path):
            print(f"  Skipping {topic_slug} (no conclusions.yaml)")
            continue
        print(f"  Topic: {topic_slug}")
        if build_conclusions_for_topic(topic_dir):
            processed += 1

    if processed == 0:
        print("No topics with conclusions.yaml found.", file=sys.stderr)


if __name__ == "__main__":
    build_conclusions_data()
