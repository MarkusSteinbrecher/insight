#!/usr/bin/env python3
"""Scrape web sources and generate structured source notes.

Reads pending URLs from a topic's source-input.yaml, uses Playwright
(for JS-rendered pages) to fetch full page text, extracts metadata from
HTML tags, and generates sources/source-NNN.md files with full text.

No LLM or API key required. Structured analysis (summary, takeaways,
segmentation) is handled downstream by /analyze.

Usage:
    python3 scripts/scrape-sources.py "EA for AI"
    python3 scripts/scrape-sources.py "EA for AI" --dry-run

Requires:
    - pip install playwright beautifulsoup4
    - playwright install chromium
"""

import argparse
import glob
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from urllib.parse import urlparse

import yaml
from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOPICS_DIR = os.path.join(ROOT, "knowledge-base", "topics")

# Tags to strip from the page before extracting text
STRIP_TAGS = [
    "nav", "header", "footer", "aside", "script", "style", "noscript",
    "iframe", "svg", "form", "button",
]

# Known domain-to-author mappings
DOMAIN_AUTHORS = {
    "bcg.com": "BCG",
    "bcgplatinion.com": "BCG Platinion",
    "bain.com": "Bain",
    "mckinsey.com": "McKinsey",
    "deloitte.com": "Deloitte",
    "ey.com": "EY",
    "pwc.com": "PwC",
    "pwc.ch": "PwC Switzerland",
    "kpmg.com": "KPMG",
    "accenture.com": "Accenture",
    "gartner.com": "Gartner",
    "forrester.com": "Forrester",
    "capgemini.com": "Capgemini",
    "hbr.org": "Harvard Business Review",
    "mit.edu": "MIT",
}


def find_topic_dir(slug):
    """Find the topic directory matching the given slug."""
    for name in os.listdir(TOPICS_DIR):
        path = os.path.join(TOPICS_DIR, name)
        if os.path.isdir(path) and name == slug:
            return path
    # Try case-insensitive match
    slug_lower = slug.lower().replace(" ", "-")
    for name in os.listdir(TOPICS_DIR):
        path = os.path.join(TOPICS_DIR, name)
        if os.path.isdir(path) and name.lower().replace(" ", "-") == slug_lower:
            return path
    return None


def load_source_input(topic_dir):
    """Load source-input.yaml and return the parsed data."""
    path = os.path.join(topic_dir, "source-input.yaml")
    if not os.path.exists(path):
        print(f"Error: {path} not found")
        sys.exit(1)
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    return data, path


def get_next_source_number(topic_dir):
    """Determine the next source number from existing source files."""
    sources_dir = os.path.join(topic_dir, "sources")
    if not os.path.isdir(sources_dir):
        os.makedirs(sources_dir, exist_ok=True)
        return 1
    existing = glob.glob(os.path.join(sources_dir, "source-*.md"))
    numbers = []
    for f in existing:
        basename = os.path.basename(f)
        match = re.match(r"source-(\d+)\.md", basename)
        if match:
            numbers.append(int(match.group(1)))
    return max(numbers) + 1 if numbers else 1


def get_pending_entries(data):
    """Return entries from source-input.yaml that need processing."""
    if not data or "sources" not in data:
        return []
    return [
        (i, entry) for i, entry in enumerate(data["sources"])
        if not entry.get("status") or entry.get("status") == "queued"
    ]


def guess_author(url):
    """Guess the author/organization from the URL domain."""
    domain = urlparse(url).netloc.lower()
    # Strip www. prefix
    domain = re.sub(r"^www\.", "", domain)
    for pattern, author in DOMAIN_AUTHORS.items():
        if domain.endswith(pattern):
            return author
    return domain


def extract_metadata(soup, url):
    """Extract metadata (title, author, date) from HTML meta tags."""
    meta = {}

    # Title: og:title > title tag
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        meta["title"] = og_title["content"].strip()
    elif soup.title and soup.title.string:
        meta["title"] = soup.title.string.strip()
    else:
        meta["title"] = "Untitled"

    # Clean up title — remove trailing site names like " | Gartner"
    meta["title"] = re.sub(r"\s*[|–—-]\s*[^|–—-]+$", "", meta["title"]).strip()

    # Author: meta author > og:site_name > domain guess
    author_tag = soup.find("meta", attrs={"name": "author"})
    if author_tag and author_tag.get("content"):
        meta["author"] = author_tag["content"].strip()
    else:
        og_site = soup.find("meta", property="og:site_name")
        if og_site and og_site.get("content"):
            meta["author"] = og_site["content"].strip()
        else:
            meta["author"] = guess_author(url)

    # Date: article:published_time > meta date > JSON-LD datePublished
    date_str = ""
    pub_time = soup.find("meta", property="article:published_time")
    if pub_time and pub_time.get("content"):
        date_str = pub_time["content"]
    else:
        date_tag = soup.find("meta", attrs={"name": "date"})
        if date_tag and date_tag.get("content"):
            date_str = date_tag["content"]
        else:
            # Try JSON-LD
            for script in soup.find_all("script", type="application/ld+json"):
                try:
                    ld = json.loads(script.string or "")
                    if isinstance(ld, dict):
                        date_str = ld.get("datePublished", "")
                    elif isinstance(ld, list):
                        for item in ld:
                            if isinstance(item, dict) and "datePublished" in item:
                                date_str = item["datePublished"]
                                break
                except (json.JSONDecodeError, TypeError):
                    continue

    if date_str:
        # Normalize to YYYY-MM-DD or YYYY
        date_match = re.match(r"(\d{4}[-/]\d{2}[-/]\d{2})", date_str)
        if date_match:
            meta["date"] = date_match.group(1).replace("/", "-")
        else:
            year_match = re.match(r"(\d{4})", date_str)
            meta["date"] = year_match.group(1) if year_match else ""

    if not meta.get("date"):
        meta["date"] = datetime.now().strftime("%Y-%m-%d")

    # Description (used as fallback summary)
    desc = soup.find("meta", property="og:description")
    if not desc:
        desc = soup.find("meta", attrs={"name": "description"})
    meta["description"] = desc["content"].strip() if desc and desc.get("content") else ""

    return meta


