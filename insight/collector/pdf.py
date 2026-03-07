"""
PDF document extractor for the Collector.

Extracts text from PDF files using PyMuPDF, detects headings via
font analysis, splits into structured content blocks with section
path tracking. Writes Source + ContentBlock nodes to the knowledge graph.
"""

from __future__ import annotations

import hashlib
import os
import re
from collections import Counter
from pathlib import Path

from insight.collector.blocks import clean_blocks as _clean_blocks


def _analyze_fonts(doc) -> dict:
    """
    Analyze font usage across the document to identify body vs heading fonts.

    Returns dict with:
        body_size: most common font size (= body text)
        heading_styles: set of (size, is_bold) that are likely headings
    """
    size_counts: Counter = Counter()
    style_samples: dict[tuple, list[str]] = {}

    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:
            if b["type"] != 0:  # skip images
                continue
            for line in b["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip()
                    if not text or len(text) < 3:
                        continue
                    size = round(span["size"], 1)
                    is_bold = bool(span["flags"] & (1 << 4))  # bit 4 = bold
                    size_counts[size] += len(text)
                    key = (size, is_bold)
                    if key not in style_samples:
                        style_samples[key] = []
                    if len(style_samples[key]) < 5:
                        style_samples[key].append(text[:80])

    if not size_counts:
        return {"body_size": 10.0, "heading_styles": set()}

    # Body text is the font size with the most total characters
    body_size = size_counts.most_common(1)[0][0]

    # Headings are bold text at body size or larger, or any text larger than body
    heading_styles = set()
    for (size, is_bold), samples in style_samples.items():
        if size > body_size + 1:
            heading_styles.add((size, is_bold))
        elif size >= body_size and is_bold:
            heading_styles.add((size, is_bold))

    return {
        "body_size": body_size,
        "heading_styles": heading_styles,
    }


def _is_header_footer(text: str, body_size: float, span_size: float, page_height: float, y_pos: float) -> bool:
    """Check if text is likely a header or footer."""
    # Very small text relative to body
    if span_size < body_size - 2:
        return True
    # Page numbers
    if re.match(r"^\d{1,4}$", text.strip()):
        return True
    # Common header/footer patterns
    if re.match(r"^(Copyright|©|ISSN|Page\s+\d|^\d+\s*$)", text.strip(), re.IGNORECASE):
        return True
    # Text in top/bottom 5% of page
    if y_pos < page_height * 0.05 or y_pos > page_height * 0.95:
        if len(text.strip()) < 100:
            return True
    return False


def _classify_heading_level(size: float, is_bold: bool, body_size: float) -> int:
    """Classify a heading into levels 1-4 based on font size relative to body."""
    diff = size - body_size
    if diff > 3:
        return 1
    if diff > 1:
        return 2
    if diff > 0 or (is_bold and diff >= 0):
        return 3
    return 4


def _extract_with_dict(doc, body_size: float, heading_styles: set) -> list[dict]:
    """Extract blocks using dict mode (font-aware). Returns empty list if no text found."""
    heading_stack: list[tuple[int, str]] = []
    blocks: list[dict] = []
    seen_texts: set[str] = set()
    stop_extraction = False

    for page_num, page in enumerate(doc):
        if stop_extraction:
            break
        page_height = page.rect.height
        page_blocks = page.get_text("dict")["blocks"]

        for block in page_blocks:
            if stop_extraction:
                break
            if block["type"] != 0:
                continue

            lines_data = []
            for line in block["lines"]:
                line_text_parts = []
                line_sizes = []
                line_bold_chars = 0
                line_total_chars = 0
                line_y = line["bbox"][1]

                for span in line["spans"]:
                    text = span["text"]
                    if not text:
                        continue
                    line_text_parts.append(text)
                    line_sizes.append(span["size"])
                    line_total_chars += len(text.strip())
                    if span["flags"] & (1 << 4):
                        line_bold_chars += len(text.strip())

                line_text = "".join(line_text_parts).strip()
                if not line_text:
                    continue

                avg_size = sum(line_sizes) / len(line_sizes) if line_sizes else body_size
                is_bold = line_bold_chars > line_total_chars * 0.5

                if _is_header_footer(line_text, body_size, avg_size, page_height, line_y):
                    continue

                lines_data.append({
                    "text": line_text,
                    "size": round(avg_size, 1),
                    "bold": is_bold,
                    "y": line_y,
                })

            if not lines_data:
                continue

            current_group: list[str] = []
            current_style: tuple | None = None

            def flush_group():
                nonlocal stop_extraction
                if not current_group:
                    return
                text = " ".join(current_group)
                text = re.sub(r"\s+", " ", text).strip()
                if not text or text in seen_texts:
                    return
                if len(text) < 10 and current_style and (current_style[0], current_style[1]) not in heading_styles:
                    return
                seen_texts.add(text)

                if _REFERENCE_ENTRY.match(text):
                    stop_extraction = True
                    return

                size, is_bold = current_style or (body_size, False)
                is_heading = (round(size, 1), is_bold) in heading_styles and len(text) < 200

                if is_heading:
                    if _STOP_HEADINGS.match(text):
                        stop_extraction = True
                        return

                    level = _classify_heading_level(size, is_bold, body_size)
                    while heading_stack and heading_stack[-1][0] >= level:
                        heading_stack.pop()
                    heading_stack.append((level, text))

                    blocks.append({
                        "text": text,
                        "format": "heading",
                        "section_path": _build_section_path(heading_stack),
                    })
                else:
                    fmt = "prose"
                    if re.match(r"^[•●◦▪‣\-–]\s", text):
                        fmt = "bullet"
                        text = re.sub(r"^[•●◦▪‣\-–]\s+", "", text)
                    elif re.match(r"^\d+[\.\)]\s", text):
                        fmt = "bullet"
                    elif re.match(r"^[a-z][\.\)]\s", text):
                        fmt = "bullet"

                    blocks.append({
                        "text": text,
                        "format": fmt,
                        "section_path": _build_section_path(heading_stack),
                    })

            for ld in lines_data:
                style = (ld["size"], ld["bold"])
                if current_style is None:
                    current_style = style
                elif style != current_style:
                    flush_group()
                    current_group = []
                    current_style = style
                current_group.append(ld["text"])

            flush_group()

    return blocks


def _extract_with_text(doc) -> list[dict]:
    """
    Fallback extraction using plain text mode.
    Used when dict mode yields no text (e.g., PDFs with XObject text).
    """
    blocks: list[dict] = []
    seen_texts: set[str] = set()
    heading_stack: list[tuple[int, str]] = []

    for page in doc:
        text = page.get_text("text")
        if not text.strip():
            continue

        # Normalize Unicode line/paragraph separators to newlines
        text = text.replace("\u2028", "\n").replace("\u2029", "\n\n")

        paragraphs = re.split(r"\n{2,}", text)
        for para in paragraphs:
            para = para.strip()
            if not para or para in seen_texts:
                continue

            # Rejoin soft line breaks within a paragraph
            para = re.sub(r"(?<=[a-z,;])\n(?=[a-z])", " ", para)
            para = re.sub(r"\n", " ", para)
            para = re.sub(r"\s+", " ", para).strip()

            if not para or len(para) < 5:
                continue
            if para in seen_texts:
                continue
            seen_texts.add(para)

            # Stop at references
            if _REFERENCE_ENTRY.match(para):
                break
            if _STOP_HEADINGS.match(para):
                break

            # Detect headings: short lines that look like titles
            is_heading = (
                len(para) < 100
                and not para.endswith(".")
                and not para.endswith(",")
                and re.match(r"^(\d+[\.\s]|[A-Z])", para)
            )

            if is_heading:
                level = 2 if re.match(r"^\d+\.\d+", para) else 1
                while heading_stack and heading_stack[-1][0] >= level:
                    heading_stack.pop()
                heading_stack.append((level, para))
                blocks.append({
                    "text": para,
                    "format": "heading",
                    "section_path": _build_section_path(heading_stack),
                })
            else:
                fmt = "prose"
                if re.match(r"^[•●◦▪‣\-–]\s", para):
                    fmt = "bullet"
                    para = re.sub(r"^[•●◦▪‣\-–]\s+", "", para)

                blocks.append({
                    "text": para,
                    "format": fmt,
                    "section_path": _build_section_path(heading_stack),
                })

    return blocks


def _merge_nearby_rects(rects: list[tuple], gap: int = 10) -> list[tuple]:
    """Merge rectangles that overlap or are within gap pixels of each other.

    Uses union-find to cluster nearby rectangles, then returns
    the bounding box of each cluster.

    Args:
        rects: list of (x0, y0, x1, y1) tuples
        gap: maximum pixel distance to consider rects as belonging together

    Returns: list of merged (x0, y0, x1, y1) bounding boxes
    """
    if not rects:
        return []

    n = len(rects)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j):
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[ri] = rj

    for i in range(n):
        ax0, ay0, ax1, ay1 = rects[i]
        for j in range(i + 1, n):
            bx0, by0, bx1, by1 = rects[j]
            if (ax0 - gap <= bx1 and ax1 + gap >= bx0
                    and ay0 - gap <= by1 and ay1 + gap >= by0):
                union(i, j)

    groups: dict[int, list[tuple]] = {}
    for i in range(n):
        g = find(i)
        if g not in groups:
            groups[g] = []
        groups[g].append(rects[i])

    return [
        (min(r[0] for r in g), min(r[1] for r in g),
         max(r[2] for r in g), max(r[3] for r in g))
        for g in groups.values()
    ]


