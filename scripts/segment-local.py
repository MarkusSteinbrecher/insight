#!/usr/bin/env python3
"""Segment and classify content blocks locally — no API calls.

Reads content blocks from the knowledge graph, splits into segments,
classifies each segment by type using heuristics, and writes
raw/source-NNN-raw.yaml files.

Usage:
    python3 scripts/segment-local.py ea-for-ai
    python3 scripts/segment-local.py ea-for-ai --source 033
    python3 scripts/segment-local.py ea-for-ai --dry-run
"""

import argparse
import os
import re
import sys
from collections import Counter

import yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOPICS_DIR = os.path.join(ROOT, "knowledge-base", "topics")

SEGMENT_TYPES = [
    "claim", "statistic", "evidence", "definition", "recommendation",
    "context", "methodology", "example", "attribution", "noise",
]

# Minimum blocks to consider a source worth segmenting
MIN_USEFUL_BLOCKS = 5


def find_topic_dir(slug):
    for name in os.listdir(TOPICS_DIR):
        path = os.path.join(TOPICS_DIR, name)
        if not os.path.isdir(path):
            continue
        index_path = os.path.join(path, "_index.md")
        if os.path.exists(index_path):
            with open(index_path) as f:
                for line in f:
                    if line.startswith("slug:") and slug in line:
                        return path
    return None


def blocks_to_segments(blocks):
    """Convert content blocks into segments."""
    segments = []
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
            segments.append({
                "text": text, "section": section,
                "position": position, "source_format": "heading",
            })
            continue

        if fmt in ("bullet", "table_cell", "table_row", "caption"):
            position += 1
            segments.append({
                "text": text, "section": section,
                "position": position,
                "source_format": "bullet" if fmt == "bullet" else "prose",
            })
            continue

        if fmt == "quote":
            position += 1
            segments.append({
                "text": text, "section": section,
                "position": position, "source_format": "quote",
            })
            continue

        # Prose: split long blocks into sentences
        if len(text) > 300:
            for sent in _split_sentences(text):
                sent = sent.strip()
                if not sent or len(sent) < 10:
                    continue
                position += 1
                segments.append({
                    "text": sent, "section": section,
                    "position": position, "source_format": "prose",
                })
        else:
            position += 1
            segments.append({
                "text": text, "section": section,
                "position": position, "source_format": "prose",
            })

    return segments


def _split_sentences(text):
    protected = text
    for abbr in ["Mr.", "Mrs.", "Dr.", "Prof.", "Inc.", "Ltd.", "Corp.",
                 "vs.", "etc.", "e.g.", "i.e.", "Fig.", "No.", "Vol."]:
        protected = protected.replace(abbr, abbr.replace(".", "@@DOT@@"))
    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z"\'])', protected)
    return [p.replace("@@DOT@@", ".") for p in parts]


# --- Heuristic classification ---

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
    re.compile(r'\[\d+\]'),  # reference markers
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


def classify_segment(text, source_format, section):
    """Classify a segment using heuristics. Returns type string."""
    # Headings are noise (structural) unless very short section labels
    if source_format == "heading":
        # Short structural headings
        if len(text) < 60:
            return "noise"
        # Longer headings that make a claim
        return "claim"

    # Check noise first
    for pat in _NOISE_PATTERNS:
        if pat.search(text):
            return "noise"

    # Very short text is likely noise
    if len(text) < 20:
        return "noise"

    # Statistics — numbers with units or percentages
    if _STAT_PATTERN.search(text):
        # Could be statistic or evidence-with-numbers
        if any(p.search(text) for p in _EVIDENCE_PATTERNS):
            return "evidence"
        return "statistic"

    # Attribution
    for pat in _ATTRIBUTION_PATTERNS:
        if pat.search(text):
            return "attribution"

    # Methodology
    for pat in _METHODOLOGY_PATTERNS:
        if pat.search(text):
            return "methodology"

    # Definitions
    for pat in _DEFINITION_PATTERNS:
        if pat.search(text):
            return "definition"

    # Examples
    for pat in _EXAMPLE_PATTERNS:
        if pat.search(text):
            return "example"

    # Recommendations
    for pat in _RECOMMENDATION_PATTERNS:
        if pat.search(text):
            return "recommendation"

    # Evidence
    for pat in _EVIDENCE_PATTERNS:
        if pat.search(text):
            return "evidence"

    # Quotes from interviews are often evidence
    if source_format == "quote":
        return "evidence"

    # Default: if the sentence makes an assertion, it's a claim; otherwise context
    # Heuristic: sentences with strong verbs or "is/are/will" patterns are claims
    if re.search(r'\b(is|are|will|can|enables?|requires?|transforms?|drives?|creates?|allows?)\b', text, re.I):
        # Check if it's more like context (background/scene-setting)
        if re.match(r'^(in |the |this |these |that |it |we |our |a |an )', text, re.I) and len(text) < 100:
            return "context"
        return "claim"

    return "context"


