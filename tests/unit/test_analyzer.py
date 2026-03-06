"""
Tests for insight.analyzer — AC-AN1 through AC-AN15.

Uses in-memory graph with pre-populated test data.
"""

from __future__ import annotations

import os
import shutil
import tempfile

import pytest

from insight.graph import InsightGraph
from insight.analyzer.segmentation import (
    get_unsegmented_sources,
    get_source_content,
    write_segments,
    get_segmentation_stats,
)
from insight.analyzer.alignment import (
    get_claim_segments,
    write_claims,
    write_contradictions,
    get_alignment_stats,
)
from insight.analyzer.queries import get_topic_summary


@pytest.fixture
def graph():
    tmpdir = tempfile.mkdtemp()
    db_path = os.path.join(tmpdir, "test.db")
    g = InsightGraph(db_path)
    g.init_schema()
    yield g
    g.close()
    shutil.rmtree(tmpdir, ignore_errors=True)


def _add_source_with_blocks(graph, source_id, topic, title="Test Source", n_blocks=3):
    """Helper to add a source with content blocks."""
    graph.add_source(source_id, topic, "web", title, url=f"https://example.com/{source_id}")
    for i in range(1, n_blocks + 1):
        graph.add_content_block(
            f"{source_id}:block-{i:03d}",
            source_id,
            text=f"Block {i} content for {title}.",
            position=i,
            location_type="heading_path",
            location_value=f"Section {i}",
            format="prose",
            section_path=f"Section {i}",
        )


class TestGetUnsegmentedSources:
    """AC-AN1, AC-AN2"""

    def test_returns_unsegmented_only(self, graph):
        """AC-AN1: returns only sources with zero segments."""
        _add_source_with_blocks(graph, "s1", "test", "Source One")
        _add_source_with_blocks(graph, "s2", "test", "Source Two")

        # Segment source 1 only
        graph.add_segment("s1:seg-001", "s1:block-001", "Claim text", "claim", 1)

        result = get_unsegmented_sources("test", graph)
        assert len(result) == 1
        assert result[0]["source_id"] == "s2"

    def test_returns_empty_when_all_segmented(self, graph):
        """AC-AN2: returns empty list when all sources are segmented."""
        _add_source_with_blocks(graph, "s1", "test")
        graph.add_segment("s1:seg-001", "s1:block-001", "Text", "claim", 1)

        result = get_unsegmented_sources("test", graph)
        assert result == []


class TestGetSourceContent:
    """AC-AN3"""

    def test_returns_blocks_ordered(self, graph):
        """AC-AN3: returns blocks ordered by position."""
        _add_source_with_blocks(graph, "s1", "test", "Test Source", n_blocks=5)
        content = get_source_content("s1", graph)

        assert content["source_id"] == "s1"
        assert content["title"] == "Test Source"
        assert len(content["blocks"]) == 5
        positions = [b["position"] for b in content["blocks"]]
        assert positions == [1, 2, 3, 4, 5]

    def test_returns_none_for_missing(self, graph):
        assert get_source_content("nonexistent", graph) is None


class TestWriteSegments:
    """AC-AN4, AC-AN5"""

    def test_creates_nodes_and_edges(self, graph):
        """AC-AN4: writes Segment nodes and SEGMENTED_FROM edges."""
        _add_source_with_blocks(graph, "s1", "test")

        segments = [
            {"block_id": "s1:block-001", "text": "AI adoption is growing.", "segment_type": "claim", "position": 1},
            {"block_id": "s1:block-001", "text": "72% of companies use AI.", "segment_type": "statistic", "position": 2},
            {"block_id": "s1:block-002", "text": "Background info here.", "segment_type": "context", "position": 3},
        ]

        count = write_segments("s1", segments, graph)
        assert count == 3

        # Verify segments exist
        all_segs = graph.get_segments("s1")
        assert len(all_segs) == 3

        # Verify linked to blocks
        block1_segs = graph.get_segments_for_block("s1:block-001")
        assert len(block1_segs) == 2

    def test_auto_generates_ids(self, graph):
        """AC-AN5: auto-generates sequential segment IDs."""
        _add_source_with_blocks(graph, "s1", "test")

        segments = [
            {"block_id": "s1:block-001", "text": "First", "segment_type": "claim", "position": 1},
            {"block_id": "s1:block-002", "text": "Second", "segment_type": "claim", "position": 2},
        ]

        write_segments("s1", segments, graph)
        all_segs = graph.get_segments("s1")
        seg_ids = [s["segment_id"] for s in all_segs]
        assert "s1:seg-001" in seg_ids
        assert "s1:seg-002" in seg_ids