def _text_coverage_in_region(page, region: tuple) -> float:
    """Compute what fraction of a region is covered by text blocks.

    Used to distinguish figures (low text coverage) from styled text
    containers like colored cards or section boxes (high text coverage).

    Returns a value between 0.0 (no text) and 1.0+ (all text).
    """
    rx0, ry0, rx1, ry1 = region
    region_area = (rx1 - rx0) * (ry1 - ry0)
    if region_area <= 0:
        return 0.0

    text_area = 0.0
    text_dict = page.get_text("dict")
    for block in text_dict.get("blocks", []):
        if block["type"] != 0:  # skip image blocks
            continue
        bx0, by0, bx1, by1 = block["bbox"]
        # Intersection of text block with region
        ix0 = max(rx0, bx0)
        iy0 = max(ry0, by0)
        ix1 = min(rx1, bx1)
        iy1 = min(ry1, by1)
        if ix0 < ix1 and iy0 < iy1:
            text_area += (ix1 - ix0) * (iy1 - iy0)

    return text_area / region_area


def _find_figure_regions(
    page, raster_rects: list[tuple] | None = None,
    min_area: int = 5000, padding: int = 30,
    max_text_coverage: float = 0.3, min_drawings: int = 5,
) -> list[tuple]:
    """Find vector figure regions on a page by clustering drawing operations.

    Clusters nearby vector drawings into figure groups, filters out:
    - Degenerate/tiny drawings and page-filling backgrounds
    - Decorative elements (thin bars, card backgrounds)
    - Regions already covered by raster images
    - Text-heavy regions (styled cards/boxes, not actual figures)
    - Regions with too few drawing operations (single fills vs real charts)

    Args:
        page: PyMuPDF Page object
        raster_rects: display positions of raster images already extracted,
            as (x0, y0, x1, y1) tuples — used to avoid duplicate extraction
        min_area: minimum area in square points to consider a region a figure
        padding: points to add around each detected region
        max_text_coverage: maximum fraction of region covered by text blocks;
            regions above this are treated as styled text containers
        min_drawings: minimum number of drawing operations in a region;
            real figures have many drawings (chart bars, lines, gridlines),
            card backgrounds have only 1-3

    Returns: list of (x0, y0, x1, y1) tuples for each detected figure
    """
    drawings = page.get_drawings()
    if not drawings:
        return []

    # Collect valid drawing bounding rects, filtering out backgrounds
    page_area = page.rect.width * page.rect.height
    rects = []
    for d in drawings:
        r = d.get("rect")
        if r is None:
            continue
        x0, y0, x1, y1 = r
        if x1 - x0 < 1 or y1 - y0 < 1:
            continue
        # Skip page-filling background rectangles
        rect_area = (x1 - x0) * (y1 - y0)
        if rect_area > page_area * 0.5:
            continue
        rects.append((x0, y0, x1, y1))

    if len(rects) < min_drawings:
        return []

    # Merge nearby drawings into figure groups
    merged = _merge_nearby_rects(rects, gap=10)

    page_w = page.rect.width
    page_h = page.rect.height
    figures = []

    for x0, y0, x1, y1 in merged:
        w, h = x1 - x0, y1 - y0
        area = w * h

        # Skip tiny regions (decorative dots, bullets, underlines)
        if area < min_area:
            continue

        # Skip full-width thin bars (page rules, decorations)
        if w > page_w * 0.85 and h < 15:
            continue

        # Skip full-height thin bars
        if h > page_h * 0.85 and w < 15:
            continue

        # Count how many original drawings fall within this region.
        # Real figures (charts, diagrams) have many drawing operations;
        # card backgrounds or decorative fills have only 1-3.
        n_drawings = sum(
            1 for r in rects
            if r[0] >= x0 - 1 and r[1] >= y0 - 1
            and r[2] <= x1 + 1 and r[3] <= y1 + 1
        )
        if n_drawings < min_drawings:
            continue

        # Skip if significantly overlapping with an already-extracted raster image
        if raster_rects:
            skip = False
            for rx0, ry0, rx1, ry1 in raster_rects:
                ix0 = max(x0, rx0)
                iy0 = max(y0, ry0)
                ix1 = min(x1, rx1)
                iy1 = min(y1, ry1)
                if ix0 < ix1 and iy0 < iy1:
                    inter_area = (ix1 - ix0) * (iy1 - iy0)
                    raster_area = (rx1 - rx0) * (ry1 - ry0)
                    if raster_area > 0 and inter_area > raster_area * 0.5:
                        skip = True
                        break
            if skip:
                continue

        # Skip text-heavy regions (styled cards/boxes, not actual figures)
        if _text_coverage_in_region(page, (x0, y0, x1, y1)) > max_text_coverage:
            continue

        # Expand region to include nearby short text (axis labels, titles,
        # annotations) that belong to the figure but sit outside the
        # drawing bounding box. Only include text blocks that are short
        # (< 60 chars) and close to the region boundary (within padding).
        ex0, ey0, ex1, ey1 = x0, y0, x1, y1
        text_dict = page.get_text("dict")
        for block in text_dict.get("blocks", []):
            if block["type"] != 0:
                continue
            bx0, by0, bx1, by1 = block["bbox"]
            # Concatenate text in block to check length
            block_text = ""
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    block_text += span.get("text", "")
            if len(block_text.strip()) > 60:
                continue  # skip prose paragraphs
            # Check if this text block is close to the drawing region
            if (bx0 < x1 + padding and bx1 > x0 - padding
                    and by0 < y1 + padding and by1 > y0 - padding):
                ex0 = min(ex0, bx0)
                ey0 = min(ey0, by0)
                ex1 = max(ex1, bx1)
                ey1 = max(ey1, by1)

        # Apply base padding and clip to page bounds
        fx0 = max(ex0 - padding, page.rect.x0)
        fy0 = max(ey0 - padding, page.rect.y0)
        fx1 = min(ex1 + padding, page.rect.x1)
        fy1 = min(ey1 + padding, page.rect.y1)

        figures.append((fx0, fy0, fx1, fy1))

    return figures


