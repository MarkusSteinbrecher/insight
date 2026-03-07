"""
Tests for insight.exporter — AC-P1 through AC-P9.

Uses in-memory graph with test data, writes to temp directory.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile

import pytest

from insight.graph import InsightGraph
from insight.exporter.export import (
    export_topics,
    export_stats,
    export_sources,
    export_all,
)


@pytest.fixture
def graph():
    tmpdir = tempfile.mkdtemp()
    db_path = os.path.join(tmpdir, "test.db")
    g = InsightGraph(db_path)
    g.init_schema()
    yield g
    g.close()
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def output_dir():
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)


def _populate_graph(graph):
    """Add test data: 2 topics, sources, extracts, claims."""
    # Topic 1: ea-for-ai — 3 sources, extracts, claims
    for i in range(1, 4):
        sid = f"ea-for-ai:source-{i:03d}"
        graph.add_source(sid, "ea-for-ai", "web" if i <= 2 else "pdf",
                         f"Source {i}", url=f"https://example.com/ea-{i}")
        for j in range(1, 4):
            eid = f"{sid}:extract-{j:03d}"
            graph.add_extract(eid, sid, f"Extract {j} text", j,
                              format="prose", extract_type="assertion",
                              section_path=f"Section {j}")

    graph.add_claim("ea-for-ai:cc-001", "ea-for-ai", "canonical",
                     "AI Growth", "AI is growing")
    graph.add_claim("ea-for-ai:uc-001", "ea-for-ai", "unique",
                     "Novel Point", "Something new")

    # Topic 2: ai-pm — 1 source, no extracts
    graph.add_source("ai-pm:source-001", "ai-pm", "web",
                     "PM Source", url="https://example.com/pm-1")


class TestExportTopics:
    """AC-P1, AC-P2, AC-P3"""

    def test_produces_valid_manifest(self, graph, output_dir):
        """AC-P1: produces topics.json with all topics."""
        _populate_graph(graph)
        topics = export_topics(graph, output_dir)

        path = os.path.join(output_dir, "topics.json")
        assert os.path.exists(path)

        with open(path) as f:
            data = json.load(f)

        assert len(data["topics"]) == 2
        slugs = {t["slug"] for t in data["topics"]}
        assert slugs == {"ea-for-ai", "ai-pm"}

    def test_default_topic_most_sources(self, graph, output_dir):
        """AC-P2: default_topic is topic with most sources."""
        _populate_graph(graph)
        export_topics(graph, output_dir)

        with open(os.path.join(output_dir, "topics.json")) as f:
            data = json.load(f)

        assert data["default_topic"] == "ea-for-ai"  # 3 sources vs 1

    def test_phase_from_graph_state(self, graph, output_dir):
        """AC-P3: phase determined from graph state."""
        _populate_graph(graph)
        topics = export_topics(graph, output_dir)

        topic_map = {t["slug"]: t for t in topics}
        assert topic_map["ea-for-ai"]["phase"] == 3  # has claims
        assert topic_map["ai-pm"]["phase"] == 0  # sources only


class TestExportStats:
    """AC-P4, AC-P5"""

    def test_source_count_and_types(self, graph, output_dir):
        """AC-P4: correct source count and type breakdown."""
        _populate_graph(graph)
        stats = export_stats("ea-for-ai", graph, output_dir)

        assert stats["sources"] == 3
        assert stats["source_types"]["web"] == 2
        assert stats["source_types"]["pdf"] == 1

        # Verify file exists and is valid JSON
        path = os.path.join(output_dir, "ea-for-ai", "stats.json")
        assert os.path.exists(path)
        with open(path) as f:
            json.load(f)  # Should not raise

    def test_extract_and_claim_counts(self, graph, output_dir):
        """AC-P5: correct extract and claim counts."""
        _populate_graph(graph)
        stats = export_stats("ea-for-ai", graph, output_dir)

        assert stats["total_extracts"] == 9  # 3 sources × 3 extracts
        assert stats["canonical_claims"] == 1
        assert stats["unique_claims"] == 1
        assert stats["contradictions"] == 0

    def test_zero_counts_when_not_analyzed(self, graph, output_dir):
        """AC-P5: zero when not yet analyzed."""
        _populate_graph(graph)
        stats = export_stats("ai-pm", graph, output_dir)

        assert stats["sources"] == 1
        assert stats["total_extracts"] == 0
        assert stats["canonical_claims"] == 0


class TestExportSources:
    """AC-P6, AC-P7"""

    def test_lists_all_sources(self, graph, output_dir):
        """AC-P6: lists all sources with metadata."""
        _populate_graph(graph)
        sources = export_sources("ea-for-ai", graph, output_dir)

        assert len(sources) == 3
        assert all("title" in s for s in sources)
        assert all("url" in s for s in sources)
        assert all("author" in s for s in sources)
        assert all("type" in s for s in sources)

    def test_extract_counts(self, graph, output_dir):
        """AC-P7: includes extract_count per source."""
        _populate_graph(graph)
        sources = export_sources("ea-for-ai", graph, output_dir)

        for s in sources:
            assert s["extract_count"] == 3

    def test_file_written(self, graph, output_dir):
        _populate_graph(graph)
        export_sources("ea-for-ai", graph, output_dir)

        path = os.path.join(output_dir, "ea-for-ai", "sources.json")
        assert os.path.exists(path)
        with open(path) as f:
            data = json.load(f)
        assert data["topic"] == "ea-for-ai"
        assert len(data["sources"]) == 3


class TestExportAll:
    """AC-P8, AC-P9"""

    def test_creates_all_files(self, graph, output_dir):
        """AC-P8: creates topic subdirectories and writes all files."""
        _populate_graph(graph)
        result = export_all(graph, output_dir)

        assert result["topics"] == 2
        assert result["sources"] == 4  # 3 + 1

        assert os.path.exists(os.path.join(output_dir, "topics.json"))
        assert os.path.exists(os.path.join(output_dir, "ea-for-ai", "stats.json"))
        assert os.path.exists(os.path.join(output_dir, "ea-for-ai", "sources.json"))
        assert os.path.exists(os.path.join(output_dir, "ai-pm", "stats.json"))
        assert os.path.exists(os.path.join(output_dir, "ai-pm", "sources.json"))

    def test_all_json_valid(self, graph, output_dir):
        """AC-P9: all exported JSON is valid and parseable."""
        _populate_graph(graph)
        export_all(graph, output_dir)

        for root, dirs, files in os.walk(output_dir):
            for fname in files:
                if fname.endswith(".json"):
                    path = os.path.join(root, fname)
                    with open(path) as f:
                        json.load(f)  # Should not raise
