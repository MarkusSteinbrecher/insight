#!/usr/bin/env python3
"""Segment source notes into raw YAML files for the analysis pipeline.

Splits source markdown into segments deterministically (sentences, bullets,
headings, quotes), then classifies each segment via a single Claude API call
per source. Writes raw/source-NNN-raw.yaml files.

Usage:
    python3 scripts/segment-source.py "EA for AI"              # All unsegmented sources
    python3 scripts/segment-source.py "EA for AI" --source 033 # Specific source
    python3 scripts/segment-source.py "EA for AI" --dry-run    # Preview segments only
    python3 scripts/segment-source.py "EA for AI" --parallel 5 # 5 concurrent sources

Requires:
    - pip install anthropic pyyaml
    - ANTHROPIC_API_KEY environment variable
"""

import argparse
import asyncio
import glob
import json
import os
import re
import sys
from collections import Counter

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOPICS_DIR = os.path.join(ROOT, "knowledge-base", "topics")

MODEL = "claude-sonnet-4-5-20250929"
MAX_TOKENS = 16000

SEGMENT_TYPES = [
    "claim", "statistic", "evidence", "definition", "recommendation",
    "context", "methodology", "example", "attribution", "noise",
]

CLASSIFICATION_PROMPT = """You are a research analyst classifying text segments from a source document about "{topic_title}".

For each segment below, assign exactly one type from this taxonomy:
- claim: An assertion or argument (normative, empirical, predictive, or definitional)
- statistic: A quantified data point with numbers
- evidence: Data or example supporting a claim
- definition: Defining or explaining a term/concept
- recommendation: Prescriptive/actionable statement
- context: Background information, scene-setting
- methodology: How something was studied or done
- example: Illustrative case or anecdote
- attribution: Citing or referencing another source
- noise: Filler, transitions, marketing language, boilerplate, structural headings

For segments of type "statistic", also extract metadata with fields: metric, value, unit, population (when available). If the statistic contains multiple data points, use a data_points array.

For segments of type "claim" or "evidence" that contain direct quotes, extract metadata with fields: speaker, affiliation (when available).

Return a JSON array where each element has:
- "id": the segment id (e.g., "seg-001")
- "type": one of the 10 types above
- "metadata": optional object with type-specific enrichment (omit if not applicable)

IMPORTANT: Return ONLY the JSON array, no other text.

Segments to classify:
{segments_json}"""


def find_topic_dir(slug):
    """Find topic directory by slug or folder name."""
    for name in os.listdir(TOPICS_DIR):
        path = os.path.join(TOPICS_DIR, name)
        if not os.path.isdir(path):
            continue
        if name == slug:
            return path
        if name.lower().replace(" ", "-") == slug.lower().replace(" ", "-"):
            return path
    return None


def load_frontmatter(filepath):
    """Load YAML frontmatter and body from a markdown file."""
    with open(filepath, "r") as f:
        content = f.read()
    if not content.startswith("---"):
        return {}, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content
    try:
        meta = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        meta = {}
    return meta, parts[2].strip()


def split_into_segments(body):
    """Split markdown body into segments deterministically.

    Returns list of dicts: {text, section, position, source_format}
    """
    segments = []
    current_section = "Body"
    position = 0

    lines = body.split("\n")
    # Buffer for accumulating prose sentences
    prose_buffer = []

    def flush_prose():
        nonlocal position
        if not prose_buffer:
            return
        text = " ".join(prose_buffer).strip()
        if not text:
            prose_buffer.clear()
            return
        # Split into sentences
        sentences = _split_sentences(text)
        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue
            position += 1
            segments.append({
                "text": sent,
                "section": current_section,
                "position": position,
                "source_format": "prose",
            })
        prose_buffer.clear()

    for line in lines:
        stripped = line.strip()

        # Empty line — flush prose buffer
        if not stripped:
            flush_prose()
            continue

        # Heading
        heading_match = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading_match:
            flush_prose()
            level = len(heading_match.group(1))
            text = heading_match.group(2).strip()
            current_section = text
            position += 1
            segments.append({
                "text": text,
                "section": current_section,
                "position": position,
                "source_format": "heading",
            })
            continue

        # Bullet/list item
        bullet_match = re.match(r"^[-*+]\s+(.+)$", stripped)
        if bullet_match:
            flush_prose()
            text = bullet_match.group(1).strip()
            position += 1
            segments.append({
                "text": text,
                "section": current_section,
                "position": position,
                "source_format": "bullet",
            })
            continue

        # Numbered list
        num_match = re.match(r"^\d+[.)]\s+(.+)$", stripped)
        if num_match:
            flush_prose()
            text = num_match.group(1).strip()
            position += 1
            segments.append({
                "text": text,
                "section": current_section,
                "position": position,
                "source_format": "bullet",
            })
            continue

        # Block quote
        quote_match = re.match(r"^>\s+(.+)$", stripped)
        if quote_match:
            flush_prose()
            text = quote_match.group(1).strip()
            # Strip trailing attribution like "— Author Name"
            position += 1
            segments.append({
                "text": text,
                "section": current_section,
                "position": position,
                "source_format": "quote",
            })
            continue

        # Regular prose — accumulate
        prose_buffer.append(stripped)

    # Flush any remaining prose
    flush_prose()

    return segments