def _extract_images(doc, image_dir: str, text_blocks_per_page: dict, min_size: int = 100) -> list[dict]:
    """
    Extract meaningful images from a PDF document.

    Two strategies:
    1. Extract raster images (charts, diagrams embedded as images)
    2. Detect vector figure regions (charts, diagrams drawn with lines/shapes),
       crop to just the figure area, and render at high DPI

    Args:
        doc: PyMuPDF Document
        image_dir: Directory to save extracted images
        text_blocks_per_page: dict mapping page_num to text block count
        min_size: Minimum width/height to consider (pixels)
    """
    import pymupdf

    os.makedirs(image_dir, exist_ok=True)
    image_blocks = []
    seen_xrefs = set()

    # Track raster image display positions per page for overlap detection
    raster_positions: dict[int, list[tuple]] = {}

    # Strategy 1: Extract raster images
    for page_num, page in enumerate(doc):
        images = page.get_images(full=True)
        page_raster_rects: list[tuple] = []

        # Get on-page display positions of raster images
        try:
            image_info = page.get_image_info(xrefs=True)
        except Exception:
            image_info = []

        for img_idx, img in enumerate(images):
            xref = img[0]
            if xref in seen_xrefs:
                continue
            seen_xrefs.add(xref)

            try:
                pix = pymupdf.Pixmap(doc, xref)

                if pix.width < min_size or pix.height < min_size:
                    pix = None
                    continue

                if pix.n > 4:
                    pix = pymupdf.Pixmap(pymupdf.csRGB, pix)

                img_filename = f"p{page_num:03d}_img{img_idx:02d}.png"
                img_path = os.path.join(image_dir, img_filename)
                pix.save(img_path)

                # Track display position for Strategy 2 overlap detection
                for info in image_info:
                    if info.get("xref") == xref:
                        bbox = info["bbox"]
                        page_raster_rects.append(
                            (bbox[0], bbox[1], bbox[2], bbox[3])
                        )

                image_blocks.append({
                    "text": f"[Image: {pix.width}x{pix.height} from page {page_num + 1}]",
                    "format": "figure",
                    "section_path": f"page:{page_num + 1}",
                    "image_path": img_path,
                    "page": page_num,
                    "width": pix.width,
                    "height": pix.height,
                })

                pix = None
            except Exception:
                continue

        raster_positions[page_num] = page_raster_rects

    # Strategy 2: Detect and crop vector figure regions
    # Instead of rendering full pages, cluster drawing operations into
    # figure regions and render only those areas at high DPI.
    for page_num, page in enumerate(doc):
        raster_rects = raster_positions.get(page_num, [])
        figure_regions = _find_figure_regions(
            page, raster_rects=raster_rects, min_area=5000, padding=15,
        )

        for fig_idx, region in enumerate(figure_regions):
            try:
                clip = pymupdf.Rect(region)
                pix = page.get_pixmap(clip=clip, dpi=200)

                if pix.width < min_size or pix.height < min_size:
                    pix = None
                    continue

                img_filename = f"p{page_num:03d}_fig{fig_idx:02d}.png"
                img_path = os.path.join(image_dir, img_filename)
                pix.save(img_path)

                image_blocks.append({
                    "text": f"[Figure: {pix.width}x{pix.height} from page {page_num + 1}]",
                    "format": "figure",
                    "section_path": f"page:{page_num + 1}",
                    "image_path": img_path,
                    "page": page_num,
                    "width": pix.width,
                    "height": pix.height,
                })
                pix = None
            except Exception:
                continue

    # Sort by page number
    image_blocks.sort(key=lambda b: b["page"])
    return image_blocks


