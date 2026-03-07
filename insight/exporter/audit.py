"""
Export source audit data: source metadata + markdown content + extracted blocks.

Used by the site's Audit page to show side-by-side comparison of
original source notes vs. extracted content blocks.
"""

from __future__ import annotations

import json
import os
import re
from datetime import date


def _read_source_markdown(kb_path: str, topic_dir: str, source_id: str) -> dict:
    """Read source markdown file and parse into structured sections."""
    # source_id is like "ea-for-ai:source-001", extract the file part
    file_part = source_id.split(":")[-1]  # "source-001"
    md_path = os.path.join(kb_path, "topics", topic_dir, "sources", f"{file_part}.md")

    if not os.path.isfile(md_path):
        return {"raw_markdown": "", "sections": []}

    with open(md_path) as f:
        content = f.read()

    # Strip YAML frontmatter
    if content.startswith("---"):
        end = content.find("---", 3)
        if end != -1:
            content = content[end + 3:].strip()

    # Split into sections by ## headings
    sections = []
    current_heading = "Introduction"
    current_lines = []

    for line in content.split("\n"):
        if line.startswith("## "):
            if current_lines:
                sections.append({
                    "heading": current_heading,
                    "content": "\n".join(current_lines).strip(),
                })
            current_heading = line[3:].strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections.append({
            "heading": current_heading,
            "content": "\n".join(current_lines).strip(),
        })

    return {
        "raw_markdown": content,
        "sections": sections,
    }


def _build_embed_url(source: dict, metadata: dict) -> str:
    """Build an embeddable URL for the original source."""
    stype = source["source_type"]
    url = source["url"]

    if stype == "youtube" and url:
        # Extract video ID from YouTube URL
        vid = ""
        if "v=" in url:
            vid = url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in url:
            vid = url.split("youtu.be/")[1].split("?")[0]
        if vid:
            return f"https://www.youtube.com/embed/{vid}"
        return url

    if stype == "pdf":
        # Local PDF with document_path
        doc_path = metadata.get("document_path", metadata.get("document", ""))
        if doc_path:
            # Serve from static/documents/
            filename = os.path.basename(doc_path)
            return f"documents/{filename}"
        # Remote PDF — try URL directly
        if url:
            return url

    if stype == "web" and url:
        return url

    return ""


def _find_topic_dir(kb_path: str, topic_slug: str) -> str | None:
    """Find the actual directory name for a topic slug."""
    topics_dir = os.path.join(kb_path, "topics")
    if not os.path.isdir(topics_dir):
        return None
    for d in os.listdir(topics_dir):
        index_path = os.path.join(topics_dir, d, "_index.md")
        if os.path.isfile(index_path):
            with open(index_path) as f:
                for line in f:
                    if line.startswith("slug:") and topic_slug in line:
                        return d
    return None


def _get_claim_findings(graph, topic: str) -> dict:
    """Get finding info for each claim.

    Returns dict mapping claim_id → {finding_id, finding_title, category}.
    """
    result = graph.conn.execute(
        """
        MATCH (c:Claim)-[:CLAIM_IN_FINDING]->(f:Finding)
        WHERE f.topic = $topic
        RETURN c.claim_id, f.finding_id, f.title, f.category
        """,
        parameters={"topic": topic}
    )
    mapping: dict = {}
    while result.has_next():
        row = result.get_next()
        cid, fid, title, category = row
        mapping[cid] = {
            "finding_id": fid,
            "finding_title": title,
            "category": category,
        }
    return mapping


def _get_extract_claims(graph, source_id: str, claim_findings: dict) -> dict:
    """Get claims linked to each extract.

    Returns dict mapping extract_id → list of {claim_id, summary, theme, finding}.
    """
    result = graph.conn.execute(
        """
        MATCH (s:Source)-[:HAS_EXTRACT]->(e:Extract)-[:EXTRACT_SUPPORTS]->(c:Claim)
        WHERE s.source_id = $sid
        RETURN e.extract_id, c.claim_id, c.summary, c.theme
        ORDER BY e.extract_id, c.claim_id
        """,
        parameters={"sid": source_id}
    )
    extract_claims: dict = {}
    seen: set = set()
    while result.has_next():
        row = result.get_next()
        eid, cid, summary, theme = row
        key = (eid, cid)
        if key in seen:
            continue
        seen.add(key)
        if eid not in extract_claims:
            extract_claims[eid] = []
        entry = {
            "claim_id": cid,
            "summary": summary,
            "theme": theme,
        }
        finding = claim_findings.get(cid)
        if finding:
            entry["finding"] = finding
        extract_claims[eid].append(entry)
    return extract_claims


def export_audit(topic: str, graph, output_dir: str, kb_path: str = None) -> dict:
    """Export {topic}/audit.json with source content + extracted blocks."""
    sources = graph.get_sources_by_topic(topic)

    # Find topic directory in knowledge base
    topic_dir = None
    if kb_path:
        topic_dir = _find_topic_dir(kb_path, topic)

    # Pre-fetch claim → finding mapping for the whole topic
    claim_findings = _get_claim_findings(graph, topic)

    audit_sources = []

    for s in sources:
        sid = s["source_id"]
        extracts = graph.get_extracts(sid)

        # Read source markdown
        markdown_data = {"raw_markdown": "", "sections": []}
        if topic_dir and kb_path:
            markdown_data = _read_source_markdown(kb_path, topic_dir, sid)

        # Parse metadata JSON
        metadata = {}
        if s.get("metadata"):
            try:
                metadata = json.loads(s["metadata"]) if isinstance(s["metadata"], str) else s["metadata"]
            except (json.JSONDecodeError, TypeError):
                pass

        # Build embed URL for original source viewing
        embed_url = _build_embed_url(s, metadata)

        # Build extract → claims mapping
        extract_claims = _get_extract_claims(graph, sid, claim_findings)

        extract_list = []
        for e in extracts:
            entry = {
                "id": e["extract_id"],
                "text": e["text"],
                "position": e["position"],
                "section": e.get("section_path", ""),
                "format": e["format"],
                "extract_type": e["extract_type"],
            }
            # Add linked claims if any
            claims = extract_claims.get(e["extract_id"], [])
            if claims:
                entry["claims"] = claims
            extract_list.append(entry)

        # Group extracts by section for easy display
        sections = {}
        for e in extract_list:
            sec = e["section"] or "Ungrouped"
            if sec not in sections:
                sections[sec] = []
            sections[sec].append(e)

        audit_sources.append({
            "id": sid,
            "title": s["title"],
            "author": s["author"],
            "date": s.get("publication_date", ""),
            "type": s["source_type"],
            "url": s["url"],
            "embed_url": embed_url,
            "extract_count": len(extract_list),
            "metadata": metadata,
            "markdown": markdown_data,
            "extracts": extract_list,
            "extract_sections": sections,
        })

    output = {
        "topic": topic,
        "generated": str(date.today()),
        "total_sources": len(audit_sources),
        "sources": audit_sources,
    }

    topic_dir_out = os.path.join(output_dir, topic)
    os.makedirs(topic_dir_out, exist_ok=True)
    with open(os.path.join(topic_dir_out, "audit.json"), "w") as f:
        json.dump(output, f, indent=2)

    return output