def _split_sentences(text):
    """Split text into sentences. Handles common abbreviations."""
    # Protect common abbreviations from sentence splitting
    protected = text
    abbrevs = ["Mr.", "Mrs.", "Dr.", "Prof.", "Inc.", "Ltd.", "Corp.",
               "vs.", "etc.", "e.g.", "i.e.", "Fig.", "No.", "Vol."]
    for abbr in abbrevs:
        protected = protected.replace(abbr, abbr.replace(".", "@@DOT@@"))

    # Split on sentence-ending punctuation followed by space + uppercase
    # or end of string
    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z"\'])', protected)

    # Restore abbreviation dots
    return [p.replace("@@DOT@@", ".") for p in parts]


def format_raw_yaml(source_id, meta, segments, classifications):
    """Build the raw YAML structure."""
    # Merge classifications into segments
    class_map = {}
    for c in classifications:
        class_map[c["id"]] = c

    full_segments = []
    for seg in segments:
        seg_id = f"seg-{seg['position']:03d}"
        cls = class_map.get(seg_id, {})
        entry = {
            "id": seg_id,
            "text": seg["text"],
            "type": cls.get("type", "context"),
            "section": seg["section"],
            "position": seg["position"],
            "source_format": seg["source_format"],
        }
        if cls.get("metadata"):
            entry["metadata"] = cls["metadata"]
        full_segments.append(entry)

    # Calculate composition
    type_counts = Counter(s["type"] for s in full_segments)
    total = len(full_segments)
    composition = {}
    for t in SEGMENT_TYPES:
        count = type_counts.get(t, 0)
        pct = round(count / total * 100, 1) if total > 0 else 0.0
        composition[t] = {"count": count, "pct": pct}

    noise_count = type_counts.get("noise", 0)
    signal_ratio = round((total - noise_count) / total * 100, 1) if total > 0 else 0.0

    raw = {
        "source_id": source_id,
        "title": meta.get("title", ""),
        "url": meta.get("url", ""),
        "author": meta.get("author", ""),
        "date": str(meta.get("date", "")),
        "total_segments": total,
        "composition": composition,
        "signal_ratio": signal_ratio,
        "segments": full_segments,
    }
    return raw


def write_raw_yaml(raw_data, output_path):
    """Write the raw YAML file with flow-style composition."""
    # Custom dump: flow style for composition entries
    lines = []
    lines.append(f'source_id: {raw_data["source_id"]}')
    lines.append(f'title: "{raw_data["title"]}"')
    lines.append(f'url: "{raw_data["url"]}"')
    lines.append(f'author: "{raw_data["author"]}"')
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
        # Escape quotes in text
        text_escaped = seg["text"].replace('"', '\\"')
        lines.append(f'    text: "{text_escaped}"')
        lines.append(f'    type: {seg["type"]}')
        section_escaped = seg["section"].replace('"', '\\"')
        lines.append(f'    section: "{section_escaped}"')
        lines.append(f'    position: {seg["position"]}')
        lines.append(f'    source_format: {seg["source_format"]}')
        if seg.get("metadata"):
            # Use yaml.dump for metadata to handle nested structures
            meta_yaml = yaml.dump(
                {"metadata": seg["metadata"]},
                default_flow_style=False,
                allow_unicode=True,
            ).strip()
            for meta_line in meta_yaml.split("\n"):
                lines.append(f"    {meta_line}")
        lines.append("")

    with open(output_path, "w") as f:
        f.write("\n".join(lines))


async def classify_segments(segments, topic_title, source_id):
    """Call Claude API to classify segments. Returns list of classifications."""
    import anthropic

    # Build compact segment list for the prompt
    seg_list = []
    for seg in segments:
        seg_list.append({
            "id": f"seg-{seg['position']:03d}",
            "text": seg["text"],
            "source_format": seg["source_format"],
        })

    prompt = CLASSIFICATION_PROMPT.format(
        topic_title=topic_title,
        segments_json=json.dumps(seg_list, indent=2),
    )

    client = anthropic.AsyncAnthropic()
    response = await client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )

    # Parse response
    text = response.content[0].text.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)

    try:
        classifications = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"  [Warning] Failed to parse API response for {source_id}: {e}")
        print(f"  Response starts with: {text[:200]}")
        # Fall back to all "context"
        classifications = [
            {"id": f"seg-{s['position']:03d}", "type": "context"}
            for s in segments
        ]

    return classifications


