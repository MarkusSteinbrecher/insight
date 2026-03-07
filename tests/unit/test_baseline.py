"""Tests for insight.collector.baseline — loading, saving, and tracking."""

from __future__ import annotations

import os
import tempfile
import shutil

import pytest

from insight.collector.baseline import (
    load_baseline, save_baseline, baseline_path,
    record_run, add_sources, Baseline, SourceRecord, RunRecord,
)


@pytest.fixture
def baselines_dir():
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)


def _write_baseline(baselines_dir, slug, content):
    path = os.path.join(baselines_dir, f"{slug}.yaml")
    with open(path, "w") as f:
        f.write(content)
    return path


class TestBaselinePath:

    def test_returns_yaml_path(self, baselines_dir):
        path = baseline_path("my-topic", baselines_dir)
        assert path == os.path.join(baselines_dir, "my-topic.yaml")


class TestLoadBaseline:

    def test_loads_valid_baseline(self, baselines_dir):
        _write_baseline(baselines_dir, "test-topic", """
topic: test-topic
title: Test Topic
question: What is this about?
keywords:
  - "keyword one"
  - "keyword two"
youtube_keywords:
  - "yt keyword"
sources: []
runs: []
""")
        bl = load_baseline("test-topic", baselines_dir)
        assert bl.topic == "test-topic"
        assert bl.title == "Test Topic"
        assert bl.question == "What is this about?"
        assert bl.keywords == ["keyword one", "keyword two"]
        assert bl.youtube_keywords == ["yt keyword"]
        assert bl.sources == []
        assert bl.runs == []

    def test_missing_file_raises(self, baselines_dir):
        with pytest.raises(FileNotFoundError):
            load_baseline("nonexistent", baselines_dir)

    def test_empty_file_raises(self, baselines_dir):
        _write_baseline(baselines_dir, "empty", "")
        with pytest.raises(ValueError, match="Invalid baseline"):
            load_baseline("empty", baselines_dir)

    def test_defaults_for_optional_fields(self, baselines_dir):
        _write_baseline(baselines_dir, "minimal", """
topic: minimal
title: Minimal
question: Minimal question?
""")
        bl = load_baseline("minimal", baselines_dir)
        assert bl.keywords == []
        assert bl.youtube_keywords == []
        assert bl.sources == []
        assert bl.runs == []

    def test_topic_defaults_to_slug(self, baselines_dir):
        _write_baseline(baselines_dir, "no-topic-field", """
title: No Topic Field
question: What?
""")
        bl = load_baseline("no-topic-field", baselines_dir)
        assert bl.topic == "no-topic-field"

    def test_loads_sources(self, baselines_dir):
        _write_baseline(baselines_dir, "with-sources", """
topic: with-sources
title: With Sources
question: Test?
sources:
  - url: https://example.com/one
    title: Source One
    source_type: web
    source_id: with-sources:source-001
  - url: https://example.com/two
    title: ""
    source_type: web
    source_id: ""
""")
        bl = load_baseline("with-sources", baselines_dir)
        assert len(bl.sources) == 2
        assert bl.sources[0].url == "https://example.com/one"
        assert bl.sources[0].source_id == "with-sources:source-001"
        assert bl.sources[1].source_id == ""

    def test_loads_runs(self, baselines_dir):
        _write_baseline(baselines_dir, "with-runs", """
topic: with-runs
title: With Runs
question: Test?
runs:
  - date: "2026-03-01"
    keywords_used: ["keyword one"]
    found: 10
    new: 7
    already_collected: 3
""")
        bl = load_baseline("with-runs", baselines_dir)
        assert len(bl.runs) == 1
        assert bl.runs[0].date == "2026-03-01"
        assert bl.runs[0].found == 10
        assert bl.runs[0].new == 7