def extract_pdf_blocks(filepath: str, image_dir: str = "") -> tuple[list[dict], dict]:
    """
    Extract structured content blocks from a PDF file.

    Uses font-aware dict extraction first, falls back to plain text
    extraction if dict mode yields no text. Optionally extracts images.

    Returns (blocks, metadata).
    """
    import pymupdf

    doc = pymupdf.open(filepath)
    font_info = _analyze_fonts(doc)
    body_size = font_info["body_size"]
    heading_styles = font_info["heading_styles"]

    meta = doc.metadata or {}
    doc_metadata = {
        "title": meta.get("title", ""),
        "author": meta.get("author", ""),
        "pages": len(doc),
        "body_font_size": body_size,
    }

    # Try font-aware extraction first
    blocks = _extract_with_dict(doc, body_size, heading_styles)

    # Fall back to plain text if dict mode got nothing
    if not blocks:
        blocks = _extract_with_text(doc)

    # Count text blocks per page for image extraction heuristic
    text_blocks_per_page: dict[int, int] = {}
    for page_num, page in enumerate(doc):
        count = 0
        for b in page.get_text("dict")["blocks"]:
            if b["type"] == 0:
                count += 1
        text_blocks_per_page[page_num] = count

    # Extract images if image_dir provided
    image_blocks = []
    if image_dir:
        image_blocks = _extract_images(doc, image_dir, text_blocks_per_page)

    doc.close()

    # Strip leading boilerplate: skip until first numbered heading
    # or first substantial paragraph
    first_content = 0
    for i, b in enumerate(blocks):
        text = b["text"]
        if b["format"] == "heading" and re.match(r"^\d+[\.\s]", text):
            first_content = i
            break
        if b["format"] == "heading" and re.match(r"^(Abstract|Introduction|Summary|Overview|Foreword)", text, re.IGNORECASE):
            first_content = i
            break
        if b["format"] == "prose" and len(text) > 200:
            first_content = i
            break
        if i >= 20:
            break
    if first_content > 0:
        blocks = blocks[first_content:]

    # Post-process text blocks: fix cut-offs and split long blocks
    blocks = _clean_blocks(blocks, max_len=800)

    # Interleave image blocks at their page positions
    if image_blocks:
        # Insert image blocks after the last text block from the same page
        # For simplicity, append them at the end — they'll be positioned by page
        blocks.extend(image_blocks)

    return blocks, doc_metadata