def format_raw_yaml(source_id, meta, segments):
    """Build the raw YAML structure with classifications."""
    full_segments = []
    for seg in segments:
        seg_type = classify_segment(seg["text"], seg["source_format"], seg["section"])
        entry = {
            "id": f"seg-{seg['position']:03d}",
            "text": seg["text"],
            "type": seg_type,
            "section": seg["section"],
            "position": seg["position"],
            "source_format": seg["source_format"],
        }
        full_segments.append(entry)

    type_counts = Counter(s["type"] for s in full_segments)
    total = len(full_segments)
    composition = {}
    for t in SEGMENT_TYPES:
        count = type_counts.get(t, 0)
        pct = round(count / total * 100, 1) if total > 0 else 0.0
        composition[t] = {"count": count, "pct": pct}

    noise_count = type_counts.get("noise", 0)
    signal_ratio = round((total - noise_count) / total * 100, 1) if total > 0 else 0.0

    return {
        "source_id": source_id,
        "title": meta.get("title", ""),
        "url": meta.get("url", ""),
        "author": meta.get("author", ""),
        "date": str(meta.get("date", meta.get("publication_date", ""))),
        "total_segments": total,
        "composition": composition,
        "signal_ratio": signal_ratio,
        "segments": full_segments,
    }


def write_raw_yaml(raw_data, output_path):
    """Write the raw YAML file."""
    lines = []
    lines.append(f'source_id: {raw_data["source_id"]}')
    title_escaped = raw_data["title"].replace('"', '\\"')
    lines.append(f'title: "{title_escaped}"')
    lines.append(f'url: "{raw_data["url"]}"')
    author_escaped = raw_data["author"].replace('"', '\\"')
    lines.append(f'author: "{author_escaped}"')
    lines.append(f'date: {raw_data["date"]}')
    lines.append(f'total_segments: {raw_data["total_segments"]}')
    lines.append("")
    lines.append("composition:")
    for t in SEGMENT_TYPES:
        c = raw_data["composition"][t]
        lines.append(f'  {t}: {{ count: {c["count"]}, pct: {c["pct"]} }}')
    lines.append("")
    lines.append(f'signal_ratio: {raw_data["signal_ratio"]}')
    lines.append("")
    lines.append("segments:")

    for seg in raw_data["segments"]:
        lines.append(f'  - id: {seg["id"]}')
        text_escaped = seg["text"].replace('"', '\\"')
        lines.append(f'    text: "{text_escaped}"')
        lines.append(f'    type: {seg["type"]}')
        section_escaped = seg["section"].replace('"', '\\"')
        lines.append(f'    section: "{section_escaped}"')
        lines.append(f'    position: {seg["position"]}')
        lines.append(f'    source_format: {seg["source_format"]}')
        lines.append("")

    with open(output_path, "w") as f:
        f.write("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description="Segment content blocks locally (no API)")
    parser.add_argument("topic", help="Topic slug")
    parser.add_argument("--source", type=int, help="Process only this source number")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = parser.parse_args()

    from insight.graph import InsightGraph

    topic_dir = find_topic_dir(args.topic)
    if not topic_dir:
        print(f"Error: Topic '{args.topic}' not found")
        sys.exit(1)

    raw_dir = os.path.join(topic_dir, "raw")
    os.makedirs(raw_dir, exist_ok=True)

    graph = InsightGraph()
    graph.init_schema()

    sources = graph.get_sources_by_topic(args.topic)
    sources.sort(key=lambda s: s["source_id"])

    if args.source:
        filter_id = f"{args.topic}:source-{args.source:03d}"
        sources = [s for s in sources if s["source_id"] == filter_id]

    print(f"Topic: {args.topic} ({os.path.basename(topic_dir)})")
    print(f"Sources: {len(sources)}")

    total_segments = 0
    succeeded = 0
    skipped = 0
    skipped_sources = []

    for s in sources:
        sid = s["source_id"]
        blocks = graph.get_content_blocks(sid)

        if len(blocks) < MIN_USEFUL_BLOCKS:
            skipped += 1
            skipped_sources.append((sid, len(blocks), s["title"][:50]))
            continue

        segments = blocks_to_segments(blocks)
        if not segments:
            skipped += 1
            skipped_sources.append((sid, 0, s["title"][:50]))
            continue

        meta = {
            "title": s.get("title", ""),
            "url": s.get("url", ""),
            "author": s.get("author", ""),
            "publication_date": s.get("publication_date", ""),
        }

        raw_data = format_raw_yaml(sid, meta, segments)
        total_segments += raw_data["total_segments"]

        # Top types
        comp = raw_data["composition"]
        top_types = sorted(
            [(t, comp[t]["count"]) for t in SEGMENT_TYPES if comp[t]["count"] > 0],
            key=lambda x: -x[1],
        )
        top_str = ", ".join(f"{t}:{c}" for t, c in top_types[:4])

        num_match = re.search(r"source-(\d+)$", sid)
        source_num = num_match.group(1) if num_match else "000"

        if args.dry_run:
            print(f"  [{sid}] {len(blocks)} blocks → {len(segments)} segs, "
                  f"signal: {raw_data['signal_ratio']}% ({top_str})")
        else:
            raw_path = os.path.join(raw_dir, f"source-{source_num}-raw.yaml")
            write_raw_yaml(raw_data, raw_path)
            print(f"  [{sid}] {len(segments)} segs, signal: {raw_data['signal_ratio']}% ({top_str})")

        succeeded += 1

    print(f"\n{'='*60}")
    print(f"Done. {succeeded} segmented, {skipped} skipped, {total_segments} total segments.")

    if skipped_sources:
        print(f"\nSkipped (< {MIN_USEFUL_BLOCKS} blocks):")
        for sid, bc, title in skipped_sources:
            print(f"  {sid}: {bc} blocks — {title}")

    graph.close()


if __name__ == "__main__":
    main()
