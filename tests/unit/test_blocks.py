"""Tests for insight.collector.blocks — shared content block post-processing."""

from __future__ import annotations

from insight.collector.blocks import (
    split_sentences, merge_incomplete_blocks, split_long_blocks, clean_blocks,
)


class TestSplitSentences:

    def test_basic_split(self):
        text = "First sentence. Second sentence. Third sentence."
        parts = split_sentences(text)
        assert len(parts) == 3

    def test_preserves_abbreviations(self):
        text = "Dr. Smith works at Inc. Corp. He is great."
        parts = split_sentences(text)
        assert any("Dr. Smith" in p for p in parts)

    def test_handles_question_marks(self):
        text = "Is this true? Yes it is. Really?"
        parts = split_sentences(text)
        assert len(parts) == 3

    def test_single_sentence(self):
        text = "Just one sentence here."
        parts = split_sentences(text)
        assert parts == ["Just one sentence here."]

    def test_closing_quote_split(self):
        text = 'He said "yes." She said "no." They agreed.'
        parts = split_sentences(text)
        assert len(parts) >= 2

    def test_us_abbreviation(self):
        text = "The U.S. government announced policy. Another sentence."
        parts = split_sentences(text)
        assert any("U.S." in p for p in parts)


class TestMergeIncompleteBlocks:

    def test_merges_mid_sentence_blocks(self):
        blocks = [
            {"text": "This is the start of a sentence that", "format": "prose",
             "section_path": "A", "location_value": "A"},
            {"text": "continues here and ends properly.", "format": "prose",
             "section_path": "A", "location_value": "A"},
        ]
        result = merge_incomplete_blocks(blocks)
        assert len(result) == 1
        assert "continues here" in result[0]["text"]

    def test_preserves_complete_blocks(self):
        blocks = [
            {"text": "Complete sentence.", "format": "prose",
             "section_path": "A", "location_value": "A"},
            {"text": "Another complete sentence.", "format": "prose",
             "section_path": "A", "location_value": "A"},
        ]
        result = merge_incomplete_blocks(blocks)
        assert len(result) == 2

    def test_skips_non_prose(self):
        blocks = [
            {"text": "Incomplete start that", "format": "prose",
             "section_path": "A", "location_value": "A"},
            {"text": "A Heading", "format": "heading",
             "section_path": "A", "location_value": "A"},
            {"text": "Next paragraph starts fresh.", "format": "prose",
             "section_path": "A", "location_value": "A"},
        ]
        result = merge_incomplete_blocks(blocks)
        # The incomplete prose becomes standalone, heading stays, next prose stays
        assert len(result) == 3
        assert result[0]["format"] == "prose"
        assert result[1]["format"] == "heading"

    def test_handles_closing_punctuation(self):
        blocks = [
            {"text": 'She said "hello."', "format": "prose",
             "section_path": "", "location_value": ""},
            {"text": "Then she left.", "format": "prose",
             "section_path": "", "location_value": ""},
        ]
        result = merge_incomplete_blocks(blocks)
        assert len(result) == 2  # Both are complete

    def test_handles_closing_paren(self):
        blocks = [
            {"text": "According to the report (2026).", "format": "prose",
             "section_path": "", "location_value": ""},
            {"text": "Another finding.", "format": "prose",
             "section_path": "", "location_value": ""},
        ]
        result = merge_incomplete_blocks(blocks)
        assert len(result) == 2

    def test_chain_merge(self):
        blocks = [
            {"text": "Start of a long sentence that", "format": "prose",
             "section_path": "", "location_value": ""},
            {"text": "continues through another fragment and", "format": "prose",
             "section_path": "", "location_value": ""},
            {"text": "finally ends here.", "format": "prose",
             "section_path": "", "location_value": ""},
        ]
        result = merge_incomplete_blocks(blocks)
        assert len(result) == 1
        assert result[0]["text"].endswith("here.")

    def test_empty_input(self):
        assert merge_incomplete_blocks([]) == []


class TestSplitLongBlocks:

    def test_splits_at_sentence_boundary(self):
        # Create a block with two sentences that together exceed max_len
        sent1 = "A" * 500 + "."
        sent2 = "B" * 500 + "."
        blocks = [{"text": f"{sent1} {sent2}", "format": "prose",
                    "section_path": "", "location_value": ""}]
        result = split_long_blocks(blocks, max_len=600)
        assert len(result) == 2

    def test_preserves_short_blocks(self):
        blocks = [{"text": "Short text.", "format": "prose",
                    "section_path": "", "location_value": ""}]
        result = split_long_blocks(blocks, max_len=800)
        assert len(result) == 1

    def test_skips_non_prose(self):
        blocks = [{"text": "A" * 1000, "format": "heading",
                    "section_path": "", "location_value": ""}]
        result = split_long_blocks(blocks, max_len=800)
        assert len(result) == 1

    def test_preserves_all_content(self):
        original = "Sentence one. Sentence two. Sentence three. Sentence four."
        blocks = [{"text": original, "format": "prose",
                    "section_path": "", "location_value": ""}]
        result = split_long_blocks(blocks, max_len=30)
        reconstructed = " ".join(b["text"] for b in result)
        assert reconstructed == original


class TestCleanBlocks:

    def test_merge_then_split(self):
        # Incomplete block followed by a long complete block
        blocks = [
            {"text": "This starts but", "format": "prose",
             "section_path": "", "location_value": ""},
            {"text": "continues. " + "X" * 900 + ".", "format": "prose",
             "section_path": "", "location_value": ""},
        ]
        result = clean_blocks(blocks, max_len=800)
        # Should merge first (incomplete + next), then split if too long
        assert all(b["format"] == "prose" for b in result)
        # All content preserved
        total = " ".join(b["text"] for b in result)
        assert "This starts but" in total
        assert "continues." in total
