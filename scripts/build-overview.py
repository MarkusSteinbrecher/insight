#!/usr/bin/env python3
"""Build _overview.md for each topic from knowledge base state.

Scans source notes, raw segmentation files, and claim alignment to determine
per-source pipeline status. Generates a markdown overview with status table,
type breakdown, and institution breakdown.

Output: knowledge-base/topics/{topic}/sources/_overview.md
"""

import glob
import os
import re
import sys
from collections import defaultdict
from datetime import datetime

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOPICS_DIR = os.path.join(ROOT, "knowledge-base", "topics")


def parse_frontmatter(filepath):
    """Parse YAML frontmatter from a markdown file."""
    with open(filepath, "r") as f:
        content = f.read()

    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return {}

    fm = {}
    for line in match.group(1).split("\n"):
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("- "):
            continue
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if val:
                fm[key] = val
    return fm


def get_analyzed_sources(topic_dir):
    """Return set of source IDs referenced in claim-alignment.yaml."""
    path = os.path.join(topic_dir, "extractions", "claim-alignment.yaml")
    if not os.path.exists(path):
        return set()

    with open(path, "r") as f:
        data = yaml.safe_load(f)
    if not data:
        return set()

    source_ids = set()

    # Scan canonical claims
    for claim in data.get("canonical_claims", []) or []:
        for src in claim.get("supporting_sources", []) or []:
            sid = src.get("source_id", "")
            if sid:
                source_ids.add(sid)

    # Scan unique claims
    for claim in data.get("unique_claims", []) or []:
        sid = claim.get("source", "")
        if sid:
            source_ids.add(sid)
        for seg in claim.get("segments", []) or []:
            if isinstance(seg, dict):
                sid = seg.get("source_id", "")
                if sid:
                    source_ids.add(sid)

    # Scan contradictions
    for ct in data.get("contradictions", []) or []:
        for pos in ct.get("positions", []) or []:
            sid = pos.get("source_id", "")
            if sid:
                source_ids.add(sid)

    return source_ids


def get_queued_sources(topic_dir):
    """Return list of URLs/documents from source-input.yaml that are pending."""
    path = os.path.join(topic_dir, "source-input.yaml")
    if not os.path.exists(path):
        return []

    with open(path, "r") as f:
        data = yaml.safe_load(f)
    if not data:
        return []

    return data.get("sources", []) or []


def get_source_status(source_id, raw_dir, analyzed_sources):
    """Determine pipeline status for a source.

    Returns: analyzed | segmented | gathered
    """
    if source_id in analyzed_sources:
        return "analyzed"
    raw_path = os.path.join(raw_dir, f"{source_id}-raw.yaml")
    if os.path.exists(raw_path):
        return "segmented"
    return "gathered"


def get_updated_date(source_id, sources_dir, raw_dir):
    """Get the most recent modification date for a source's files."""
    candidates = [
        os.path.join(sources_dir, f"{source_id}.md"),
        os.path.join(raw_dir, f"{source_id}-raw.yaml"),
    ]
    newest = 0
    for path in candidates:
        if os.path.exists(path):
            mtime = os.path.getmtime(path)
            if mtime > newest:
                newest = mtime
    if newest > 0:
        return datetime.fromtimestamp(newest).strftime("%Y-%m-%d")
    return ""


def shorten_author(author):
    """Shorten long author strings for the table."""
    if len(author) > 30:
        # Try to abbreviate multi-author papers
        if "," in author:
            parts = [p.strip() for p in author.split(",")]
            if len(parts) > 2:
                return f"{parts[0]} et al."
        if "/" in author:
            parts = [p.strip() for p in author.split("/")]
            return parts[0]
    return author


# Institution detection rules: (keyword_in_author_or_url, institution_label)
INSTITUTION_RULES = [
    # Author-based matches
    (lambda a, u: "deloitte" in a.lower(), "Deloitte"),
    (lambda a, u: "forrester" in a.lower(), "Forrester"),
    (lambda a, u: "open group" in a.lower(), "The Open Group"),
    (lambda a, u: "mit " in a.lower() or " mit)" in a.lower() or "cisr" in a.lower() or a.lower().endswith("mit"), "MIT (CISR + Sloan)"),
    (lambda a, u: "gartner" in a.lower(), "Gartner"),
    (lambda a, u: "mckinsey" in a.lower(), "McKinsey"),
    # URL-based matches (for sources without org in author)
    (lambda a, u: "deloitte.com" in u, "Deloitte"),
    (lambda a, u: "forrester.com" in u, "Forrester"),
    (lambda a, u: "opengroup.org" in u, "The Open Group"),
    (lambda a, u: "mit.edu" in u, "MIT (CISR + Sloan)"),
    (lambda a, u: "ieeexplore.ieee.org" in u, "IEEE"),
    (lambda a, u: "arxiv.org" in u, "arXiv"),
    (lambda a, u: "gartner.com" in u, "Gartner"),
    (lambda a, u: "mckinsey.com" in u, "McKinsey"),
]


def detect_institution(author, url):
    """Detect institution from author string and URL."""
    for rule_fn, label in INSTITUTION_RULES:
        if rule_fn(author, url):
            return label
    return None