class TestSegmentationStats:
    """AC-AN6, AC-AN7"""

    def test_composition_breakdown(self, graph):
        """AC-AN6: returns correct composition breakdown."""
        _add_source_with_blocks(graph, "s1", "test", n_blocks=1)

        segments = [
            {"block_id": "s1:block-001", "text": "Claim 1", "segment_type": "claim", "position": 1},
            {"block_id": "s1:block-001", "text": "Claim 2", "segment_type": "claim", "position": 2},
            {"block_id": "s1:block-001", "text": "Stat 1", "segment_type": "statistic", "position": 3},
            {"block_id": "s1:block-001", "text": "Noise", "segment_type": "noise", "position": 4},
        ]
        write_segments("s1", segments, graph)

        stats = get_segmentation_stats("s1", graph)
        assert stats["total_segments"] == 4
        assert stats["composition"]["claim"]["count"] == 2
        assert stats["composition"]["claim"]["pct"] == 50.0
        assert stats["composition"]["statistic"]["count"] == 1
        assert stats["composition"]["noise"]["count"] == 1

    def test_signal_ratio(self, graph):
        """AC-AN7: signal_ratio excludes noise."""
        _add_source_with_blocks(graph, "s1", "test", n_blocks=1)

        segments = [
            {"block_id": "s1:block-001", "text": "Claim", "segment_type": "claim", "position": 1},
            {"block_id": "s1:block-001", "text": "Claim 2", "segment_type": "claim", "position": 2},
            {"block_id": "s1:block-001", "text": "Noise", "segment_type": "noise", "position": 3},
        ]
        write_segments("s1", segments, graph)

        stats = get_segmentation_stats("s1", graph)
        assert stats["signal_ratio"] == pytest.approx(66.7, abs=0.1)

    def test_empty_source(self, graph):
        _add_source_with_blocks(graph, "s1", "test")
        stats = get_segmentation_stats("s1", graph)
        assert stats["total_segments"] == 0


class TestGetClaimSegments:
    """AC-AN8, AC-AN9"""

    def test_filters_by_type(self, graph):
        """AC-AN8: returns only segments of specified types."""
        _add_source_with_blocks(graph, "s1", "test", n_blocks=1)
        segments = [
            {"block_id": "s1:block-001", "text": "A claim", "segment_type": "claim", "position": 1},
            {"block_id": "s1:block-001", "text": "Context", "segment_type": "context", "position": 2},
            {"block_id": "s1:block-001", "text": "A stat", "segment_type": "statistic", "position": 3},
        ]
        write_segments("s1", segments, graph)

        result = get_claim_segments("test", graph, types=["claim"])
        assert len(result) == 1
        assert len(result[0]["segments"]) == 1
        assert result[0]["segments"][0]["segment_type"] == "claim"

    def test_groups_by_source(self, graph):
        """AC-AN9: groups segments by source."""
        _add_source_with_blocks(graph, "s1", "test", "Source One", n_blocks=1)
        _add_source_with_blocks(graph, "s2", "test", "Source Two", n_blocks=1)

        write_segments("s1", [
            {"block_id": "s1:block-001", "text": "Claim from s1", "segment_type": "claim", "position": 1},
        ], graph)
        write_segments("s2", [
            {"block_id": "s2:block-001", "text": "Claim from s2", "segment_type": "claim", "position": 1},
        ], graph)

        result = get_claim_segments("test", graph, types=["claim"])
        assert len(result) == 2
        source_ids = {r["source_id"] for r in result}
        assert source_ids == {"s1", "s2"}

    def test_default_types(self, graph):
        """Default types include claim, recommendation, statistic, evidence."""
        _add_source_with_blocks(graph, "s1", "test", n_blocks=1)
        segments = [
            {"block_id": "s1:block-001", "text": "Claim", "segment_type": "claim", "position": 1},
            {"block_id": "s1:block-001", "text": "Rec", "segment_type": "recommendation", "position": 2},
            {"block_id": "s1:block-001", "text": "Stat", "segment_type": "statistic", "position": 3},
            {"block_id": "s1:block-001", "text": "Evidence", "segment_type": "evidence", "position": 4},
            {"block_id": "s1:block-001", "text": "Context", "segment_type": "context", "position": 5},
        ]
        write_segments("s1", segments, graph)

        result = get_claim_segments("test", graph)
        assert len(result[0]["segments"]) == 4  # context excluded


