#!/usr/bin/env python3
"""Build Extract nodes from ContentBlocks in the knowledge graph.

Reads ContentBlocks for a topic, splits long prose into atomic units,
classifies each by type (claim, statistic, evidence, etc.), and stores
as Extract nodes linked directly to Source.

Usage:
    python3 scripts/build-extracts.py ea-for-ai
    python3 scripts/build-extracts.py ea-for-ai --dry-run
"""

import argparse
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# --- Sentence splitting ---

_ABBREVS = {"Mr.", "Mrs.", "Dr.", "Prof.", "Inc.", "Ltd.", "Corp.",
            "vs.", "etc.", "e.g.", "i.e.", "Fig.", "No.", "Vol.",
            "St.", "Jr.", "Sr.", "Dept.", "approx.", "est."}


def _split_sentences(text):
    protected = text
    for abbr in _ABBREVS:
        protected = protected.replace(abbr, abbr.replace(".", "@@DOT@@"))
    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z"\'\(])', protected)
    return [p.replace("@@DOT@@", ".") for p in parts]


# --- Heuristic classification (from segment-local.py) ---

_STAT_PATTERN = re.compile(
    r'(\d+\.?\d*)\s*(%|percent|billion|million|trillion|x\b|fold|times|bps|pp)|'
    r'\$\s*\d|'
    r'\d+\s*(out of|of the|respondents|organizations|companies|executives|leaders|firms)',
    re.IGNORECASE,
)

_RECOMMENDATION_PATTERNS = [
    re.compile(r'\b(should|must|need to|needs to|ought to|have to|recommend|advise)\b', re.I),
    re.compile(r'\b(best practice|key (step|action|priority)|action item|takeaway)\b', re.I),
    re.compile(r'^(ensure|establish|invest|implement|develop|create|build|adopt|prioritize|define|align)\b', re.I),
]

_DEFINITION_PATTERNS = [
    re.compile(r'\b(is defined as|refers to|is the (process|practice|concept|approach|ability)|means that)\b', re.I),
    re.compile(r'\bwe define\b', re.I),
    re.compile(r'^[A-Z][a-zA-Z\s]+ (is|are) (a|an|the) ', re.I),
]

_METHODOLOGY_PATTERNS = [
    re.compile(r'\b(survey|surveyed|interview|interviewed|methodology|sample size|respondents|we (asked|analyzed|examined|studied|collected|conducted))\b', re.I),
    re.compile(r'\b(research (method|design|approach)|data collection|sample of|n\s*=\s*\d)\b', re.I),
]

_EXAMPLE_PATTERNS = [
    re.compile(r'\b(for (example|instance)|such as|case study|case in point|consider the|one (company|organization|example))\b', re.I),
    re.compile(r'\b(illustrat|anecdot|real-world example|in practice)\b', re.I),
]

_ATTRIBUTION_PATTERNS = [
    re.compile(r'\b(according to|as (noted|reported|stated|argued|described) by|cited by|per\s+[A-Z])\b', re.I),
    re.compile(r'\bsource:\s', re.I),
    re.compile(r'\[\d+\]'),
]

_NOISE_PATTERNS = [
    re.compile(r'^(menu|subscribe|sign up|log in|cookie|privacy|share|follow us|download|read more|click here|learn more|contact us|all rights reserved|copyright)', re.I),
    re.compile(r'^(checking your browser|performing security verification|just a moment|verification successful|waiting for)', re.I),
    re.compile(r'^(alerts alerts|manage content|download pdf|download references|request permissions)', re.I),
    re.compile(r'^\s*\d+\s*min(ute)?\s*read\s*$', re.I),
    re.compile(r'^(written by|reviewed by|published|updated|posted)\b.*\d{4}', re.I),
]

_EVIDENCE_PATTERNS = [
    re.compile(r'\b(data shows|evidence suggests|research (found|shows|indicates|reveals)|study (found|shows)|findings (show|indicate|suggest|reveal))\b', re.I),
    re.compile(r'\b(demonstrated|observed|measured|confirmed by|validated by)\b', re.I),
]


def classify_extract(text, fmt):
    """Classify an extract using heuristics. Returns type string."""
    if fmt == "heading":
        return "noise" if len(text) < 60 else "assertion"

    for pat in _NOISE_PATTERNS:
        if pat.search(text):
            return "noise"

    if len(text) < 20:
        return "noise"

    if _STAT_PATTERN.search(text):
        if any(p.search(text) for p in _EVIDENCE_PATTERNS):
            return "evidence"
        return "statistic"

    for pat in _ATTRIBUTION_PATTERNS:
        if pat.search(text):
            return "attribution"

    for pat in _METHODOLOGY_PATTERNS:
        if pat.search(text):
            return "methodology"

    for pat in _DEFINITION_PATTERNS:
        if pat.search(text):
            return "definition"

    for pat in _EXAMPLE_PATTERNS:
        if pat.search(text):
            return "example"

    for pat in _RECOMMENDATION_PATTERNS:
        if pat.search(text):
            return "recommendation"

    for pat in _EVIDENCE_PATTERNS:
        if pat.search(text):
            return "evidence"

    if fmt == "quote":
        return "evidence"

    if re.search(r'\b(is|are|will|can|enables?|requires?|transforms?|drives?|creates?|allows?)\b', text, re.I):
        if re.match(r'^(in |the |this |these |that |it |we |our |a |an )', text, re.I) and len(text) < 100:
            return "context"
        return "assertion"

    return "context"


