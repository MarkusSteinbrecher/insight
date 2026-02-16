#!/usr/bin/env python3
"""Check pipeline progress for all topics (or a specific topic).

Scans topic directories to determine which pipeline steps are complete
based on actual file existence — not just _index.md frontmatter.

Usage:
    python3 scripts/check-progress.py                # All topics, human-readable
    python3 scripts/check-progress.py --json          # All topics, JSON output
    python3 scripts/check-progress.py "EA for AI"     # Specific topic
    python3 scripts/check-progress.py ea-for-ai       # By slug
"""

import argparse
import glob
import json
import os
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOPICS_DIR = os.path.join(ROOT, "knowledge-base", "topics")


def find_topic_dir(slug):
    """Find topic directory by slug or folder name (case-insensitive)."""
    for name in os.listdir(TOPICS_DIR):
        path = os.path.join(TOPICS_DIR, name)
        if not os.path.isdir(path):
            continue
        if name == slug:
            return path
        if name.lower().replace(" ", "-") == slug.lower().replace(" ", "-"):
            return path
    return None


def count_files(directory, pattern):
    """Count files matching a glob pattern in a directory."""
    if not os.path.isdir(directory):
        return 0
    return len(glob.glob(os.path.join(directory, pattern)))


def load_frontmatter(filepath):
    """Load YAML frontmatter from a markdown file."""
    if not os.path.exists(filepath):
        return {}
    with open(filepath, "r") as f:
        content = f.read()
    if not content.startswith("---"):
        return {}
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}
    try:
        return yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        return {}


def check_topic(topic_dir):
    """Check pipeline progress for a single topic. Returns a dict."""
    topic_name = os.path.basename(topic_dir)
    index_path = os.path.join(topic_dir, "_index.md")
    meta = load_frontmatter(index_path)

    sources_dir = os.path.join(topic_dir, "sources")
    raw_dir = os.path.join(topic_dir, "raw")
    extractions_dir = os.path.join(topic_dir, "extractions")
    insights_dir = os.path.join(topic_dir, "insights")
    discussion_dir = os.path.join(topic_dir, "discussion")

    # Count actual files on disk
    source_count = count_files(sources_dir, "source-*.md")
    raw_count = count_files(raw_dir, "source-*-raw.yaml")
    insight_count = count_files(insights_dir, "insight-*.md")
    discussion_count = count_files(discussion_dir, "discussion-*.yaml")

    # Check extraction files
    has_claim_alignment = os.path.exists(
        os.path.join(extractions_dir, "claim-alignment.yaml")
    )
    has_critical_analysis = os.path.exists(
        os.path.join(extractions_dir, "critical-analysis.yaml")
    )
    has_cross_source = os.path.exists(
        os.path.join(extractions_dir, "cross-source-analysis.md")
    )
    has_baseline_eval = os.path.exists(
        os.path.join(extractions_dir, "baseline-evaluation.yaml")
    )
    has_use_cases = os.path.exists(
        os.path.join(extractions_dir, "use-case-inventory.yaml")
    )
    has_baseline = os.path.exists(os.path.join(topic_dir, "baseline.md"))
    has_synthesis = os.path.exists(os.path.join(topic_dir, "synthesis.md"))
    has_findings = os.path.exists(os.path.join(topic_dir, "findings.yaml"))

    # Pending source-input entries
    input_path = os.path.join(topic_dir, "source-input.yaml")
    pending_inputs = 0
    if os.path.exists(input_path):
        with open(input_path, "r") as f:
            data = yaml.safe_load(f)
        if data and "sources" in data and data["sources"]:
            pending_inputs = sum(
                1 for e in data["sources"]
                if not e.get("status") or e.get("status") == "queued"
            )

    # Determine completed steps from file evidence
    steps = {}

    # Phase 0
    steps["0.1"] = source_count > 0
    steps["0.2"] = count_files(os.path.join(topic_dir, "documents"), "*") > 0
    steps["0.3"] = has_baseline and has_baseline_eval

    # Phase 1
    steps["1.1"] = raw_count > 0 and raw_count >= source_count
    steps["1.2"] = has_claim_alignment
    steps["1.3"] = has_critical_analysis
    steps["1.4"] = has_cross_source

    # Phase 2
    steps["2.1"] = discussion_count > 0
    steps["2.2"] = insight_count > 0
    steps["2.3"] = has_synthesis

    # Phase 3
    steps["3.1"] = has_findings

    # Determine next suggested step
    next_step = None
    next_command = None
    slug = meta.get("slug", topic_name.lower().replace(" ", "-"))

    if not steps["0.1"]:
        next_step = "0.1"
        next_command = f"/research {slug}"
    elif not steps["1.1"]:
        next_step = "1.1"
        next_command = f"/analyze {slug}"
    elif not steps["1.2"]:
        next_step = "1.2"
        next_command = f"/analyze {slug}"
    elif not steps["0.3"] and has_baseline:
        next_step = "0.3"
        next_command = f"/baseline {slug}"
    elif not steps["1.3"]:
        next_step = "1.3"
        next_command = f"/analyze {slug}"
    elif not steps["0.3"]:
        next_step = "0.3"
        next_command = f"/baseline {slug}"
    elif not steps["1.4"]:
        next_step = "1.4"
        next_command = f"/analyze {slug}"
    elif not steps["2.1"]:
        next_step = "2.1"
        next_command = f"/discuss {slug}"
    elif not steps["2.3"]:
        next_step = "2.3"
        next_command = f"/synthesize {slug}"
    elif not steps["3.1"]:
        next_step = "3.1"
        next_command = f"/conclude {slug}"

    # Count claim-alignment stats if available
    claims_stats = {}
    if has_claim_alignment:
        ca_path = os.path.join(extractions_dir, "claim-alignment.yaml")
        try:
            with open(ca_path, "r") as f:
                ca = yaml.safe_load(f)
            if ca:
                claims_stats["canonical"] = len(ca.get("canonical_claims", []))
                claims_stats["unique"] = len(ca.get("unique_claims", []))
                claims_stats["contradictions"] = len(ca.get("contradictions", []))
        except (yaml.YAMLError, TypeError):
            pass

    return {
        "topic": topic_name,
        "slug": slug,
        "title": meta.get("title", topic_name),
        "phase": meta.get("phase", 0),
        "status": meta.get("status", "unknown"),
        "current_step": meta.get("current_step"),
        "created": str(meta.get("created", "")),
        "updated": str(meta.get("updated", "")),
        "counts": {
            "sources": source_count,
            "raw_files": raw_count,
            "insights": insight_count,
            "discussions": discussion_count,
            "pending_inputs": pending_inputs,
        },
        "files": {
            "baseline": has_baseline,
            "baseline_evaluation": has_baseline_eval,
            "claim_alignment": has_claim_alignment,
            "critical_analysis": has_critical_analysis,
            "cross_source_analysis": has_cross_source,
            "use_case_inventory": has_use_cases,
            "synthesis": has_synthesis,
            "findings": has_findings,
        },
        "claims": claims_stats,
        "steps": steps,
        "next_step": next_step,
        "next_command": next_command,
    }


