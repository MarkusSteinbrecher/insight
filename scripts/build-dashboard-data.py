#!/usr/bin/env python3
"""Build dashboard.json from raw segment YAML files and claim alignment.

Reads all knowledge-base/topics/*/raw/source-*-raw.yaml files plus
the claim-alignment.yaml and produces a unified JSON structure for the
research dashboard visualization.

Output: docs/data/dashboard.json
"""

import glob
import json
import os
import sys
from collections import defaultdict

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_GLOB = os.path.join(
    ROOT, "knowledge-base", "topics", "*", "raw", "source-*-raw.yaml"
)
OUTPUT_DIR = os.path.join(ROOT, "docs", "data")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "dashboard.json")

# Segment types we care about (skip noise, context, attribution, methodology)
SEGMENT_TYPES = {
    "claim", "statistic", "recommendation", "definition",
    "evidence", "example",
}

# Color assignments (consumed by JS but stored in JSON for single source of truth)
TYPE_COLORS = {
    "finding": "#f59e0b",      # gold/amber — canonical cross-source findings
    "claim": "#3b82f6",        # blue
    "statistic": "#6b7280",    # gray
    "recommendation": "#8b5cf6",  # purple
    "definition": "#10b981",   # green
    "evidence": "#14b8a6",     # teal
    "example": "#f97316",      # orange
    "source": "#ec4899",       # pink
}


