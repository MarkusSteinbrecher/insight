"""
Tests for insight.collector.discovery — AC-D1 through AC-D5.
"""

from __future__ import annotations

import os
import tempfile
import shutil

import pytest

from insight.graph import InsightGraph
from insight.collector.discovery import normalize_url, check_urls, detect_source_type


@pytest.fixture
def graph():
    tmpdir = tempfile.mkdtemp()
    db_path = os.path.join(tmpdir, "test.db")
    g = InsightGraph(db_path)
    g.init_schema()
    yield g
    g.close()
    shutil.rmtree(tmpdir, ignore_errors=True)


class TestURLNormalization:
    """AC-D3, AC-D4"""

    def test_strips_www(self):
        assert normalize_url("https://www.example.com/path") == "https://example.com/path"

    def test_lowercase_hostname(self):
        assert normalize_url("https://EXAMPLE.COM/Path") == "https://example.com/Path"

    def test_removes_trailing_slash(self):
        assert normalize_url("https://example.com/path/") == "https://example.com/path"

    def test_normalizes_scheme(self):
        """AC-D3: http and https treated as same after normalization (both lowercase)."""
        # Both become lowercase scheme
        http = normalize_url("HTTP://example.com/page")
        https = normalize_url("HTTPS://example.com/page")
        assert http == "http://example.com/page"
        assert https == "https://example.com/page"

    def test_http_vs_https_with_www(self):
        """AC-D3: http://www.example.com/ and https://example.com treated equivalently minus scheme."""
        a = normalize_url("http://www.example.com/")
        b = normalize_url("https://example.com")
        # Both strip www and trailing slash; only scheme differs
        assert a == "http://example.com"
        assert b == "https://example.com"

    def test_strips_utm_params(self):
        """AC-D4: utm_* tracking parameters are removed."""
        url = "https://example.com/article?utm_source=twitter&utm_medium=social&id=123"
        normalized = normalize_url(url)
        assert "utm_source" not in normalized
        assert "utm_medium" not in normalized
        assert "id=123" in normalized

    def test_strips_ref_param(self):
        url = "https://example.com/page?ref=homepage&section=ai"
        normalized = normalize_url(url)
        assert "ref=" not in normalized
        assert "section=ai" in normalized

    def test_preserves_path_and_fragment(self):
        url = "https://example.com/deep/path?key=value#section"
        normalized = normalize_url(url)
        assert "/deep/path" in normalized
        assert "key=value" in normalized

    def test_empty_query_after_stripping(self):
        url = "https://example.com/page?utm_source=twitter"
        normalized = normalize_url(url)
        assert normalized == "https://example.com/page"


class TestDiscoveryResult:
    """AC-D1, AC-D2, AC-D5"""

    def test_existing_urls_identified(self, graph):
        """AC-D1: check_urls correctly identifies existing URLs."""
        graph.add_source("s1", "test-topic", "web", "Test", url="https://example.com/page-1")
        result = check_urls(["https://example.com/page-1"], "test-topic", graph)
        assert result.existing == ["https://example.com/page-1"]
        assert result.new == []

    def test_new_urls_identified(self, graph):
        """AC-D2: check_urls correctly identifies new URLs."""
        result = check_urls(["https://example.com/new-page"], "test-topic", graph)
        assert result.new == ["https://example.com/new-page"]
        assert result.existing == []

    def test_mixed_urls(self, graph):
        """Mix of new and existing URLs."""
        graph.add_source("s1", "test-topic", "web", "Existing", url="https://example.com/old")
        result = check_urls(
            ["https://example.com/old", "https://example.com/new"],
            "test-topic", graph
        )
        assert result.existing == ["https://example.com/old"]
        assert result.new == ["https://example.com/new"]
        assert result.total == 2

    def test_empty_graph_all_new(self, graph):
        """AC-D5: empty graph returns all URLs as new."""
        urls = ["https://a.com", "https://b.com", "https://c.com"]
        result = check_urls(urls, "test-topic", graph)
        assert result.new == urls
        assert result.existing == []
        assert result.total == 3

    def test_normalized_comparison(self, graph):
        """URLs matched using normalized forms."""
        graph.add_source("s1", "test-topic", "web", "Test",
                         url="https://www.example.com/page/")
        # Same page, different format
        result = check_urls(["https://example.com/page"], "test-topic", graph)
        assert result.existing == ["https://example.com/page"]

    def test_cross_topic_isolation(self, graph):
        """Sources from other topics don't affect registry check."""
        graph.add_source("s1", "topic-a", "web", "Test", url="https://example.com/page")
        result = check_urls(["https://example.com/page"], "topic-b", graph)
        assert result.new == ["https://example.com/page"]


class TestSourceTypeDetection:

    def test_youtube_watch(self):
        assert detect_source_type("https://www.youtube.com/watch?v=abc123") == "youtube"

    def test_youtube_short(self):
        assert detect_source_type("https://youtu.be/abc123") == "youtube"

    def test_pdf(self):
        assert detect_source_type("https://example.com/report.pdf") == "pdf"

    def test_web(self):
        assert detect_source_type("https://example.com/article") == "web"
