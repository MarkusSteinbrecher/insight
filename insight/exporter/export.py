"""
Graph → JSON exporter for the static site.

Reads from the knowledge graph and writes JSON files that the
docs/ site renders. Replaces the v1 build scripts.
"""

from __future__ import annotations

import json
import os
from datetime import date


def _get_all_topics(graph) -> list[str]:
    """Get distinct topic slugs from Source nodes."""
    result = graph.conn.execute(
        "MATCH (s:Source) RETURN DISTINCT s.topic ORDER BY s.topic"
    )
    topics = []
    while result.has_next():
        topics.append(result.get_next()[0])
    return topics


def _determine_phase(topic: str, graph) -> int:
    """Determine topic phase from graph state."""
    claims = graph.count_claims(topic=topic)
    if claims > 0:
        return 3

    # Check if any extracts belong to sources in this topic
    sources = graph.get_sources_by_topic(topic)
    for s in sources:
        if graph.count_extracts(source_id=s["source_id"]) > 0:
            return 1

    return 0


def _topic_title(slug: str, kb_path: str = None) -> str:
    """Derive a display title from a topic slug or _index.md."""
    if kb_path:
        # Search for matching topic directory
        kb = os.path.join(kb_path, "topics")
        if os.path.isdir(kb):
            for d in os.listdir(kb):
                index_path = os.path.join(kb, d, "_index.md")
                if os.path.isfile(index_path):
                    with open(index_path) as f:
                        for line in f:
                            if line.startswith("slug:") and slug in line:
                                # Found the right topic, look for title
                                f.seek(0)
                                for l2 in f:
                                    if l2.startswith("title:"):
                                        return l2.split(":", 1)[1].strip().strip('"')
                                break
    return slug.replace("-", " ").title()


def export_topics(graph, output_dir: str, kb_path: str = None) -> list[dict]:
    """Export topics.json manifest."""
    topics = _get_all_topics(graph)
    topic_list = []
    max_sources = 0
    default_topic = None

    for slug in topics:
        source_count = graph.count_sources(topic=slug)
        phase = _determine_phase(slug, graph)
        topic_list.append({
            "slug": slug,
            "title": _topic_title(slug, kb_path),
            "phase": phase,
            "source_count": source_count,
        })
        if source_count > max_sources:
            max_sources = source_count
            default_topic = slug

    manifest = {
        "topics": topic_list,
        "default_topic": default_topic or (topics[0] if topics else ""),
    }

    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, "topics.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    return topic_list


def export_stats(topic: str, graph, output_dir: str) -> dict:
    """Export {topic}/stats.json with aggregated statistics."""
    sources = graph.get_sources_by_topic(topic)
    type_counts = {}
    for s in sources:
        t = s["source_type"]
        type_counts[t] = type_counts.get(t, 0) + 1

    total_extracts = 0
    for s in sources:
        total_extracts += graph.count_extracts(source_id=s["source_id"])

    claims = graph.get_claims_by_topic(topic)
    # Claim type is encoded in the ID prefix: cc- = canonical, uc- = unique, ct- = contradiction
    canonical = sum(1 for c in claims if ":cc-" in c["claim_id"])
    unique = sum(1 for c in claims if ":uc-" in c["claim_id"])
    contradiction = sum(1 for c in claims if ":ct-" in c["claim_id"])

    finding_count = graph.count_findings(topic=topic)

    stats = {
        "generated": str(date.today()),
        "sources": len(sources),
        "source_types": type_counts,
        "total_extracts": total_extracts,
        "canonical_claims": canonical,
        "unique_claims": unique,
        "contradictions": contradiction,
        "findings": finding_count,
    }

    topic_dir = os.path.join(output_dir, topic)
    os.makedirs(topic_dir, exist_ok=True)
    with open(os.path.join(topic_dir, "stats.json"), "w") as f:
        json.dump(stats, f, indent=2)

    return stats


def _source_claim_counts(graph, topic: str) -> dict:
    """Get claim count per source for a topic."""
    result = graph.conn.execute(
        """
        MATCH (s:Source)-[:HAS_EXTRACT]->(e:Extract)-[:EXTRACT_SUPPORTS]->(c:Claim)
        WHERE c.topic = $topic
        RETURN s.source_id, count(DISTINCT c.claim_id)
        """,
        parameters={"topic": topic}
    )
    counts = {}
    while result.has_next():
        row = result.get_next()
        counts[row[0]] = row[1]
    return counts