def build_overview(topic_dir):
    """Build _overview.md for a single topic."""
    topic_name = os.path.basename(topic_dir)
    sources_dir = os.path.join(topic_dir, "sources")
    raw_dir = os.path.join(topic_dir, "raw")

    # Read topic metadata
    index_path = os.path.join(topic_dir, "_index.md")
    topic_meta = parse_frontmatter(index_path) if os.path.exists(index_path) else {}
    topic_title = topic_meta.get("title", topic_name)

    # Collect source files
    source_files = sorted(glob.glob(os.path.join(sources_dir, "source-*.md")))
    if not source_files:
        print(f"  No sources found for {topic_name}, skipping.")
        return

    # Get analyzed sources from claim alignment
    analyzed_sources = get_analyzed_sources(topic_dir)

    # Parse each source
    sources = []
    type_counts = defaultdict(int)
    institution_map = defaultdict(list)

    for filepath in source_files:
        fm = parse_frontmatter(filepath)
        basename = os.path.basename(filepath).replace(".md", "")
        source_num = basename.replace("source-", "")
        source_id = basename

        source_type = fm.get("type", "article")
        author = fm.get("author", "Unknown")
        title = fm.get("title", source_id)
        date = fm.get("date", "")
        url = fm.get("url", "")

        status = get_source_status(source_id, raw_dir, analyzed_sources)
        updated = get_updated_date(source_id, sources_dir, raw_dir)

        type_counts[source_type] += 1

        # Determine institution for grouping
        institution = detect_institution(author, url)
        if institution:
            institution_map[institution].append(source_num)

        sources.append({
            "num": source_num,
            "title": title,
            "author": shorten_author(author),
            "type": source_type,
            "date": date,
            "url": url,
            "status": status,
            "updated": updated,
        })

    total = len(sources)
    today = datetime.now().strftime("%Y-%m-%d")

    # Build type counts for frontmatter
    by_type_str = "{ " + ", ".join(
        f"{k}: {v}" for k, v in sorted(type_counts.items())
    ) + " }"

    # Build type descriptions
    type_labels = {
        "article": "Practitioner and analyst articles",
        "paper": "Academic and research papers",
        "report": "Industry reports and surveys",
        "blog": "Practitioner blog posts",
    }

    # Count sources not in any institution
    sources_in_institutions = set()
    for nums in institution_map.values():
        sources_in_institutions.update(nums)
    independent_count = total - len(sources_in_institutions)

    # Generate markdown
    lines = []

    # Frontmatter
    lines.append("---")
    lines.append(f"topic: {topic_name.lower().replace(' ', '-')}")
    lines.append(f"total_sources: {total}")
    lines.append(f"by_type: {by_type_str}")
    lines.append(f"updated: {today}")
    lines.append("---")
    lines.append("")

    # Heading
    lines.append(f"# Sources Overview: {topic_title}")
    lines.append("")
    type_list = ", ".join(
        f"{v} {k}{'s' if v != 1 else ''}" for k, v in sorted(type_counts.items(), key=lambda x: -x[1])
    )
    lines.append(f"{total} sources: {type_list}.")
    lines.append("")

    # Source table
    lines.append("## Source Table")
    lines.append("")
    lines.append("| # | Title | Author | Type | Status | Updated |")
    lines.append("|---|-------|--------|------|--------|---------|")
    for s in sources:
        title = s["title"]
        # Truncate long titles for the table
        if len(title) > 60:
            title = title[:57] + "..."
        lines.append(
            f"| {s['num']} | {title} | {s['author']} | {s['type']} | {s['status']} | {s['updated']} |"
        )
    lines.append("")

    # Status key
    lines.append("## Status Key")
    lines.append("")
    lines.append("- **gathered** — Source note created (source-NNN.md exists)")
    lines.append("- **segmented** — Raw segments extracted (raw/source-NNN-raw.yaml exists)")
    lines.append("- **analyzed** — Included in claim alignment and critical analysis")
    lines.append("- **queued** — In source-input.yaml, not yet processed")
    lines.append("")

    # By Type
    lines.append("## By Type")
    lines.append("")
    for src_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        label = type_labels.get(src_type, src_type.capitalize())
        ids = ", ".join(s["num"] for s in sources if s["type"] == src_type)
        lines.append(f"- **{src_type.capitalize()}** ({count}): {label} — {ids}")
    lines.append("")

    # By Institution
    lines.append("## By Institution")
    lines.append("")
    lines.append("| Institution | Count | Source IDs |")
    lines.append("|-------------|-------|-----------|")
    for inst, nums in sorted(institution_map.items(), key=lambda x: -len(x[1])):
        ids = ", ".join(sorted(nums))
        lines.append(f"| {inst} | {len(nums)} | {ids} |")
    if independent_count > 0:
        lines.append(f"| Independent | {independent_count} | — |")
    lines.append("")

    # Adding sources section
    lines.append("## Adding Sources")
    lines.append("")
    lines.append("To add new sources to this topic:")
    lines.append("- **Web sources**: Add URLs to `source-input.yaml` in the topic directory, then run `/research <topic>`")
    lines.append("- **Documents**: Drop PDFs/files into `documents/`, add an entry to `source-input.yaml`, then run `/ingest <topic>`")
    lines.append("")

    # Write output
    output_path = os.path.join(sources_dir, "_overview.md")
    with open(output_path, "w") as f:
        f.write("\n".join(lines))

    # Print summary
    status_counts = defaultdict(int)
    for s in sources:
        status_counts[s["status"]] += 1
    status_summary = ", ".join(
        f"{v} {k}" for k, v in sorted(status_counts.items(), key=lambda x: -x[1])
    )
    print(f"  {output_path}")
    print(f"  {total} sources ({status_summary})")


def main():
    topic_dirs = sorted([
        d for d in glob.glob(os.path.join(TOPICS_DIR, "*"))
        if os.path.isdir(d) and os.path.exists(os.path.join(d, "_index.md"))
    ])

    if not topic_dirs:
        print("No topic directories found.", file=sys.stderr)
        sys.exit(1)

    print("Building source overviews...")
    for topic_dir in topic_dirs:
        print(f"  Topic: {os.path.basename(topic_dir)}")
        build_overview(topic_dir)

    print("Done.")


if __name__ == "__main__":
    main()