async def process_source(source_path, raw_dir, topic_title, dry_run=False):
    """Process a single source file into a raw YAML file."""
    basename = os.path.basename(source_path)
    source_match = re.match(r"source-(\d+)\.md", basename)
    if not source_match:
        return None
    source_num = source_match.group(1)
    source_id = f"source-{source_num}"
    raw_path = os.path.join(raw_dir, f"source-{source_num}-raw.yaml")

    meta, body = load_frontmatter(source_path)
    if not body.strip():
        print(f"  [{source_id}] Empty body, skipping")
        return None

    # Split into segments
    segments = split_into_segments(body)
    if not segments:
        print(f"  [{source_id}] No segments extracted, skipping")
        return None

    print(f"  [{source_id}] {len(segments)} segments extracted")

    if dry_run:
        # Print first few segments as preview
        for seg in segments[:5]:
            print(f"    seg-{seg['position']:03d} [{seg['source_format']}] "
                  f"{seg['text'][:80]}...")
        if len(segments) > 5:
            print(f"    ... and {len(segments) - 5} more")
        return {"source_id": source_id, "segments": len(segments), "status": "dry-run"}

    # Classify via API
    print(f"  [{source_id}] Classifying via API...")
    classifications = await classify_segments(segments, topic_title, source_id)

    # Build and write raw YAML
    raw_data = format_raw_yaml(source_id, meta, segments, classifications)
    os.makedirs(raw_dir, exist_ok=True)
    write_raw_yaml(raw_data, raw_path)

    # Composition summary
    comp = raw_data["composition"]
    top_types = sorted(
        [(t, comp[t]["count"]) for t in SEGMENT_TYPES if comp[t]["count"] > 0],
        key=lambda x: -x[1],
    )
    top_str = ", ".join(f"{t}:{c}" for t, c in top_types[:4])
    print(f"  [{source_id}] Written {raw_path}")
    print(f"  [{source_id}] {raw_data['total_segments']} segments, "
          f"signal: {raw_data['signal_ratio']}% ({top_str})")

    return {
        "source_id": source_id,
        "segments": raw_data["total_segments"],
        "signal_ratio": raw_data["signal_ratio"],
        "status": "done",
    }


async def run(topic_slug, source_filter=None, dry_run=False, parallel=3):
    """Main async entry point."""
    topic_dir = find_topic_dir(topic_slug)
    if not topic_dir:
        print(f"Error: Topic '{topic_slug}' not found in {TOPICS_DIR}")
        sys.exit(1)

    topic_name = os.path.basename(topic_dir)
    index_path = os.path.join(topic_dir, "_index.md")
    index_meta, _ = load_frontmatter(index_path)
    topic_title = index_meta.get("title", topic_name)

    sources_dir = os.path.join(topic_dir, "sources")
    raw_dir = os.path.join(topic_dir, "raw")

    print(f"Topic: {topic_title}")
    print(f"Directory: {topic_dir}")

    # Find source files to process
    all_sources = sorted(glob.glob(os.path.join(sources_dir, "source-*.md")))
    # Exclude _overview.md
    all_sources = [s for s in all_sources if "_overview" not in s]

    if source_filter:
        # Filter to specific source number
        all_sources = [
            s for s in all_sources
            if re.search(rf"source-0*{source_filter}\.md$", s)
        ]
        if not all_sources:
            print(f"Error: source-{source_filter:>03} not found")
            sys.exit(1)

    # Filter out already-segmented sources (unless specific source requested)
    if not source_filter:
        pending = []
        for s in all_sources:
            basename = os.path.basename(s)
            num = re.match(r"source-(\d+)\.md", basename).group(1)
            raw_path = os.path.join(raw_dir, f"source-{num}-raw.yaml")
            if not os.path.exists(raw_path):
                pending.append(s)
        all_sources = pending

    if not all_sources:
        print("\nNo unsegmented sources found. All sources already have raw files.")
        sys.exit(0)

    print(f"\n{len(all_sources)} source(s) to segment:")
    for s in all_sources:
        print(f"  {os.path.basename(s)}")

    if not dry_run and not os.environ.get("ANTHROPIC_API_KEY"):
        print("\nError: ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)

    # Process with concurrency limit
    semaphore = asyncio.Semaphore(parallel)
    results = []

    async def bounded_process(source_path):
        async with semaphore:
            return await process_source(source_path, raw_dir, topic_title, dry_run)

    print(f"\nProcessing (parallel={parallel})...\n")
    tasks = [bounded_process(s) for s in all_sources]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Summary
    succeeded = sum(1 for r in results if isinstance(r, dict) and r and r.get("status") == "done")
    failed = sum(1 for r in results if isinstance(r, Exception))
    skipped = len(results) - succeeded - failed

    if failed > 0:
        print("\nErrors:")
        for i, r in enumerate(results):
            if isinstance(r, Exception):
                print(f"  {os.path.basename(all_sources[i])}: {r}")

    print(f"\n{'='*60}")
    status = "dry-run preview" if dry_run else f"{succeeded} succeeded"
    print(f"Done. {status}, {failed} failed, {skipped} skipped.")
    print(f"{'='*60}")

    return succeeded


def main():
    parser = argparse.ArgumentParser(
        description="Segment source notes into raw YAML files"
    )
    parser.add_argument("topic", help="Topic slug or name")
    parser.add_argument("--source", type=int, help="Process only this source number")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview segments without calling API")
    parser.add_argument("--parallel", type=int, default=3,
                        help="Number of concurrent API calls (default: 3)")
    args = parser.parse_args()

    asyncio.run(run(args.topic, args.source, args.dry_run, args.parallel))


if __name__ == "__main__":
    main()