def blocks_to_extracts(blocks):
    """Convert ContentBlocks into atomic extracts with classification."""
    extracts = []
    position = 0

    for block in blocks:
        text = block.get("text", "").strip()
        fmt = block.get("format", "prose")
        section = block.get("section_path", "")

        if not text or len(text) < 10:
            continue
        if fmt == "figure" or block.get("image_path"):
            continue

        if fmt == "heading":
            position += 1
            extracts.append({
                "text": text, "format": "heading",
                "section_path": section, "position": position,
                "extract_type": classify_extract(text, "heading"),
            })
            continue

        if fmt in ("bullet", "table_cell", "table_row", "caption"):
            position += 1
            extract_fmt = "bullet" if fmt == "bullet" else fmt
            extracts.append({
                "text": text, "format": extract_fmt,
                "section_path": section, "position": position,
                "extract_type": classify_extract(text, extract_fmt),
            })
            continue

        if fmt == "quote":
            position += 1
            extracts.append({
                "text": text, "format": "quote",
                "section_path": section, "position": position,
                "extract_type": classify_extract(text, "quote"),
            })
            continue

        # Prose: split long text into sentences for atomicity
        if len(text) > 300:
            for sent in _split_sentences(text):
                sent = sent.strip()
                if not sent or len(sent) < 10:
                    continue
                position += 1
                extracts.append({
                    "text": sent, "format": "prose",
                    "section_path": section, "position": position,
                    "extract_type": classify_extract(sent, "prose"),
                })
        else:
            position += 1
            extracts.append({
                "text": text, "format": "prose",
                "section_path": section, "position": position,
                "extract_type": classify_extract(text, "prose"),
            })

    return extracts


def main():
    parser = argparse.ArgumentParser(description="Build Extract nodes from ContentBlocks")
    parser.add_argument("topic", help="Topic slug")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = parser.parse_args()

    from insight.graph import InsightGraph

    graph = InsightGraph()
    graph.init_schema()

    sources = graph.get_sources_by_topic(args.topic)
    sources.sort(key=lambda s: s["source_id"])

    print(f"Topic: {args.topic}")
    print(f"Sources: {len(sources)}")

    if not args.dry_run:
        # Clear existing extracts for this topic
        print("Clearing existing extracts...")
        graph.conn.execute(
            """
            MATCH (s:Source)-[:HAS_EXTRACT]->(e:Extract)
            WHERE s.topic = $topic
            DETACH DELETE e
            """,
            parameters={"topic": args.topic}
        )

    total_extracts = 0
    type_totals = Counter()

    for s in sources:
        sid = s["source_id"]
        blocks = graph.get_content_blocks(sid)

        if len(blocks) < 3:
            continue

        extracts = blocks_to_extracts(blocks)
        if not extracts:
            continue

        type_counts = Counter(e["extract_type"] for e in extracts)
        noise = type_counts.get("noise", 0)
        signal = len(extracts) - noise

        for t, c in type_counts.items():
            type_totals[t] += c

        top = sorted(type_counts.items(), key=lambda x: -x[1])[:4]
        top_str = ", ".join(f"{t}:{c}" for t, c in top)

        if not args.dry_run:
            for e in extracts:
                eid = f"{sid}:extract-{e['position']:03d}"
                graph.add_extract(
                    extract_id=eid,
                    source_id=sid,
                    text=e["text"],
                    position=e["position"],
                    format=e["format"],
                    extract_type=e["extract_type"],
                    section_path=e["section_path"],
                )

        total_extracts += len(extracts)
        print(f"  [{sid}] {len(blocks)} blocks → {len(extracts)} extracts, signal: {signal} ({top_str})")

    print(f"\n{'='*60}")
    print(f"Total: {total_extracts} extracts from {len(sources)} sources")
    print(f"\nType breakdown:")
    for t, c in sorted(type_totals.items(), key=lambda x: -x[1]):
        pct = round(c / total_extracts * 100, 1) if total_extracts else 0
        print(f"  {t}: {c} ({pct}%)")

    graph.close()
    prefix = "DRY RUN — " if args.dry_run else ""
    print(f"\n{prefix}Done.")


if __name__ == "__main__":
    main()
