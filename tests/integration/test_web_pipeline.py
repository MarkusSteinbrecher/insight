"""
Integration tests for web extraction pipeline — AC-W10, AC-W11, AC-W12, AC-SR1 through AC-SR4.

These tests use the sample_article.html fixture served by a local HTTP server
to avoid network dependency.
"""

from __future__ import annotations

import os
import shutil
import tempfile
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

import pytest

from insight.graph import InsightGraph
from insight.collector.web import extract_web_source, extract_content_blocks
from insight.collector.discovery import check_urls


FIXTURES = Path(__file__).parent.parent / "fixtures"


class QuietHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, directory=None, **kwargs):
        super().__init__(*args, directory=str(FIXTURES), **kwargs)

    def log_message(self, format, *args):
        pass  # Suppress server logs


@pytest.fixture(scope="module")
def local_server():
    """Start a local HTTP server serving the fixtures directory."""
    server = HTTPServer(("127.0.0.1", 0), QuietHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


@pytest.fixture
def graph():
    tmpdir = tempfile.mkdtemp()
    db_path = os.path.join(tmpdir, "test.db")
    g = InsightGraph(db_path)
    g.init_schema()
    yield g
    g.close()
    shutil.rmtree(tmpdir, ignore_errors=True)


class TestWebPipeline:
    """AC-W10, AC-W11, AC-W12"""

    def test_writes_source_and_blocks(self, local_server, graph):
        """AC-W10: extract_web_source writes one Source node and N ContentBlock nodes."""
        url = f"{local_server}/sample_article.html"
        result = extract_web_source(url, "test-topic", "test:source-001", graph)

        # Source node created
        source = graph.get_source("test:source-001")
        assert source is not None
        assert source["source_type"] == "web"
        assert source["topic"] == "test-topic"
        assert result["block_count"] > 5

    def test_blocks_linked_via_contains(self, local_server, graph):
        """AC-W11: all ContentBlock nodes linked to Source via CONTAINS edges."""
        url = f"{local_server}/sample_article.html"
        result = extract_web_source(url, "test-topic", "test:source-001", graph)

        blocks = graph.get_content_blocks("test:source-001")
        assert len(blocks) == result["block_count"]

    def test_content_hash_deterministic(self, local_server, graph):
        """AC-W12: content hash is deterministic — same content, same hash."""
        url = f"{local_server}/sample_article.html"
        result1 = extract_web_source(url, "test-topic", "test:source-001", graph)

        # Create a second graph to extract again
        tmpdir2 = tempfile.mkdtemp()
        g2 = InsightGraph(os.path.join(tmpdir2, "test2.db"))
        g2.init_schema()
        result2 = extract_web_source(url, "test-topic", "test:source-002", g2)

        s1 = graph.get_source("test:source-001")
        s2 = g2.get_source("test:source-002")
        assert s1["content_hash"] == s2["content_hash"]
        g2.close()
        shutil.rmtree(tmpdir2, ignore_errors=True)


class TestSourceRegistry:
    """AC-SR1 through AC-SR4"""

    def test_collected_source_found_by_discover(self, local_server, graph):
        """AC-SR1: after collecting, discover shows URL as existing."""
        url = f"{local_server}/sample_article.html"
        extract_web_source(url, "test-topic", "test:source-001", graph)

        result = check_urls([url], "test-topic", graph)
        assert result.existing == [url]
        assert result.new == []

    def test_cross_topic_isolation(self, local_server, graph):
        """AC-SR2: sources from different topics don't cross-contaminate."""
        url = f"{local_server}/sample_article.html"
        extract_web_source(url, "topic-a", "topic-a:source-001", graph)

        result = check_urls([url], "topic-b", graph)
        assert result.new == [url]

    def test_source_id_format(self, local_server, graph):
        """AC-SR4: source IDs follow {topic}:source-{NNN} format."""
        url = f"{local_server}/sample_article.html"
        source_id = "my-topic:source-001"
        extract_web_source(url, "my-topic", source_id, graph)

        source = graph.get_source(source_id)
        assert source is not None
        assert source["source_id"] == "my-topic:source-001"