def _build_section_path(heading_stack: list) -> str:
    """Build a section path string from the heading stack."""
    if not heading_stack:
        return ""
    return " > ".join(text for _, text in heading_stack)


# Headings that indicate we should stop extracting
_STOP_HEADINGS = re.compile(
    r"^(References|Bibliography|Works\s+Cited|Acknowledgements?|Appendix|"
    r"About\s+the\s+Author|Endnotes|Footnotes|Data\s+availability)",
    re.IGNORECASE,
)

# Reference entry pattern — indicates we've entered the bibliography
_REFERENCE_ENTRY = re.compile(r"^\[\d+\]\s+[A-Z]")

# Patterns for content to skip at document start (journal headers, etc.)
_SKIP_PATTERNS = re.compile(
    r"^(ISSN|DOI|Copyright|©|Vol\.\s*\d|http|www\.|Keywords:|Abstract\s*$|"
    r"International\s+Journal|Science\s+and\s+EN|Journal\s+of\s+)",
    re.IGNORECASE,
)


def _split_compound_blocks(blocks: list[dict]) -> list[dict]:
    """
    Split blocks that contain inline enumerations like
    '(1) first thing; (2) second thing; (3) third thing'
    into separate blocks.
    """
    result = []
    for block in blocks:
        if block["format"] != "prose":
            result.append(block)
            continue

        text = block["text"]

        # Pattern: (1) ... (2) ... (3) ... or (a) ... (b) ... etc.
        # Only split if there are 2+ enumeration markers
        parts = re.split(r"(?<=[\.\;\:])\s*\((\d+|[a-z]|[iv]+)\)\s+", text)
        if len(parts) >= 5:  # original + 2*(marker+text) minimum
            # Reconstruct: parts[0] is preamble, then alternating marker/text
            preamble = parts[0].strip()
            if preamble:
                result.append({
                    "text": preamble,
                    "format": "prose",
                    "section_path": block["section_path"],
                })
            for i in range(1, len(parts), 2):
                marker = parts[i]
                content = parts[i + 1].strip().rstrip(";.") if i + 1 < len(parts) else ""
                if content:
                    result.append({
                        "text": f"({marker}) {content}",
                        "format": "bullet",
                        "section_path": block["section_path"],
                    })
        else:
            result.append(block)

    return result


