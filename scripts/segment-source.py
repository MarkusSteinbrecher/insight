#!/usr/bin/env python3
"""Segment extracted content blocks into classified raw YAML files.

Reads content blocks from the knowledge graph (KuzuDB), groups them into
segments, then classifies each segment via a single Claude API call per
source. Writes raw/source-NNN-raw.yaml files.

Usage:
    python3 scripts/segment-source.py ea-for-ai              # All unsegmented sources
    python3 scripts/segment-source.py ea-for-ai --source 033  # Specific source
    python3 scripts/segment-source.py ea-for-ai --dry-run     # Preview segments only
    python3 scripts/segment-source.py ea-for-ai --parallel 5  # 5 concurrent sources

Requires:
    - pip install anthropic pyyaml
    - ANTHROPIC_API_KEY environment variable
"""

import argparse
import asyncio
import json
import os
import re
import sys
from collections import Counter

import yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOPICS_DIR = os.path.join(ROOT, "knowledge-base", "topics")

MODEL = "claude-sonnet-4-5-20250929"
MAX_TOKENS = 16000
# Max segments to send in one API call; larger sources are batched
BATCH_SIZE = 200

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
        # Check _index.md for slug
        index_path = os.path.join(path, "_index.md")
        if os.path.exists(index_path):
            with open(index_path) as f:
                for line in f:
                    if line.startswith("slug:") and slug in line:
                        return path
    return None


def load_frontmatter(filepath):
    """Load YAML frontmatter from a markdown file."""
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


def blocks_to_segments(blocks):
    """Convert content blocks from the graph into segments for classification.

    Each content block becomes one or more segments. Prose blocks with multiple
    sentences are split. Short blocks (<20 chars) are skipped.
    """
    segments = []
    position = 0

    for block in blocks:
        text = block.get("text", "").strip()
        fmt = block.get("format", "prose")
        section = block.get("section_path", "")

        if not text or len(text) < 10:
            continue

        # Skip image blocks (they have image_path but minimal text)
        if fmt == "figure" or block.get("image_path"):
            continue

        # Headings become a single segment
        if fmt == "heading":
            position += 1
            segments.append({
                "text": text,
                "section": section,
                "position": position,
                "source_format": "heading",
            })
            continue

        # Bullets and table cells: one segment each
        if fmt in ("bullet", "table_cell", "table_row", "caption"):
            position += 1
            segments.append({
                "text": text,
                "section": section,
                "position": position,
                "source_format": fmt if fmt == "bullet" else "prose",
            })
            continue

        # Quotes
        if fmt == "quote":
            position += 1
            segments.append({
                "text": text,
                "section": section,
                "position": position,
                "source_format": "quote",
            })
            continue

        # Prose: split into sentences if long
        if len(text) > 300:
            sentences = _split_sentences(text)
            for sent in sentences:
                sent = sent.strip()
                if not sent or len(sent) < 10:
                    continue
                position += 1
                segments.append({
                    "text": sent,
                    "section": section,
                    "position": position,
                    "source_format": "prose",
                })
        else:
            position += 1
            segments.append({
                "text": text,
                "section": section,
                "position": position,
                "source_format": "prose",
            })

    return segments


def _split_sentences(text):
    """Split text into sentences. Handles common abbreviations."""
    protected = text
    abbrevs = ["Mr.", "Mrs.", "Dr.", "Prof.", "Inc.", "Ltd.", "Corp.",
               "vs.", "etc.", "e.g.", "i.e.", "Fig.", "No.", "Vol."]
    for abbr in abbrevs:
        protected = protected.replace(abbr, abbr.replace(".", "@@DOT@@"))

    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z"\'])', protected)
    return [p.replace("@@DOT@@", ".") for p in parts]


def format_raw_yaml(source_id, meta, segments, classifications):
    """Build the raw YAML structure."""
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
        "date": str(meta.get("date", "")),
        "total_segments": total,
        "composition": composition,
        "signal_ratio": signal_ratio,
        "segments": full_segments,
    }


