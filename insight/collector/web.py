"""
Web page extractor for the Collector.

Fetches web pages via Playwright, extracts metadata and structured
content blocks with heading path tracking. Writes Source + ContentBlock
nodes to the knowledge graph.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from urllib.parse import urlparse

from bs4 import BeautifulSoup


# Tags to strip before extracting content
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

# Patterns indicating trailing boilerplate
_BOILERPLATE_HEADINGS = re.compile(
    r"^(Contact\s+us|Related\s+content|Cookie|Footer|Newsletter|Subscribe|"
    r"Follow\s+us|Legal|Privacy|Disclaimer|Share\s+this|About\s+the\s+author)",
    re.IGNORECASE,
)

# Short lines that are likely navigation noise
_NAV_NOISE = re.compile(
    r"^(Menu|Featured|Loading.*|No Match Found|Skip to .*)$",
    re.IGNORECASE,
)


def fetch_page(url: str) -> str:
    """Fetch a page using Playwright, return raw HTML."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )
        page = context.new_page()
        try:
            # Try networkidle first, fall back to domcontentloaded on timeout
            try:
                page.goto(url, wait_until="networkidle", timeout=30000)
            except Exception:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(2000)
            html = page.content()
        finally:
            browser.close()
    return html


def _guess_author(url: str) -> str:
    """Guess author/organization from URL domain."""
    domain = urlparse(url).netloc.lower()
    domain = re.sub(r"^www\.", "", domain)
    for pattern, author in DOMAIN_AUTHORS.items():
        if domain.endswith(pattern):
            return author
    return domain


def extract_metadata(soup: BeautifulSoup, url: str) -> dict:
    """Extract metadata (title, author, date, description) from HTML."""
    meta = {}

    # Title
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        meta["title"] = og_title["content"].strip()
    elif soup.title and soup.title.string:
        meta["title"] = soup.title.string.strip()
    else:
        meta["title"] = "Untitled"
    meta["title"] = re.sub(r"\s*[|–—-]\s*[^|–—-]+$", "", meta["title"]).strip()

    # Author
    author_tag = soup.find("meta", attrs={"name": "author"})
    if author_tag and author_tag.get("content"):
        meta["author"] = author_tag["content"].strip()
    else:
        og_site = soup.find("meta", property="og:site_name")
        if og_site and og_site.get("content"):
            meta["author"] = og_site["content"].strip()
        else:
            meta["author"] = _guess_author(url)

    # Date
    date_str = ""
    pub_time = soup.find("meta", property="article:published_time")
    if pub_time and pub_time.get("content"):
        date_str = pub_time["content"]
    else:
        date_tag = soup.find("meta", attrs={"name": "date"})
        if date_tag and date_tag.get("content"):
            date_str = date_tag["content"]
        else:
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
        date_match = re.match(r"(\d{4}[-/]\d{2}[-/]\d{2})", date_str)
        if date_match:
            meta["date"] = date_match.group(1).replace("/", "-")
        else:
            year_match = re.match(r"(\d{4})", date_str)
            meta["date"] = year_match.group(1) if year_match else ""
    meta.setdefault("date", "")

    # Description
    desc = soup.find("meta", property="og:description")
    if not desc:
        desc = soup.find("meta", attrs={"name": "description"})
    meta["description"] = desc["content"].strip() if desc and desc.get("content") else ""

    return meta