def extract_full_text(soup):
    """Extract the main article text from the page, stripping boilerplate."""
    # Remove unwanted tags
    for tag_name in STRIP_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    # Find the best content container — pick the largest one
    target = None
    best_len = 0

    candidates = []
    # Check multiple container types
    candidates.extend(soup.find_all("article"))
    candidates.extend(soup.find_all("main"))
    candidates.extend(soup.find_all("div", role="main"))
    candidates.extend(soup.find_all("div", class_=re.compile(r"(article|content|post|entry)", re.I)))

    for candidate in candidates:
        text_len = len(candidate.get_text(strip=True))
        if text_len > best_len:
            best_len = text_len
            target = candidate

    # Fall back to body if nothing substantial found
    if not target or best_len < 500:
        target = soup.body if soup.body else soup

    # Extract text, preserving paragraph breaks.
    # Track seen text to avoid duplicates from nested elements (e.g. <li><p>same text</p></li>).
    lines = []
    seen = set()
    for element in target.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "blockquote", "td", "th", "figcaption"]):
        text = element.get_text(separator=" ", strip=True)
        if not text or text in seen:
            continue
        seen.add(text)

        # Add markdown heading markers
        if element.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level = int(element.name[1])
            text = "#" * level + " " + text
        elif element.name == "li":
            text = "- " + text
        elif element.name == "blockquote":
            text = "> " + text

        lines.append(text)

    full_text = "\n\n".join(lines)

    # Clean up: strip leading navigation noise and trailing boilerplate
    full_text = _clean_extracted_text(full_text)

    return full_text


# Patterns that indicate trailing boilerplate sections
_BOILERPLATE_HEADINGS = re.compile(
    r"^#{1,6}\s+(Contact\s+us|Related\s+content|Cookie|Footer|Newsletter|Subscribe|Follow\s+us|Legal|Privacy|Disclaimer)",
    re.IGNORECASE | re.MULTILINE,
)

# Short lines that are likely navigation noise
_NAV_NOISE = re.compile(
    r"^(Menu|Featured|Loading.*|No Match Found|Skip to .*)$",
    re.IGNORECASE,
)


def _clean_extracted_text(text):
    """Remove navigation noise from the top and boilerplate from the bottom."""
    # Truncate at the first boilerplate heading
    match = _BOILERPLATE_HEADINGS.search(text)
    if match:
        text = text[:match.start()].rstrip()

    # Remove leading navigation noise lines
    lines = text.split("\n\n")
    # Find the first substantial content line (>40 chars or a heading)
    start = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if _NAV_NOISE.match(stripped):
            continue
        if len(stripped) < 20 and not stripped.startswith("#"):
            continue
        start = i
        break

    return "\n\n".join(lines[start:])