_SENTENCE_END = re.compile(r'(?<=[.!?])\s+(?=[A-Z"\'\(])')

# Common abbreviations that end with a period but aren't sentence ends
_ABBREVS = {"Mr.", "Mrs.", "Dr.", "Prof.", "Inc.", "Ltd.", "Corp.",
            "vs.", "etc.", "e.g.", "i.e.", "Fig.", "No.", "Vol.",
            "St.", "Jr.", "Sr.", "Dept.", "approx.", "est."}


def _split_sentences_safe(text: str) -> list[str]:
    """Split text into sentences, protecting abbreviations."""
    protected = text
    for abbr in _ABBREVS:
        protected = protected.replace(abbr, abbr.replace(".", "@@DOT@@"))
    parts = _SENTENCE_END.split(protected)
    return [p.replace("@@DOT@@", ".").strip() for p in parts if p.strip()]


def _merge_incomplete_blocks(blocks: list[dict]) -> list[dict]:
    """Merge prose blocks that end mid-sentence with the following prose block.

    A block is considered incomplete if it doesn't end with sentence-ending
    punctuation (.!?") and the next block starts with a lowercase letter
    (continuation of a sentence).
    """
    if not blocks:
        return blocks

    result = []
    carry = None  # text to prepend to the next block

    for block in blocks:
        if carry is not None and block["format"] == "prose":
            block = dict(block)
            block["text"] = carry + " " + block["text"]
            carry = None

        text = block["text"].rstrip()
        is_prose = block["format"] == "prose"

        if is_prose and text and not re.search(r'[.!?"\'\)]\s*$', text):
            # Ends mid-sentence — check if it's genuinely incomplete
            # (not just a short fragment or heading-like text)
            if len(text) > 50:
                carry = text
                continue

        if carry is not None:
            # Next block isn't prose, so emit the carried text as its own block
            result.append({
                "text": carry,
                "format": "prose",
                "section_path": block.get("section_path", ""),
            })
            carry = None

        result.append(block)

    if carry is not None:
        result.append({
            "text": carry,
            "format": "prose",
            "section_path": blocks[-1].get("section_path", "") if blocks else "",
        })

    return result


