"""
Shared content block post-processing for all extractors.

Provides sentence-boundary-aware merging and splitting so that no
extractor produces blocks that end mid-sentence. All three extractors
(web, youtube, pdf) call clean_blocks() after initial extraction.
"""

from __future__ import annotations

import re


# Sentence-ending regex: period/exclamation/question followed by space
# and an uppercase letter, opening quote, or opening paren.
_SENTENCE_END = re.compile(r'(?<=[.!?])\s+(?=[A-Z"\'\(])')

# Also treat closing punctuation combos as sentence ends:
# ." or .) or ?" etc.
_SENTENCE_END_CLOSING = re.compile(r'(?<=[.!?]["\'\)])\s+(?=[A-Z"\'\(])')

# Common abbreviations that end with a period but aren't sentence ends
_ABBREVS = {
    "Mr.", "Mrs.", "Ms.", "Dr.", "Prof.", "Inc.", "Ltd.", "Corp.",
    "vs.", "etc.", "e.g.", "i.e.", "Fig.", "No.", "Vol.", "Rev.",
    "St.", "Jr.", "Sr.", "Dept.", "approx.", "est.", "al.",
    "Gen.", "Gov.", "Sgt.", "Cpl.", "Pvt.", "Capt.",
    "Jan.", "Feb.", "Mar.", "Apr.", "Jun.", "Jul.", "Aug.",
    "Sep.", "Sept.", "Oct.", "Nov.", "Dec.",
    "U.S.", "U.K.", "E.U.", "Ph.D.", "M.D.",
}

# Pattern to detect incomplete blocks (no sentence-ending punctuation at end)
_INCOMPLETE_END = re.compile(r'[.!?"\'\)]\s*$')


def split_sentences(text: str) -> list[str]:
    """Split text into sentences, protecting abbreviations.

    Returns a list of sentence strings. Never drops content.
    """
    protected = text
    for abbr in _ABBREVS:
        protected = protected.replace(abbr, abbr.replace(".", "@@DOT@@"))

    # Split at sentence boundaries
    parts = _SENTENCE_END.split(protected)

    # Also try splitting at closing-punctuation boundaries
    result = []
    for part in parts:
        sub = _SENTENCE_END_CLOSING.split(part)
        result.extend(sub)

    return [p.replace("@@DOT@@", ".").strip() for p in result if p.strip()]


def merge_incomplete_blocks(blocks: list[dict]) -> list[dict]:
    """Merge prose blocks that end mid-sentence with the following prose block.

    A block is considered incomplete if its text doesn't end with
    sentence-ending punctuation (.!?"\\')).
    """
    if not blocks:
        return blocks

    result = []
    carry = None  # text to prepend to the next block
    carry_section = ""

    for block in blocks:
        if carry is not None and block["format"] == "prose":
            block = dict(block)
            block["text"] = carry + " " + block["text"]
            carry = None
            carry_section = ""

        text = block["text"].rstrip()
        is_prose = block["format"] == "prose"

        if is_prose and text and not _INCOMPLETE_END.search(text):
            # Ends mid-sentence — carry it forward
            carry = text
            carry_section = block.get("section_path", "")
            continue

        if carry is not None:
            # Next block isn't prose — emit the carried text standalone
            result.append({
                "text": carry,
                "format": "prose",
                "section_path": carry_section,
                "location_value": block.get("location_value", carry_section),
            })
            carry = None
            carry_section = ""

        result.append(block)

    if carry is not None:
        result.append({
            "text": carry,
            "format": "prose",
            "section_path": carry_section,
            "location_value": carry_section,
        })

    return result


def split_long_blocks(blocks: list[dict], max_len: int = 800) -> list[dict]:
    """Split prose blocks longer than max_len at sentence boundaries.

    Preserves all content — never drops text.
    """
    result = []
    for block in blocks:
        if block["format"] != "prose" or len(block["text"]) <= max_len:
            result.append(block)
            continue

        sentences = split_sentences(block["text"])
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
                    "section_path": block.get("section_path", ""),
                    "location_value": block.get("location_value", ""),
                })
                current_parts = []
                current_len = 0
            current_parts.append(sent)
            current_len += len(sent)

        if current_parts:
            result.append({
                "text": " ".join(current_parts),
                "format": "prose",
                "section_path": block.get("section_path", ""),
                "location_value": block.get("location_value", ""),
            })

    return result


def clean_blocks(blocks: list[dict], max_len: int = 800) -> list[dict]:
    """Full post-processing pipeline for content blocks.

    1. Merge blocks that end mid-sentence
    2. Split blocks that are too long at sentence boundaries

    All extractors should call this after initial block extraction.
    """
    blocks = merge_incomplete_blocks(blocks)
    blocks = split_long_blocks(blocks, max_len=max_len)
    return blocks
