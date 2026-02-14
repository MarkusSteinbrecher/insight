#!/usr/bin/env python3
"""Build insights.json from critical analysis YAML files.

Reads all knowledge-base/topics/*/extractions/critical-analysis-part*.yaml files
and produces a unified JSON structure for the insights page.

Output: site/static/data/insights.json
"""

import glob
import json
import os
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANALYSIS_GLOB = os.path.join(
    ROOT, "knowledge-base", "topics", "*", "extractions", "critical-analysis-part*.yaml"
)
OUTPUT_DIR = os.path.join(ROOT, "site", "static", "data")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "insights.json")


def build_insights_data():
    yaml_files = sorted(glob.glob(ANALYSIS_GLOB))
    if not yaml_files:
        print("No critical analysis YAML files found.", file=sys.stderr)
        sys.exit(1)

    all_analyses = []
    all_contradictions = []

    for filepath in yaml_files:
        with open(filepath, "r") as f:
            data = yaml.safe_load(f)

        if data and "analyses" in data:
            all_analyses.extend(data["analyses"])
        if data and "contradiction_analyses" in data:
            all_contradictions.extend(data["contradiction_analyses"])

    # Sort by id
    all_analyses.sort(key=lambda x: x.get("id", ""))
    all_contradictions.sort(key=lambda x: x.get("id", ""))

    # Compute summary stats
    verdicts = {}
    total_platitude = 0
    total_actionability = 0
    total_novelty = 0
    all_bingo_terms = {}

    for a in all_analyses:
        v = a.get("verdict", "unknown")
        verdicts[v] = verdicts.get(v, 0) + 1
        scores = a.get("scores", {})
        total_platitude += scores.get("platitude", 0) if isinstance(scores, dict) else a.get("platitude_score", 0)
        total_actionability += scores.get("actionability", 0) if isinstance(scores, dict) else a.get("actionability_score", 0)
        total_novelty += scores.get("novelty", 0) if isinstance(scores, dict) else a.get("novelty_score", 0)
        for term in a.get("bullshit_bingo_terms", []):
            t = term.lower().strip()
            all_bingo_terms[t] = all_bingo_terms.get(t, 0) + 1

    n = len(all_analyses) or 1

    # Sort bingo terms by frequency
    bingo_ranked = sorted(all_bingo_terms.items(), key=lambda x: -x[1])

    insights = {
        "generated": "2026-02-14",
        "total_findings": len(all_analyses),
        "total_contradictions": len(all_contradictions),
        "summary": {
            "verdicts": verdicts,
            "avg_platitude_score": round(total_platitude / n, 1),
            "avg_actionability_score": round(total_actionability / n, 1),
            "avg_novelty_score": round(total_novelty / n, 1),
            "top_bingo_terms": [{"term": t, "count": c} for t, c in bingo_ranked[:15]],
        },
        "analyses": all_analyses,
        "contradiction_analyses": all_contradictions,
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(insights, f, indent=2, default=str)

    print(f"Insights data written to {OUTPUT_FILE}")
    print(f"  Findings analyzed: {len(all_analyses)}")
    print(f"  Contradictions analyzed: {len(all_contradictions)}")
    print(f"  Verdicts: {verdicts}")
    print(f"  Avg platitude score: {round(total_platitude / n, 1)}/10")
    print(f"  Avg actionability: {round(total_actionability / n, 1)}/10")
    print(f"  Top bingo terms: {', '.join(t for t, _ in bingo_ranked[:5])}")


if __name__ == "__main__":
    build_insights_data()
