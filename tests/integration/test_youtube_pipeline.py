"""
Integration tests for YouTube extraction pipeline — AC-Y7 through AC-Y10.

These tests use mocked transcript/metadata to avoid network dependency.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from unittest.mock import patch

import pytest

from insight.graph import InsightGraph
from insight.collector.youtube import extract_youtube_source


# Sample transcript data (mimics youtube-transcript-api output)
SAMPLE_TRANSCRIPT = [
    {"text": "Welcome to this presentation.", "start": 0.0, "duration": 2.5},
    {"text": "Today we will discuss AI adoption.", "start": 3.0, "duration": 3.0},
    {"text": "Let me start with an overview.", "start": 6.5, "duration": 2.0},
    # Gap of 10 seconds — new block
    {"text": "The first key finding is about scale.", "start": 18.5, "duration": 3.0},
    {"text": "Enterprise AI has reached 72 percent adoption.", "start": 22.0, "duration": 3.5},
    # Another gap
    {"text": "In conclusion, AI adoption is accelerating.", "start": 35.0, "duration": 3.0},
    {"text": "Thank you for watching.", "start": 38.5, "duration": 2.0},
]

SAMPLE_OEMBED = {
    "title": "AI Adoption in Enterprise 2025",
    "author": "Tech Insights Channel",
    "channel_url": "https://www.youtube.com/@techinsights",
}


def _mock_fetch_transcript(video_id):
    return SAMPLE_TRANSCRIPT


def _mock_fetch_metadata(video_id):
    return SAMPLE_OEMBED.copy()


@pytest.fixture
def graph():
    tmpdir = tempfile.mkdtemp()
    db_path = os.path.join(tmpdir, "test.db")
    g = InsightGraph(db_path)
    g.init_schema()
    yield g
    g.close()
    shutil.rmtree(tmpdir, ignore_errors=True)


def _extract(graph):
    with patch("insight.collector.youtube.fetch_transcript", _mock_fetch_transcript), \
         patch("insight.collector.youtube.fetch_video_metadata", _mock_fetch_metadata):
        return extract_youtube_source(
            url="https://www.youtube.com/watch?v=test123",
            topic="test-topic",
            source_id="test:source-001",
            graph=graph
        )


class TestYouTubePipeline:
    """AC-Y7 through AC-Y10"""

    def test_source_node_created(self, graph):
        """AC-Y9: writes one Source node with source_type: youtube."""
        _extract(graph)
        source = graph.get_source("test:source-001")
        assert source is not None
        assert source["source_type"] == "youtube"
        assert source["url"] == "https://www.youtube.com/watch?v=test123"

    def test_source_metadata(self, graph):
        """AC-Y10: source metadata includes video_id and duration_seconds."""
        _extract(graph)
        source = graph.get_source("test:source-001")
        metadata = json.loads(source["metadata"])
        assert metadata["video_id"] == "test123"
        assert "duration_seconds" in metadata
        assert metadata["transcript_segments"] == len(SAMPLE_TRANSCRIPT)

    def test_block_location_value(self, graph):
        """AC-Y7: ContentBlock location_value is formatted as 't:{seconds}'."""
        _extract(graph)
        blocks = graph.get_content_blocks("test:source-001")
        assert len(blocks) > 0
        for block in blocks:
            assert block["location_value"].startswith("t:")
            assert block["location_type"] == "timestamp"

    def test_block_metadata_has_timestamp_url(self, graph):
        """AC-Y8: ContentBlock metadata includes timestamp_url."""
        _extract(graph)
        blocks = graph.get_content_blocks("test:source-001")
        for block in blocks:
            meta = json.loads(block["metadata"])
            assert "timestamp_url" in meta
            assert "youtube.com/watch?v=test123&t=" in meta["timestamp_url"]

    def test_blocks_have_content(self, graph):
        """Blocks contain grouped transcript text."""
        _extract(graph)
        blocks = graph.get_content_blocks("test:source-001")
        assert len(blocks) >= 2
        all_text = " ".join(b["text"] for b in blocks)
        assert "Welcome" in all_text
        assert "conclusion" in all_text