def build_dashboard_data():
    yaml_files = sorted(glob.glob(RAW_GLOB))
    if not yaml_files:
        print("No raw segment YAML files found.", file=sys.stderr)
        sys.exit(1)

    sources = []
    nodes = []
    all_sections_by_node = {}   # node_id -> section string (for cross-source matching)
    all_types_by_node = {}      # node_id -> segment type
    stats = defaultdict(int)
    stats_by_source = defaultdict(lambda: defaultdict(int))
    topic_name = None

    for filepath in yaml_files:
        # Derive topic name from path
        parts = filepath.split(os.sep)
        topic_idx = parts.index("topics") + 1
        if topic_name is None:
            topic_name = parts[topic_idx]

        with open(filepath, "r") as f:
            data = yaml.safe_load(f)

        source_id = data.get("source_id", os.path.basename(filepath).replace("-raw.yaml", ""))
        source_title = data.get("title", source_id)
        source_author = data.get("author", "Unknown")
        source_date = str(data.get("date", ""))

        # Shorten author for display
        short_author = source_author.split(",")[0].split("(")[0].strip()
        if len(short_author) > 25:
            short_author = short_author[:22] + "..."

        sources.append({
            "id": source_id,
            "title": source_title,
            "author": source_author,
            "short_author": short_author,
            "date": source_date,
        })

        # Add source as a node
        source_node_id = f"node-{source_id}"
        nodes.append({
            "id": source_node_id,
            "type": "source",
            "label": f"{short_author} ({source_date})",
            "detail": source_title,
            "source": source_id,
            "tags": [],
            "metadata": {"author": source_author, "date": source_date},
        })

        # Process segments
        segments = data.get("segments", []) or []
        for seg in segments:
            seg_type = seg.get("type", "")
            if seg_type not in SEGMENT_TYPES:
                continue

            seg_id = f"{source_id}-{seg.get('id', 'unknown')}"
            text = seg.get("text", "")
            section = seg.get("section", "")
            label = text[:80] + "..." if len(text) > 80 else text

            stats[seg_type] += 1
            stats_by_source[source_id][seg_type] = stats_by_source[source_id].get(seg_type, 0) + 1

            nodes.append({
                "id": seg_id,
                "type": seg_type,
                "label": label,
                "detail": text,
                "source": source_id,
                "tags": [],
                "metadata": {
                    "section": section,
                    "position": seg.get("position", 0),
                },
            })
            all_sections_by_node[seg_id] = section.lower().strip() if section else ""
            all_types_by_node[seg_id] = seg_type

    # Build edges
    edges = []
    edge_set = set()
    node_source = {n["id"]: n["source"] for n in nodes}
    node_type_map = {n["id"]: n["type"] for n in nodes}

    # Connect each segment to its source node
    for n in nodes:
        if n["type"] != "source":
            source_node_id = f"node-{n['source']}"
            edge_key = tuple(sorted([n["id"], source_node_id]))
            if edge_key not in edge_set:
                edge_set.add(edge_key)
                edges.append({
                    "source": n["id"],
                    "target": source_node_id,
                    "shared_tags": [],
                    "weight": 1,
                })

    # Load claim alignment for cross-source connections
    canonical_claims = []
    unique_claims = []
    contradictions = []
    alignment_files = glob.glob(os.path.join(
        ROOT, "knowledge-base", "topics", "*", "extractions", "claim-alignment.yaml"
    ))
    if alignment_files:
        with open(alignment_files[0], "r") as f:
            alignment = yaml.safe_load(f)
        if alignment:
            for cc in (alignment.get("canonical_claims") or []):
                cc_data = {
                    "id": cc["id"],
                    "statement": cc["statement"],
                    "source_count": cc.get("source_count", 0),
                    "theme": cc.get("theme", ""),
                }
                canonical_claims.append(cc_data)

                # Add as a "finding" node
                nodes.append({
                    "id": cc["id"],
                    "type": "finding",
                    "label": cc["statement"],
                    "detail": cc["statement"],
                    "source": "cross-source",
                    "tags": [cc.get("theme", "")] if cc.get("theme") else [],
                    "metadata": {
                        "source_count": cc.get("source_count", 0),
                        "theme": cc.get("theme", ""),
                    },
                    "cross_source_freq": cc.get("source_count", 0),
                })

                # Connect finding to its supporting source nodes
                connected_sources = set()
                for sup in (cc.get("supporting_sources") or []):
                    src_id = sup.get("source_id", "")
                    if src_id:
                        connected_sources.add(src_id)

                        # Connect finding to the specific segment
                        seg_ref = f"{src_id}-{sup.get('seg_id', '')}"
                        if seg_ref in all_sections_by_node:
                            edge_key = tuple(sorted([cc["id"], seg_ref]))
                            if edge_key not in edge_set:
                                edge_set.add(edge_key)
                                edges.append({
                                    "source": cc["id"],
                                    "target": seg_ref,
                                    "shared_tags": ["finding-support"],
                                    "weight": 3,
                                })

                # Connect finding to source nodes
                for src_id in connected_sources:
                    source_node_id = f"node-{src_id}"
                    edge_key = tuple(sorted([cc["id"], source_node_id]))
                    if edge_key not in edge_set:
                        edge_set.add(edge_key)
                        edges.append({
                            "source": cc["id"],
                            "target": source_node_id,
                            "shared_tags": ["finding-source"],
                            "weight": 2,
                        })

            for uc in (alignment.get("unique_claims") or []):
                unique_claims.append({
                    "id": uc.get("id", ""),
                    "statement": uc.get("statement", ""),
                    "original": uc.get("original", ""),
                    "source": uc.get("source", ""),
                })
            for ct in (alignment.get("contradictions") or []):
                contradictions.append({
                    "id": ct.get("id", ""),
                    "tension": ct.get("tension", ""),
                    "side_a": ct.get("side_a", {}),
                    "side_b": ct.get("side_b", {}),
                })

    # Cross-source edges: connect findings that share the same theme
    theme_to_findings = defaultdict(list)
    for cc in canonical_claims:
        theme = cc.get("theme", "")
        if theme:
            theme_to_findings[theme].append(cc["id"])
    for theme, finding_ids in theme_to_findings.items():
        for i, f1 in enumerate(finding_ids):
            for f2 in finding_ids[i + 1:]:
                edge_key = tuple(sorted([f1, f2]))
                if edge_key not in edge_set:
                    edge_set.add(edge_key)
                    edges.append({
                        "source": f1,
                        "target": f2,
                        "shared_tags": [theme],
                        "weight": 2,
                    })

    # Compute cross-source frequency
    cross_source_count = defaultdict(set)
    for edge in edges:
        src = edge["source"]
        tgt = edge["target"]
        src_source = node_source.get(src)
        tgt_source = node_source.get(tgt)
        if src_source and tgt_source and src_source != tgt_source:
            if node_type_map.get(src) != "source" and node_type_map.get(tgt) != "source":
                cross_source_count[src].add(tgt_source)
                cross_source_count[tgt].add(src_source)

    for n in nodes:
        if "cross_source_freq" not in n:
            freq = len(cross_source_count.get(n["id"], set()))
            n["cross_source_freq"] = freq + 1 if n["type"] != "source" else 0

    dashboard = {
        "topic": topic_name,
        "generated": "2026-02-14",
        "stats": {
            "claims": stats.get("claim", 0),
            "statistics": stats.get("statistic", 0),
            "recommendations": stats.get("recommendation", 0),
            "definitions": stats.get("definition", 0),
            "evidence": stats.get("evidence", 0),
            "examples": stats.get("example", 0),
            "sources": len(sources),
            "segments_total": sum(stats.values()),
            "edges": len(edges),
            "findings": len(canonical_claims),
            "contradictions": len(contradictions),
        },
        "stats_by_source": {k: dict(v) for k, v in stats_by_source.items()},
        "sources": sources,
        "type_colors": TYPE_COLORS,
        "nodes": nodes,
        "edges": edges,
        "canonical_claims": canonical_claims,
        "unique_claims": unique_claims,
        "contradictions": contradictions,
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(dashboard, f, indent=2, default=str)

    print(f"Dashboard data written to {OUTPUT_FILE}")
    print(f"  Sources: {len(sources)}")
    print(f"  Nodes:   {len(nodes)} ({len(sources)} source nodes + {len(nodes) - len(sources)} items)")
    print(f"  Edges:   {len(edges)}")
    print(f"  Segments: {dict(stats)}")
    print(f"  Findings: {len(canonical_claims)}")


if __name__ == "__main__":
    build_dashboard_data()