def _split_long_blocks(blocks: list[dict], max_len: int = 800) -> list[dict]:
    """Split prose blocks longer than max_len at sentence boundaries.

    Preserves all content — never drops text. Short blocks are kept as-is.
    """
    result = []
    for block in blocks:
        if block["format"] != "prose" or len(block["text"]) <= max_len:
            result.append(block)
            continue

        sentences = _split_sentences_safe(block["text"])
        if len(sentences) <= 1:
            result.append(block)
            continue

        current_parts = []
        current_len = 0

        for sent in sentences:
            if current_len > 0 and current_len + len(sent) > max_len:
                result.append({
                    "text": " ".join(current_parts),
                    "format": "prose",
                    "section_path": block["section_path"],
                })
                current_parts = []
                current_len = 0
            current_parts.append(sent)
            current_len += len(sent)

        if current_parts:
            result.append({
                "text": " ".join(current_parts),
                "format": "prose",
                "section_path": block["section_path"],
            })

    return result


def extract_pdf_metadata(filepath: str) -> dict:
    """Extract metadata from PDF without full content extraction."""
    import pymupdf

    doc = pymupdf.open(filepath)
    meta = doc.metadata or {}

    # Try to get title from first page large text if not in metadata
    title = meta.get("title", "").strip()
    author = meta.get("author", "").strip()

    if not title:
        font_info = _analyze_fonts(doc)
        body_size = font_info["body_size"]
        page = doc[0]
        page_blocks = page.get_text("dict")["blocks"]
        largest_size = 0
        largest_text = ""
        for b in page_blocks:
            if b["type"] != 0:
                continue
            for line in b["lines"]:
                for span in line["spans"]:
                    if span["size"] > largest_size and len(span["text"].strip()) > 5:
                        largest_size = span["size"]
                        largest_text = span["text"].strip()
        if largest_text and largest_size > body_size + 1:
            title = largest_text

    doc.close()
    return {
        "title": title or os.path.basename(filepath),
        "author": author,
        "pages": meta.get("format", ""),
    }


def extract_pdf_source(filepath: str, topic: str, source_id: str, graph,
                       title: str = "", author: str = "",
                       publication_date: str = "", url: str = "",
                       image_dir: str = "") -> dict:
    """
    Full extraction pipeline for a PDF file.

    Extracts text and images, detects structure, creates content blocks,
    writes Source + ContentBlock nodes to the graph.

    Returns a summary dict.
    """
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"PDF not found: {filepath}")

    # Default image directory
    if not image_dir:
        root = Path(__file__).parent.parent.parent
        image_dir = str(root / "data" / "images" / source_id.replace(":", "/"))

    # Extract blocks (text + images)
    raw_blocks, doc_meta = extract_pdf_blocks(filepath, image_dir=image_dir)

    # Split compound blocks (inline enumerations) — only for text blocks
    text_blocks = [b for b in raw_blocks if b["format"] != "figure"]
    figure_blocks = [b for b in raw_blocks if b["format"] == "figure"]
    text_blocks = _split_compound_blocks(text_blocks)
    blocks = text_blocks + figure_blocks

    if not blocks:
        raise ValueError(f"No content blocks extracted from {filepath}")

    # Use provided metadata or fall back to PDF metadata
    final_title = title or doc_meta.get("title", "") or os.path.basename(filepath)
    final_author = author or doc_meta.get("author", "")

    # Compute content hash
    all_text = "\n".join(b["text"] for b in blocks)
    content_hash = hashlib.sha256(all_text.encode("utf-8")).hexdigest()

    # Write Source node
    graph.add_source(
        source_id=source_id,
        topic=topic,
        source_type="pdf",
        title=final_title,
        url=url,
        author=final_author,
        publication_date=publication_date,
        content_hash=content_hash,
        metadata={
            "document_path": filepath,
            "pages": doc_meta.get("pages", 0),
            "body_font_size": doc_meta.get("body_font_size", 0),
            "image_count": len(figure_blocks),
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
            location_type="heading_path" if block["format"] != "figure" else "page",
            location_value=block.get("section_path", ""),
            format=block["format"],
            section_path=block.get("section_path", ""),
            image_path=block.get("image_path", ""),
        )

    return {
        "source_id": source_id,
        "title": final_title,
        "author": final_author,
        "block_count": len(blocks),
        "image_count": len(figure_blocks),
        "content_length": len(all_text),
        "pages": doc_meta.get("pages", 0),
    }