def extract_content_blocks(soup: BeautifulSoup) -> list[dict]:
    """
    Extract structured content blocks from HTML with heading path tracking.

    Returns a list of dicts with keys:
        text, format, section_path, location_value
    """
    # Remove unwanted tags
    for tag_name in STRIP_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    # Find best content container
    target = None
    best_len = 0
    candidates = []
    candidates.extend(soup.find_all("article"))
    candidates.extend(soup.find_all("main"))
    candidates.extend(soup.find_all("div", role="main"))
    candidates.extend(soup.find_all("div", class_=re.compile(
        r"(article|content|post|entry)", re.I
    )))

    for candidate in candidates:
        text_len = len(candidate.get_text(strip=True))
        if text_len > best_len:
            best_len = text_len
            target = candidate

    if not target or best_len < 500:
        target = soup.body if soup.body else soup

    # Walk elements, tracking heading hierarchy
    heading_stack = []  # [(level, text), ...]
    blocks = []
    seen = set()

    content_elements = target.find_all([
        "h1", "h2", "h3", "h4", "h5", "h6",
        "p", "li", "blockquote", "td", "th", "figcaption",
        "tr",
    ])

    for element in content_elements:
        text = element.get_text(separator=" ", strip=True)
        if not text or text in seen:
            continue
        seen.add(text)

        tag = element.name

        # Update heading stack
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level = int(tag[1])

            # Check for boilerplate heading — stop extraction
            if _BOILERPLATE_HEADINGS.match(text):
                break

            # Pop headings at same or deeper level
            while heading_stack and heading_stack[-1][0] >= level:
                heading_stack.pop()
            heading_stack.append((level, text))

            blocks.append({
                "text": text,
                "format": "heading",
                "section_path": _build_section_path(heading_stack),
                "location_value": _build_section_path(heading_stack),
            })
            continue

        # Skip navigation noise
        if len(text) < 20 and _NAV_NOISE.match(text):
            continue

        # Determine format
        if tag == "li":
            fmt = "bullet"
        elif tag == "blockquote":
            fmt = "quote"
        elif tag in ("td", "th"):
            fmt = "table_cell"
        elif tag == "tr":
            fmt = "table_row"
        elif tag == "figcaption":
            fmt = "caption"
        else:
            fmt = "prose"

        section_path = _build_section_path(heading_stack)

        blocks.append({
            "text": text,
            "format": fmt,
            "section_path": section_path,
            "location_value": section_path,
        })

    return blocks


def _build_section_path(heading_stack: list) -> str:
    """Build a section path string from the heading stack."""
    if not heading_stack:
        return ""
    return " > ".join(text for _, text in heading_stack)


def extract_web_source(url: str, topic: str, source_id: str, graph) -> dict:
    """
    Full extraction pipeline for a web URL.

    Fetches the page, extracts metadata and content blocks,
    writes Source + ContentBlock nodes to the graph.

    Returns a summary dict with source_id, title, block_count.
    """
    # Fetch
    html = fetch_page(url)
    soup = BeautifulSoup(html, "html.parser")

    # Extract metadata
    metadata = extract_metadata(soup, url)

    # Extract content blocks
    blocks = extract_content_blocks(soup)

    if not blocks:
        raise ValueError(f"No content blocks extracted from {url}")

    # Compute content hash from all block texts
    all_text = "\n".join(b["text"] for b in blocks)
    content_hash = hashlib.sha256(all_text.encode("utf-8")).hexdigest()

    # Write Source node
    graph.add_source(
        source_id=source_id,
        topic=topic,
        source_type="web",
        title=metadata["title"],
        url=url,
        author=metadata.get("author", ""),
        publication_date=metadata.get("date", ""),
        content_hash=content_hash,
        metadata={
            "description": metadata.get("description", ""),
            "html_length": len(html),
        },
    )

    # Write ContentBlock nodes
    for i, block in enumerate(blocks):
        block_id = f"{source_id}:block-{i+1:03d}"
        graph.add_content_block(
            block_id=block_id,
            source_id=source_id,
            text=block["text"],
            position=i + 1,
            location_type="heading_path",
            location_value=block["location_value"],
            format=block["format"],
            section_path=block.get("section_path", ""),
        )

    return {
        "source_id": source_id,
        "title": metadata["title"],
        "author": metadata.get("author", ""),
        "date": metadata.get("date", ""),
        "block_count": len(blocks),
        "content_length": len(all_text),
    }
