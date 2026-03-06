"""
Tests for insight.collector.web — AC-W1 through AC-W9.

Uses HTML fixtures, no network access.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from insight.collector.web import extract_content_blocks, extract_metadata


FIXTURES = Path(__file__).parent.parent / "fixtures"


def _load_fixture(name: str) -> BeautifulSoup:
    html = (FIXTURES / name).read_text()
    return BeautifulSoup(html, "html.parser")


class TestContentBlockExtraction:
    """AC-W1 through AC-W6"""

    @pytest.fixture
    def blocks(self):
        soup = _load_fixture("sample_article.html")
        return extract_content_blocks(soup)

    def test_format_values(self, blocks):
        """AC-W1: blocks have correct format values."""
        formats = {b["format"] for b in blocks}
        assert "heading" in formats
        assert "prose" in formats
        assert "bullet" in formats
        assert "quote" in formats
        assert "table_cell" in formats
        assert "caption" in formats

    def test_heading_blocks_present(self, blocks):
        headings = [b for b in blocks if b["format"] == "heading"]
        heading_texts = [h["text"] for h in headings]
        assert "Enterprise AI Adoption Trends 2025" in heading_texts
        assert "Introduction" in heading_texts
        assert "Key Findings" in heading_texts

    def test_section_path_nested(self, blocks):
        """AC-W2: section paths track nested heading hierarchy."""
        # Find block under Introduction > Background
        bg_blocks = [b for b in blocks if "Introduction > Background" in b["section_path"]]
        assert len(bg_blocks) > 0

    def test_section_path_deeper_heading(self):
        """AC-W3: deeper heading correctly updates stack."""
        soup = _load_fixture("nested_elements.html")
        blocks = extract_content_blocks(soup)

        # After "Section Two > Subsection A", content should have that path
        sub_a = [b for b in blocks if b["section_path"] == "Test Article > Section Two > Subsection A"
                 and b["format"] != "heading"]
        assert len(sub_a) > 0, f"No blocks under Section Two > Subsection A. Paths: {[b['section_path'] for b in blocks]}"

    def test_section_path_same_level_heading(self):
        """AC-W4: same-level heading pops previous and replaces."""
        soup = _load_fixture("nested_elements.html")
        blocks = extract_content_blocks(soup)

        # After Subsection B, content should be under Section Two > Subsection B (not A)
        sub_b = [b for b in blocks if b["section_path"] == "Test Article > Section Two > Subsection B"
                 and b["format"] != "heading"]
        assert len(sub_b) > 0

        # Section Three should NOT have subsection in its path
        sec3 = [b for b in blocks if b["section_path"] == "Test Article > Section Three"
                and b["format"] != "heading"]
        assert len(sec3) > 0, f"No blocks under Section Three alone. Paths: {[b['section_path'] for b in blocks]}"

    def test_boilerplate_stops_extraction(self, blocks):
        """AC-W5: boilerplate headings cause extraction to stop."""
        # "Contact Us" is in the sample — nothing after it should appear
        all_text = " ".join(b["text"] for b in blocks)
        assert "research@gartner.example.com" not in all_text
        assert "For more information" not in all_text

    def test_no_duplicate_nested_elements(self):
        """AC-W6: nested <li><p> produces only one block."""
        soup = _load_fixture("nested_elements.html")
        blocks = extract_content_blocks(soup)

        texts = [b["text"] for b in blocks]
        nested_text = "Nested paragraph inside list item should not duplicate"
        count = texts.count(nested_text)
        assert count == 1, f"Expected 1 occurrence, got {count}"

    def test_prose_blocks_have_content(self, blocks):
        prose = [b for b in blocks if b["format"] == "prose"]
        assert len(prose) >= 3
        for b in prose:
            assert len(b["text"]) > 10

    def test_bullet_blocks(self, blocks):
        bullets = [b for b in blocks if b["format"] == "bullet"]
        assert len(bullets) >= 3  # 3 in ul + 3 in ol

    def test_location_value_matches_section_path(self, blocks):
        """For web sources, location_value equals section_path."""
        for b in blocks:
            assert b["location_value"] == b["section_path"]

    def test_nav_content_excluded(self, blocks):
        """Nav elements stripped, no 'Menu' or 'Home' blocks."""
        texts = [b["text"] for b in blocks]
        assert "Menu" not in texts
        assert "Home" not in texts

    def test_fallback_to_body(self):
        """Minimal page without article/main falls back to body."""
        soup = _load_fixture("minimal_page.html")
        blocks = extract_content_blocks(soup)
        assert len(blocks) == 2


class TestMetadataExtraction:
    """AC-W7 through AC-W9"""

    def test_title_from_og(self):
        """AC-W7: title from og:title when present."""
        soup = _load_fixture("sample_article.html")
        meta = extract_metadata(soup, "https://gartner.com/article")
        # og:title is "Enterprise AI Adoption Trends 2025 | Gartner Research"
        # Trailing site name should be stripped
        assert "Enterprise AI Adoption Trends 2025" in meta["title"]
        assert "Gartner Research" not in meta["title"]

    def test_title_fallback_chain(self):
        """AC-W8: falls back to title tag when no og:title."""
        html = '<html><head><title>Fallback Title</title></head><body></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        meta = extract_metadata(soup, "https://example.com")
        assert meta["title"] == "Fallback Title"

    def test_title_untitled_fallback(self):
        """AC-W8: falls back to Untitled when no title at all."""
        html = '<html><head></head><body></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        meta = extract_metadata(soup, "https://example.com")
        assert meta["title"] == "Untitled"

    def test_author_from_meta(self):
        soup = _load_fixture("sample_article.html")
        meta = extract_metadata(soup, "https://gartner.com/article")
        assert meta["author"] == "Dr. Jane Smith"

    def test_author_fallback_to_og_site_name(self):
        html = '<html><head><meta property="og:site_name" content="TechCrunch"></head><body></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        meta = extract_metadata(soup, "https://techcrunch.com/article")
        assert meta["author"] == "TechCrunch"

    def test_author_fallback_to_domain(self):
        html = '<html><head></head><body></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        meta = extract_metadata(soup, "https://www.mckinsey.com/article")
        assert meta["author"] == "McKinsey"

    def test_date_format(self):
        """AC-W9: date is YYYY-MM-DD or empty."""
        soup = _load_fixture("sample_article.html")
        meta = extract_metadata(soup, "https://gartner.com/article")
        assert meta["date"] == "2025-03-15"

    def test_date_empty_when_missing(self):
        """AC-W9: empty string when no date found."""
        html = '<html><head></head><body></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        meta = extract_metadata(soup, "https://example.com")
        assert meta["date"] == ""

    def test_date_from_json_ld(self):
        html = '''<html><head>
            <script type="application/ld+json">{"datePublished": "2025-06-01T12:00:00Z"}</script>
        </head><body></body></html>'''
        soup = BeautifulSoup(html, "html.parser")
        meta = extract_metadata(soup, "https://example.com")
        assert meta["date"] == "2025-06-01"

    def test_description_extracted(self):
        soup = _load_fixture("sample_article.html")
        meta = extract_metadata(soup, "https://gartner.com/article")
        assert "enterprise ai adoption" in meta["description"].lower()