STEP_LABELS = {
    "0.1": "Web research",
    "0.2": "Document ingestion",
    "0.3": "Baseline evaluation",
    "1.1": "Raw segmentation",
    "1.2": "Claim alignment",
    "1.3": "Critical analysis",
    "1.4": "Cross-source comparison",
    "2.1": "Interactive discussion",
    "2.2": "Insight extraction",
    "2.3": "Synthesis",
    "3.1": "Findings & conclusions",
}


def print_topic(result):
    """Print human-readable progress for one topic."""
    print(f"\n{'='*60}")
    print(f"  {result['title']}")
    print(f"  Phase {result['phase']} — {result['status']}")
    print(f"{'='*60}")

    print(f"\n  Sources: {result['counts']['sources']}", end="")
    if result["counts"]["raw_files"]:
        print(f"  |  Raw: {result['counts']['raw_files']}", end="")
    if result["counts"]["insights"]:
        print(f"  |  Insights: {result['counts']['insights']}", end="")
    if result["counts"]["pending_inputs"]:
        print(f"  |  Pending inputs: {result['counts']['pending_inputs']}", end="")
    print()

    if result["claims"]:
        c = result["claims"]
        parts = []
        if c.get("canonical"):
            parts.append(f"{c['canonical']} canonical")
        if c.get("unique"):
            parts.append(f"{c['unique']} unique")
        if c.get("contradictions"):
            parts.append(f"{c['contradictions']} contradictions")
        if parts:
            print(f"  Claims: {', '.join(parts)}")

    print(f"\n  Pipeline steps:")
    for step_id, label in STEP_LABELS.items():
        done = result["steps"].get(step_id, False)
        marker = "done" if done else "    "
        current = " <-- next" if step_id == result["next_step"] else ""
        print(f"    [{marker}] {step_id} {label}{current}")

    if result["next_command"]:
        print(f"\n  Suggested: {result['next_command']}")


def main():
    parser = argparse.ArgumentParser(description="Check pipeline progress for topics")
    parser.add_argument("topic", nargs="?", help="Topic slug or name (optional)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if args.topic:
        topic_dir = find_topic_dir(args.topic)
        if not topic_dir:
            print(f"Error: Topic '{args.topic}' not found in {TOPICS_DIR}")
            sys.exit(1)
        results = [check_topic(topic_dir)]
    else:
        results = []
        for name in sorted(os.listdir(TOPICS_DIR)):
            path = os.path.join(TOPICS_DIR, name)
            if os.path.isdir(path) and not name.startswith("."):
                results.append(check_topic(path))

    if args.json:
        print(json.dumps(results, indent=2, default=str))
    else:
        if not results:
            print("No topics found.")
        for r in results:
            print_topic(r)
        print()


if __name__ == "__main__":
    main()