class TestWriteClaims:
    """AC-AN10, AC-AN11"""

    def test_creates_claims_and_links(self, graph):
        """AC-AN10, AC-AN11: creates Claim nodes and SUPPORTS edges."""
        _add_source_with_blocks(graph, "s1", "test", n_blocks=1)
        _add_source_with_blocks(graph, "s2", "test", n_blocks=1)
        write_segments("s1", [
            {"block_id": "s1:block-001", "text": "AI grows", "segment_type": "claim", "position": 1},
        ], graph)
        write_segments("s2", [
            {"block_id": "s2:block-001", "text": "AI expanding", "segment_type": "claim", "position": 1},
        ], graph)

        claims = [{
            "claim_id": "test:cc-001",
            "claim_category": "canonical",
            "theme": "AI growth",
            "summary": "AI adoption is growing rapidly.",
            "claim_type": "empirical",
            "strength": "strongly-supported",
            "segment_ids": ["s1:seg-001", "s2:seg-001"],
        }]

        count = write_claims("test", claims, graph)
        assert count == 1

        # Verify claim exists
        claim = graph.get_claim("test:cc-001")
        assert claim is not None
        assert claim["theme"] == "AI growth"

        # Verify segments linked
        supporting = graph.get_supporting_segments("test:cc-001")
        assert len(supporting) == 2


class TestWriteContradictions:
    """AC-AN12"""

    def test_creates_contradicts_edges(self, graph):
        """AC-AN12: creates CONTRADICTS edges between claim pairs."""
        graph.add_claim("test:cc-001", "test", "canonical", "Theme A", "Summary A")
        graph.add_claim("test:cc-002", "test", "canonical", "Theme B", "Summary B")

        count = write_contradictions([{
            "claim_id_1": "test:cc-001",
            "claim_id_2": "test:cc-002",
            "description": "They disagree on approach.",
        }], graph)

        assert count == 1
        contradictions = graph.get_contradictions("test:cc-001")
        assert len(contradictions) == 1


class TestAlignmentStats:
    """AC-AN13"""

    def test_correct_counts(self, graph):
        """AC-AN13: returns correct counts per category."""
        _add_source_with_blocks(graph, "s1", "test", n_blocks=1)
        _add_source_with_blocks(graph, "s2", "test", n_blocks=1)
        write_segments("s1", [
            {"block_id": "s1:block-001", "text": "Claim", "segment_type": "claim", "position": 1},
        ], graph)
        write_segments("s2", [
            {"block_id": "s2:block-001", "text": "Claim", "segment_type": "claim", "position": 1},
        ], graph)

        write_claims("test", [
            {"claim_id": "test:cc-001", "claim_category": "canonical", "theme": "T1",
             "summary": "S1", "segment_ids": ["s1:seg-001", "s2:seg-001"]},
            {"claim_id": "test:uc-001", "claim_category": "unique", "theme": "T2",
             "summary": "S2", "segment_ids": ["s1:seg-001"]},
        ], graph)

        stats = get_alignment_stats("test", graph)
        assert stats["total_claims"] == 2
        assert stats["canonical"] == 1
        assert stats["unique"] == 1
        assert stats["contradiction"] == 0
        assert stats["total_segments_linked"] == 3
        assert stats["sources_covered"] == 2


class TestTopicSummary:
    """AC-AN14, AC-AN15"""

    def test_correct_counts(self, graph):
        """AC-AN14: returns correct counts for all node types."""
        _add_source_with_blocks(graph, "s1", "test", n_blocks=3)
        _add_source_with_blocks(graph, "s2", "test", n_blocks=2)

        write_segments("s1", [
            {"block_id": "s1:block-001", "text": "Seg", "segment_type": "claim", "position": 1},
        ], graph)

        graph.add_claim("test:cc-001", "test", "canonical", "Theme", "Summary")

        summary = get_topic_summary("test", graph)
        assert summary["topic"] == "test"
        assert summary["sources"] == 2
        assert summary["content_blocks"] == 5
        assert summary["segments"] == 1
        assert summary["claims"] == 1

    def test_segmented_vs_unsegmented(self, graph):
        """AC-AN15: correctly counts segmented vs unsegmented sources."""
        _add_source_with_blocks(graph, "s1", "test", n_blocks=2)
        _add_source_with_blocks(graph, "s2", "test", n_blocks=2)
        _add_source_with_blocks(graph, "s3", "test", n_blocks=2)

        # Segment only s1 and s2
        write_segments("s1", [
            {"block_id": "s1:block-001", "text": "Seg", "segment_type": "claim", "position": 1},
        ], graph)
        write_segments("s2", [
            {"block_id": "s2:block-001", "text": "Seg", "segment_type": "claim", "position": 1},
        ], graph)

        summary = get_topic_summary("test", graph)
        assert summary["segmented_sources"] == 2
        assert summary["unsegmented_sources"] == 1