def write_raw_yaml(raw_data, output_path):
    """Write the raw YAML file with flow-style composition."""
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
        text_escaped = seg["text"].replace('"', '\\"')
        lines.append(f'    text: "{text_escaped}"')
        lines.append(f'    type: {seg["type"]}')
        section_escaped = seg["section"].replace('"', '\\"')
        lines.append(f'    section: "{section_escaped}"')
        lines.append(f'    position: {seg["position"]}')
        lines.append(f'    source_format: {seg["source_format"]}')
        if seg.get("metadata"):
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


async def classify_segments_batch(segments, topic_title, source_id, batch_label=""):
    """Call Claude API to classify a batch of segments."""
    import anthropic

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

    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)

    try:
        classifications = json.loads(text)
    except json.JSONDecodeError as e:
        label = f" {batch_label}" if batch_label else ""
        print(f"  [Warning] Failed to parse API response for {source_id}{label}: {e}")
        print(f"  Response starts with: {text[:200]}")
        classifications = [
            {"id": f"seg-{s['position']:03d}", "type": "context"}
            for s in segments
        ]

    return classifications


async def classify_segments(segments, topic_title, source_id):
    """Classify all segments, batching if needed."""
    if len(segments) <= BATCH_SIZE:
        return await classify_segments_batch(segments, topic_title, source_id)

    # Batch large sources
    all_classifications = []
    num_batches = (len(segments) + BATCH_SIZE - 1) // BATCH_SIZE
    for i in range(0, len(segments), BATCH_SIZE):
        batch = segments[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        print(f"  [{source_id}] Classifying batch {batch_num}/{num_batches} ({len(batch)} segments)...")
        classifications = await classify_segments_batch(
            batch, topic_title, source_id,
            batch_label=f"batch {batch_num}/{num_batches}"
        )
        all_classifications.extend(classifications)

    return all_classifications


async def process_source(source_id, graph, raw_dir, topic_title, dry_run=False):
    """Process a single source from the graph into a raw YAML file."""
    source = graph.get_source(source_id)
    if not source:
        print(f"  [{source_id}] Not found in graph, skipping")
        return None

    # Get content blocks from graph
    blocks = graph.get_content_blocks(source_id)
    if not blocks:
        print(f"  [{source_id}] No content blocks, skipping")
        return None

    # Convert blocks to segments
    segments = blocks_to_segments(blocks)
    if not segments:
        print(f"  [{source_id}] No segments after processing, skipping")
        return None

    # Source number for file naming
    num_match = re.search(r"source-(\d+)$", source_id)
    source_num = num_match.group(1) if num_match else "000"
    raw_path = os.path.join(raw_dir, f"source-{source_num}-raw.yaml")

    print(f"  [{source_id}] {len(blocks)} blocks → {len(segments)} segments")

    if dry_run:
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
    meta = {
        "title": source.get("title", ""),
        "url": source.get("url", ""),
        "author": source.get("author", ""),
        "date": source.get("publication_date", ""),
    }
    raw_data = format_raw_yaml(source_id, meta, segments, classifications)
    os.makedirs(raw_dir, exist_ok=True)
    write_raw_yaml(raw_data, raw_path)

    comp = raw_data["composition"]
    top_types = sorted(
        [(t, comp[t]["count"]) for t in SEGMENT_TYPES if comp[t]["count"] > 0],
        key=lambda x: -x[1],
    )
    top_str = ", ".join(f"{t}:{c}" for t, c in top_types[:4])
    print(f"  [{source_id}] Written → {len(segments)} segments, "
          f"signal: {raw_data['signal_ratio']}% ({top_str})")

    return {
        "source_id": source_id,
        "segments": raw_data["total_segments"],
        "signal_ratio": raw_data["signal_ratio"],
        "status": "done",
    }


async def run(topic_slug, source_filter=None, dry_run=False, parallel=3):
    """Main async entry point."""
    from insight.graph import InsightGraph

    topic_dir = find_topic_dir(topic_slug)
    if not topic_dir:
        print(f"Error: Topic '{topic_slug}' not found in {TOPICS_DIR}")
        sys.exit(1)

    topic_name = os.path.basename(topic_dir)
    index_path = os.path.join(topic_dir, "_index.md")
    index_meta = load_frontmatter(index_path)
    topic_title = index_meta.get("title", topic_name)

    raw_dir = os.path.join(topic_dir, "raw")

    graph = InsightGraph()
    graph.init_schema()

    # Get all sources from the graph
    all_sources = graph.get_sources_by_topic(topic_slug)
    all_sources.sort(key=lambda s: s["source_id"])

    print(f"Topic: {topic_title}")
    print(f"Sources in graph: {len(all_sources)}")

    if source_filter:
        filter_id = f"{topic_slug}:source-{source_filter:>03}"
        all_sources = [s for s in all_sources if s["source_id"] == filter_id]
        if not all_sources:
            print(f"Error: {filter_id} not found")
            sys.exit(1)

    # Filter out already-segmented sources (unless specific source requested)
    if not source_filter:
        pending = []
        for s in all_sources:
            num_match = re.search(r"source-(\d+)$", s["source_id"])
            if not num_match:
                continue
            raw_path = os.path.join(raw_dir, f"source-{num_match.group(1)}-raw.yaml")
            if not os.path.exists(raw_path):
                pending.append(s)
        all_sources = pending

    if not all_sources:
        print("\nNo unsegmented sources found. All sources already have raw files.")
        graph.close()
        sys.exit(0)

    print(f"\n{len(all_sources)} source(s) to segment:")
    for s in all_sources:
        bc = graph.count_content_blocks(s["source_id"])
        print(f"  {s['source_id']:30s}  {bc:4d} blocks  {s['title'][:50]}")

    if not dry_run and not os.environ.get("ANTHROPIC_API_KEY"):
        print("\nError: ANTHROPIC_API_KEY environment variable not set")
        graph.close()
        sys.exit(1)

    # Process with concurrency limit
    semaphore = asyncio.Semaphore(parallel)
    results = []

    async def bounded_process(source):
        async with semaphore:
            return await process_source(
                source["source_id"], graph, raw_dir, topic_title, dry_run
            )

    print(f"\nProcessing (parallel={parallel})...\n")
    tasks = [bounded_process(s) for s in all_sources]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Summary
    succeeded = sum(1 for r in results if isinstance(r, dict) and r and r.get("status") == "done")
    dry_runs = sum(1 for r in results if isinstance(r, dict) and r and r.get("status") == "dry-run")
    failed = sum(1 for r in results if isinstance(r, Exception))
    skipped = len(results) - succeeded - dry_runs - failed
    total_segments = sum(
        r["segments"] for r in results
        if isinstance(r, dict) and r and r.get("segments")
    )

    if failed > 0:
        print("\nErrors:")
        for i, r in enumerate(results):
            if isinstance(r, Exception):
                print(f"  {all_sources[i]['source_id']}: {r}")

    print(f"\n{'='*60}")
    if dry_run:
        print(f"Dry run: {len(all_sources)} sources, ~{total_segments} segments total")
    else:
        print(f"Done. {succeeded} succeeded, {failed} failed, {skipped} skipped.")
        print(f"Total segments: {total_segments}")
    print(f"{'='*60}")

    graph.close()
    return succeeded


def main():
    parser = argparse.ArgumentParser(
        description="Segment extracted content blocks into raw YAML files"
    )
    parser.add_argument("topic", help="Topic slug")
    parser.add_argument("--source", type=int, help="Process only this source number")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview segments without calling API")
    parser.add_argument("--parallel", type=int, default=3,
                        help="Number of concurrent API calls (default: 3)")
    args = parser.parse_args()

    asyncio.run(run(args.topic, args.source, args.dry_run, args.parallel))


if __name__ == "__main__":
    main()