def _source_finding_counts(graph, topic: str) -> dict:
    """Get finding count per source for a topic."""
    result = graph.conn.execute(
        """
        MATCH (s:Source)-[:HAS_EXTRACT]->(e:Extract)-[:EXTRACT_SUPPORTS]->(c:Claim)
              -[:CLAIM_IN_FINDING]->(f:Finding)
        WHERE f.topic = $topic
        RETURN s.source_id, count(DISTINCT f.finding_id)
        """,
        parameters={"topic": topic}
    )
    counts = {}
    while result.has_next():
        row = result.get_next()
        counts[row[0]] = row[1]
    return counts


def export_sources(topic: str, graph, output_dir: str) -> list[dict]:
    """Export {topic}/sources.json with source list and metadata."""
    sources = graph.get_sources_by_topic(topic)
    claim_counts = _source_claim_counts(graph, topic)
    finding_counts = _source_finding_counts(graph, topic)
    source_list = []

    for s in sources:
        sid = s["source_id"]
        extract_count = graph.count_extracts(source_id=sid)

        source_list.append({
            "id": sid,
            "title": s["title"],
            "url": s["url"],
            "author": s["author"],
            "date": s.get("publication_date", ""),
            "type": s["source_type"],
            "extract_count": extract_count,
            "claim_count": claim_counts.get(sid, 0),
            "finding_count": finding_counts.get(sid, 0),
        })

    output = {
        "topic": topic,
        "updated": str(date.today()),
        "sources": source_list,
    }

    topic_dir = os.path.join(output_dir, topic)
    os.makedirs(topic_dir, exist_ok=True)
    with open(os.path.join(topic_dir, "sources.json"), "w") as f:
        json.dump(output, f, indent=2)

    return source_list


def export_graph(topic: str, graph, output_dir: str) -> dict:
    """Export {topic}/graph.json with all nodes and edges for D3 visualization."""
    sources = graph.get_sources_by_topic(topic)
    nodes = []
    edges = []
    node_ids = set()
    extract_formats = set()

    for s in sources:
        sid = s["source_id"]
        nodes.append({
            "id": sid,
            "label": s["title"][:60],
            "type": "source",
            "author": s["author"],
            "sourceType": s["source_type"],
        })
        node_ids.add(sid)

        # Add Extract nodes linked to this source
        extracts = graph.get_extracts(sid)
        for e in extracts:
            eid = e["extract_id"]
            fmt = e["format"]
            extract_formats.add(fmt)
            if eid not in node_ids:
                nodes.append({
                    "id": eid,
                    "label": e["text"][:80],
                    "text": e["text"],
                    "type": "extract",
                    "format": fmt,
                    "extractType": e["extract_type"],
                    "author": s["author"],
                    "sourceType": s["source_type"],
                })
                node_ids.add(eid)
            edges.append({"source": sid, "target": eid, "type": "has_extract"})

    # Add claims
    claims = graph.get_claims_by_topic(topic)
    for c in claims:
        cid = c["claim_id"]
        if cid not in node_ids:
            nodes.append({
                "id": cid,
                "label": (c["summary"] or "")[:80],
                "text": c["summary"] or "",
                "type": "claim",
                "theme": c.get("theme", ""),
            })
            node_ids.add(cid)

    # Add EXTRACT_SUPPORTS edges
    result = graph.conn.execute(
        """
        MATCH (e:Extract)-[:EXTRACT_SUPPORTS]->(c:Claim)
        WHERE c.topic = $topic
        RETURN e.extract_id, c.claim_id
        """,
        parameters={"topic": topic}
    )
    while result.has_next():
        row = result.get_next()
        edges.append({"source": row[0], "target": row[1], "type": "supports"})

    # Add findings and CLAIM_IN_FINDING edges
    findings = graph.get_findings_by_topic(topic)
    for f in findings:
        fid = f["finding_id"]
        if fid not in node_ids:
            nodes.append({
                "id": fid,
                "label": f["title"][:80],
                "text": f["description"] or f["title"],
                "type": "finding",
                "category": f.get("category", ""),
            })
            node_ids.add(fid)

    result = graph.conn.execute(
        """
        MATCH (c:Claim)-[:CLAIM_IN_FINDING]->(f:Finding)
        WHERE f.topic = $topic
        RETURN c.claim_id, f.finding_id
        """,
        parameters={"topic": topic}
    )
    while result.has_next():
        row = result.get_next()
        edges.append({"source": row[0], "target": row[1], "type": "in_finding"})

    output = {
        "topic": topic,
        "generated": str(date.today()),
        "nodes": nodes,
        "edges": edges,
        "extract_formats": sorted(extract_formats),
    }

    topic_dir = os.path.join(output_dir, topic)
    os.makedirs(topic_dir, exist_ok=True)
    with open(os.path.join(topic_dir, "graph.json"), "w") as f:
        json.dump(output, f, indent=2)

    return output