def fetch_page(url):
    """Fetch a page using Playwright and return the HTML."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            page.goto(url, wait_until="networkidle", timeout=30000)
            # Wait a bit for any lazy-loaded content
            page.wait_for_timeout(2000)
            html = page.content()
        finally:
            browser.close()

    return html


def scrape_url(url):
    """Fetch page with Playwright and extract metadata + full text."""
    print("  Fetching page...")
    html = fetch_page(url)
    print(f"  Fetched {len(html):,} bytes of HTML")

    soup = BeautifulSoup(html, "html.parser")

    print("  Extracting metadata...")
    metadata = extract_metadata(soup, url)

    print("  Extracting full text...")
    full_text = extract_full_text(soup)
    print(f"  Extracted {len(full_text):,} chars of text")

    return metadata, full_text


def format_source_note(metadata, url, full_text):
    """Format extracted data as a source note markdown file."""
    lines = ["---"]
    lines.append(f'title: "{metadata["title"]}"')
    lines.append(f'url: "{url}"')
    lines.append(f'author: "{metadata["author"]}"')
    lines.append(f'date: "{metadata["date"]}"')
    lines.append("type: article")
    lines.append("relevance: 3")
    lines.append("tags: []")
    lines.append("---")
    lines.append("")

    # Description as provisional summary
    if metadata.get("description"):
        lines.append("## Summary")
        lines.append("")
        lines.append(metadata["description"])
        lines.append("")

    # Full Text
    if full_text and full_text.strip():
        lines.append("## Full Text")
        lines.append("")
        lines.append(full_text.strip())
        lines.append("")

    return "\n".join(lines)


def write_source_note(topic_dir, source_num, content):
    """Write a source note to the sources directory."""
    sources_dir = os.path.join(topic_dir, "sources")
    os.makedirs(sources_dir, exist_ok=True)
    filename = f"source-{source_num:03d}.md"
    filepath = os.path.join(sources_dir, filename)
    with open(filepath, "w") as f:
        f.write(content)
    return filepath, filename


def update_source_input_entry(path, entry_index, source_id):
    """Update source-input.yaml by modifying the entry at entry_index.

    Re-reads and re-writes the YAML. Preserves header comments but not
    inline comments (those are lost by yaml.dump).
    """
    # Read header comments
    with open(path, "r") as f:
        original_lines = f.readlines()
    header = []
    for line in original_lines:
        if line.startswith("#"):
            header.append(line)
        else:
            break

    # Parse, modify, write
    with open(path, "r") as f:
        data = yaml.safe_load(f)

    data["sources"][entry_index]["source"] = source_id
    data["sources"][entry_index]["status"] = "gathered"

    with open(path, "w") as f:
        for line in header:
            f.write(line)
        f.write("\n")
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def run_build_overview(topic_dir):
    """Run build-overview.py to regenerate _overview.md."""
    script = os.path.join(ROOT, "scripts", "build-overview.py")
    if os.path.exists(script):
        print("\nRegenerating _overview.md...")
        subprocess.run([sys.executable, script], cwd=ROOT)


def main():
    parser = argparse.ArgumentParser(
        description="Scrape web sources and generate structured source notes"
    )
    parser.add_argument("topic", help="Topic slug or name (e.g., 'EA for AI')")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be processed without actually scraping",
    )
    args = parser.parse_args()

    # Find topic directory
    topic_dir = find_topic_dir(args.topic)
    if not topic_dir:
        print(f"Error: Topic '{args.topic}' not found in {TOPICS_DIR}")
        sys.exit(1)

    topic_name = os.path.basename(topic_dir)
    print(f"Topic: {topic_name}")
    print(f"Directory: {topic_dir}")

    # Load source-input.yaml
    data, input_path = load_source_input(topic_dir)

    # Find pending entries
    pending = get_pending_entries(data)
    if not pending:
        print("\nNo pending entries found in source-input.yaml.")
        print("(Entries need status missing or 'queued' to be processed)")
        sys.exit(0)

    print(f"\nFound {len(pending)} pending source(s) to process:")
    for _, entry in pending:
        print(f"  - {entry.get('url', 'no URL')}")
        if entry.get("note"):
            print(f"    {entry['note']}")

    if args.dry_run:
        print("\n[Dry run] No sources were scraped.")
        sys.exit(0)

    # Determine starting source number
    next_num = get_next_source_number(topic_dir)
    print(f"\nStarting from source-{next_num:03d}")

    # Process each pending URL
    succeeded = 0
    failed = 0
    source_num = next_num

    for idx, entry in pending:
        url = entry.get("url")
        if not url:
            print(f"\n[Skip] Entry at index {idx} has no URL")
            failed += 1
            continue

        source_id = f"source-{source_num:03d}"
        print(f"\n{'='*60}")
        print(f"[{source_id}] Scraping: {url}")
        print(f"{'='*60}")

        try:
            metadata, full_text = scrape_url(url)

            if not full_text or len(full_text.strip()) < 100:
                raise ValueError(f"Extracted text too short ({len(full_text)} chars) — page may not have rendered")

            # Format and write source note
            content = format_source_note(metadata, url, full_text)
            filepath, filename = write_source_note(topic_dir, source_num, content)
            print(f"  -> Written: {filepath}")
            print(f"     Title: {metadata['title']}")
            print(f"     Author: {metadata['author']}")
            print(f"     Date: {metadata['date']}")
            print(f"     Text: {len(full_text):,} chars")

            # Update source-input.yaml entry
            update_source_input_entry(input_path, idx, source_id)

            succeeded += 1
            source_num += 1

        except Exception as e:
            print(f"  [Error] Failed to scrape {url}: {e}")
            failed += 1
            continue

    # source-input.yaml is updated per-entry during processing
    if succeeded > 0:
        print(f"\nUpdated {input_path}")

    # Summary
    print(f"\n{'='*60}")
    print(f"Done. {succeeded} succeeded, {failed} failed.")
    print(f"{'='*60}")

    # Regenerate overview
    if succeeded > 0:
        run_build_overview(topic_dir)


if __name__ == "__main__":
    main()