class TestSaveBaseline:

    def test_roundtrip(self, baselines_dir):
        bl = Baseline(
            topic="roundtrip",
            title="Roundtrip Test",
            question="Does it round-trip?",
            keywords=["kw1", "kw2"],
            youtube_keywords=["yt1"],
            sources=[SourceRecord(url="https://example.com", title="Ex",
                                  source_type="web", source_id="roundtrip:source-001")],
            runs=[RunRecord(date="2026-03-01", keywords_used=["kw1"],
                           found=5, new=3, already_collected=2)],
        )
        save_baseline(bl, baselines_dir)

        loaded = load_baseline("roundtrip", baselines_dir)
        assert loaded.topic == "roundtrip"
        assert loaded.keywords == ["kw1", "kw2"]
        assert len(loaded.sources) == 1
        assert loaded.sources[0].url == "https://example.com"
        assert len(loaded.runs) == 1
        assert loaded.runs[0].new == 3

    def test_creates_directory(self):
        tmpdir = tempfile.mkdtemp()
        nested = os.path.join(tmpdir, "sub", "baselines")
        bl = Baseline(topic="nested", title="T", question="Q?")
        save_baseline(bl, nested)
        assert os.path.isfile(os.path.join(nested, "nested.yaml"))
        shutil.rmtree(tmpdir, ignore_errors=True)


class TestRecordRun:

    def test_appends_run(self):
        bl = Baseline(topic="t", title="T", question="Q?")
        record_run(bl, keywords_used=["kw1"], found=10, new=7, already_collected=3)
        assert len(bl.runs) == 1
        assert bl.runs[0].found == 10
        assert bl.runs[0].new == 7
        assert bl.runs[0].keywords_used == ["kw1"]

    def test_multiple_runs(self):
        bl = Baseline(topic="t", title="T", question="Q?")
        record_run(bl, keywords_used=["a"], found=5, new=5, already_collected=0)
        record_run(bl, keywords_used=["b"], found=8, new=3, already_collected=5)
        assert len(bl.runs) == 2


class TestAddSources:

    def test_adds_new_sources(self):
        bl = Baseline(topic="t", title="T", question="Q?")
        records = [
            SourceRecord(url="https://a.com", title="A", source_type="web", source_id=""),
            SourceRecord(url="https://b.com", title="B", source_type="web", source_id=""),
        ]
        added = add_sources(bl, records)
        assert added == 2
        assert len(bl.sources) == 2

    def test_skips_duplicates(self):
        bl = Baseline(topic="t", title="T", question="Q?",
                      sources=[SourceRecord(url="https://a.com", title="A",
                                            source_type="web", source_id="t:source-001")])
        records = [
            SourceRecord(url="https://a.com", title="A dup", source_type="web", source_id=""),
            SourceRecord(url="https://b.com", title="B", source_type="web", source_id=""),
        ]
        added = add_sources(bl, records)
        assert added == 1
        assert len(bl.sources) == 2
        # Original stays unchanged
        assert bl.sources[0].title == "A"

    def test_deduplicates_pdfs_by_source_id(self):
        bl = Baseline(topic="t", title="T", question="Q?",
                      sources=[SourceRecord(url="", title="PDF One",
                                            source_type="pdf", source_id="t:source-001")])
        records = [
            SourceRecord(url="", title="PDF One dup", source_type="pdf", source_id="t:source-001"),
            SourceRecord(url="", title="PDF Two", source_type="pdf", source_id="t:source-002"),
        ]
        added = add_sources(bl, records)
        assert added == 1
        assert len(bl.sources) == 2
        assert bl.sources[1].title == "PDF Two"

    def test_source_urls_excludes_empty(self):
        bl = Baseline(topic="t", title="T", question="Q?",
                      sources=[
                          SourceRecord(url="https://a.com", title="", source_type="web", source_id=""),
                          SourceRecord(url="", title="PDF", source_type="pdf", source_id="t:source-001"),
                      ])
        assert bl.source_urls == {"https://a.com"}

    def test_source_ids_property(self):
        bl = Baseline(topic="t", title="T", question="Q?",
                      sources=[
                          SourceRecord(url="", title="PDF", source_type="pdf", source_id="t:source-001"),
                          SourceRecord(url="https://a.com", title="Web", source_type="web", source_id=""),
                      ])
        assert bl.source_ids == {"t:source-001"}