def export_findings(topic: str, graph, output_dir: str) -> dict:
    """Export {topic}/findings.json with findings, linked claims, and sources."""
    findings = graph.get_findings_by_topic(topic)
    finding_list = []
    total_claims_linked = 0

    for f in findings:
        fid = f["finding_id"]
        claims_raw = graph.get_claims_for_finding(fid)
        claims = []
        for c in claims_raw:
            cid = c["claim_id"]
            # Get sources via evidence chain
            chain = graph.get_evidence_chain(cid)
            sources_map = {}
            for row in chain:
                sid = row["s.source_id"]
                if sid not in sources_map:
                    sources_map[sid] = {
                        "id": sid,
                        "title": row["s.title"],
                        "author": row["s.author"],
                        "url": row["s.url"],
                        "quotes": [],
                    }
                text = row["e.text"]
                if text and text not in sources_map[sid]["quotes"]:
                    sources_map[sid]["quotes"].append(text[:300])

            claims.append({
                "id": cid,
                "statement": c.get("summary", ""),
                "source_count": len(sources_map),
                "bottom_line": c.get("bottom_line", ""),
                "sources": list(sources_map.values()),
                "baseline_category": c.get("baseline_category", ""),
            })

        total_claims_linked += len(claims)
        finding_list.append({
            "id": fid,
            "title": f["title"],
            "description": f.get("description", ""),
            "category": f.get("category", ""),
            "claim_count": len(claims),
            "claims": claims,
        })

    output = {
        "generated": str(date.today()),
        "total_findings": len(finding_list),
        "total_claims_linked": total_claims_linked,
        "findings": finding_list,
    }

    topic_dir = os.path.join(output_dir, topic)
    os.makedirs(topic_dir, exist_ok=True)
    with open(os.path.join(topic_dir, "findings.json"), "w") as f:
        json.dump(output, f, indent=2)

    return output


def export_visuals(topic: str, graph, output_dir: str) -> list[dict]:
    """Export {topic}/visuals.json with visual extraction data."""
    raw = graph.get_visual_extractions(topic)
    visuals = []

    for v in raw:
        try:
            extracted_data = json.loads(v["extracted_data"]) if isinstance(v["extracted_data"], str) else v["extracted_data"]
        except (json.JSONDecodeError, TypeError):
            extracted_data = []
        try:
            metadata = json.loads(v["metadata"]) if isinstance(v["metadata"], str) else v["metadata"]
        except (json.JSONDecodeError, TypeError):
            metadata = {}

        # Resolve image path: metadata first (has relative path),
        # then block image_path (may be absolute, needs conversion)
        image_path = metadata.get("image_path", "") or v["image_path"] or ""
        # Convert absolute paths to relative (data/images/...)
        if image_path and os.path.isabs(image_path):
            marker = "data/images/"
            idx = image_path.find(marker)
            if idx >= 0:
                image_path = image_path[idx:]

        visuals.append({
            "id": v["extraction_id"],
            "visual_type": v["visual_type"],
            "description": v["visual_description"],
            "extracted_data": extracted_data,
            "extraction_method": v["extraction_method"],
            "metadata": metadata,
            "block_id": v["block_id"],
            "section_path": v["section_path"],
            "image_path": image_path,
            "source_id": v["source_id"],
            "source_title": v["source_title"],
            "source_author": v["source_author"],
            "source_type": v["source_type"],
            "source_url": v["source_url"],
        })

    visual_types = sorted(set(v["visual_type"] for v in visuals))

    output = {
        "topic": topic,
        "generated": str(date.today()),
        "total_visuals": len(visuals),
        "visual_types": visual_types,
        "visuals": visuals,
    }

    topic_dir = os.path.join(output_dir, topic)
    os.makedirs(topic_dir, exist_ok=True)
    with open(os.path.join(topic_dir, "visuals.json"), "w") as f:
        json.dump(output, f, indent=2)

    return visuals


def export_all(graph, output_dir: str, kb_path: str = None) -> dict:
    """Export all topic data to the output directory."""
    topic_list = export_topics(graph, output_dir, kb_path=kb_path)
    total_sources = 0

    for topic_info in topic_list:
        slug = topic_info["slug"]
        export_stats(slug, graph, output_dir)
        sources = export_sources(slug, graph, output_dir)
        export_findings(slug, graph, output_dir)
        export_visuals(slug, graph, output_dir)
        total_sources += len(sources)

    return {
        "topics": len(topic_list),
        "sources": total_sources,
    }
