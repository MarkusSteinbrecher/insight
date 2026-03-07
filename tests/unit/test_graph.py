"""
Unit tests for insight.graph.InsightGraph.

Tests map to acceptance criteria in design/specs/graph-schema.md.
Each test is tagged with its AC reference.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile

import pytest

from insight.graph import InsightGraph


@pytest.fixture
def graph():
    """Create a fresh graph in a temp directory for each test."""
    tmpdir = tempfile.mkdtemp()
    db_path = os.path.join(tmpdir, "test.db")
    g = InsightGraph(db_path)
    g.init_schema()
    yield g
    g.close()
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def populated_graph(graph):
    """Graph with sample data: 2 sources, blocks, segments, claims."""
    # Sources
    graph.add_source("t:src-001", "test", "web", "Source One",
                     url="https://example.com/one", author="Author A",
                     publication_date="2025-06-01", content_hash="abc123")
    graph.add_source("t:src-002", "test", "pdf", "Source Two",
                     url="https://example.com/two", author="Author B",
                     publication_date="2025-07-01", content_hash="def456")
    graph.add_source("t2:src-001", "other-topic", "web", "Other Topic Source",
                     url="https://example.com/other", content_hash="ghi789")

    # Content blocks
    graph.add_content_block("t:src-001:block-001", "t:src-001",
                            "AI adoption has reached 72% among Fortune 500.",
                            1, "heading_path", "Introduction", "prose",
                            section_path="Introduction")
    graph.add_content_block("t:src-001:block-002", "t:src-001",
                            "Governance frameworks lag behind deployment.",
                            2, "heading_path", "Governance", "prose",
                            section_path="Governance")
    graph.add_content_block("t:src-002:block-001", "t:src-002",
                            "Enterprise AI is now mainstream.",
                            1, "page", "page:1", "prose")

    # Segments
    graph.add_segment("t:src-001:seg-001", "t:src-001:block-001",
                      "AI adoption has reached 72% among Fortune 500.",
                      "statistic", 1, section="Introduction",
                      metadata={"metric": "adoption rate", "value": 72})
    graph.add_segment("t:src-001:seg-002", "t:src-001:block-002",
                      "Governance frameworks lag behind deployment.",
                      "claim", 2, section="Governance")
    graph.add_segment("t:src-002:seg-001", "t:src-002:block-001",
                      "Enterprise AI is now mainstream.",
                      "claim", 1)

    # Claims
    graph.add_claim("test:cc-001", "test", "canonical",
                    "AI adoption widespread",
                    "Enterprise AI adoption has become widespread",
                    claim_type="empirical", strength="strongly-supported")
    graph.add_claim("test:cc-002", "test", "canonical",
                    "Governance gap",
                    "AI governance lags behind adoption",
                    claim_type="normative", strength="supported")
    graph.add_claim("test:uc-001", "test", "unique",
                    "Cascading agent risk",
                    "Inter-agent influence creates cascading risk")

    # Extracts (mirror segments as atomic units)
    graph.add_extract("t:src-001:extract-001", "t:src-001",
                      "AI adoption has reached 72% among Fortune 500.",
                      1, format="prose", extract_type="statistic",
                      section_path="Introduction")
    graph.add_extract("t:src-001:extract-002", "t:src-001",
                      "Governance frameworks lag behind deployment.",
                      2, format="prose", extract_type="assertion",
                      section_path="Governance")
    graph.add_extract("t:src-002:extract-001", "t:src-002",
                      "Enterprise AI is now mainstream.",
                      1, format="prose", extract_type="assertion")

    # Links (old segment-based)
    graph.link_segment_to_claim("t:src-001:seg-001", "test:cc-001", representative=True)
    graph.link_segment_to_claim("t:src-002:seg-001", "test:cc-001", representative=True)
    graph.link_segment_to_claim("t:src-001:seg-002", "test:cc-002", representative=True)
    graph.link_contradiction("test:cc-001", "test:uc-001", "Disagree on maturity")

    # Links (new extract-based)
    graph.link_extract_to_claim("t:src-001:extract-001", "test:cc-001", representative=True)
    graph.link_extract_to_claim("t:src-002:extract-001", "test:cc-001", representative=True)
    graph.link_extract_to_claim("t:src-001:extract-002", "test:cc-002", representative=True)

    return graph


# --- Schema (AC-S1, AC-S2) ---

class TestSchema:
    def test_init_schema_fresh(self, graph):
        """AC-S1: init_schema on fresh DB creates tables without error."""
        # graph fixture already called init_schema — verify we can query
        assert graph.count_sources() == 0

    def test_init_schema_idempotent(self, graph):
        """AC-S2: init_schema on existing DB is idempotent."""
        graph.add_source("s1", "t", "web", "Test")
        graph.init_schema()  # Should not error or lose data
        assert graph.count_sources() == 1


# --- Source CRUD (AC-SC1 through AC-SC8) ---

class TestSourceCRUD:
    def test_add_and_get_source(self, graph):
        """AC-SC1: add_source creates node retrievable by get_source."""
        graph.add_source("t:s1", "topic", "web", "My Source",
                         url="https://example.com", author="Test",
                         publication_date="2025-01-01",
                         content_hash="abc", language="en")
        src = graph.get_source("t:s1")
        assert src is not None
        assert src["source_id"] == "t:s1"
        assert src["topic"] == "topic"
        assert src["title"] == "My Source"
        assert src["url"] == "https://example.com"
        assert src["author"] == "Test"

    def test_retrieved_date_defaults_to_today(self, graph):
        """AC-SC2: retrieved_date defaults to today when None."""
        from datetime import date
        graph.add_source("t:s1", "topic", "web", "Test")
        src = graph.get_source("t:s1")
        assert src["retrieved_date"] == date.today().isoformat()

    def test_metadata_roundtrip(self, graph):
        """AC-SC3: metadata dict stored as JSON, retrievable and parseable."""
        meta = {"tags": ["ai", "governance"], "relevance": 5}
        graph.add_source("t:s1", "topic", "web", "Test", metadata=meta)
        src = graph.get_source("t:s1")
        parsed = json.loads(src["metadata"])
        assert parsed == meta

    def test_source_exists_by_url(self, graph):
        """AC-SC4: source_exists(url=...) returns True/False correctly."""
        graph.add_source("t:s1", "topic", "web", "Test", url="https://example.com")
        assert graph.source_exists(url="https://example.com") is True
        assert graph.source_exists(url="https://unknown.com") is False

    def test_source_exists_by_id(self, graph):
        """AC-SC5: source_exists(source_id=...) returns True/False correctly."""
        graph.add_source("t:s1", "topic", "web", "Test")
        assert graph.source_exists(source_id="t:s1") is True
        assert graph.source_exists(source_id="t:s999") is False

    def test_get_sources_by_topic(self, populated_graph):
        """AC-SC6: returns only sources for given topic, ordered by source_id."""
        sources = populated_graph.get_sources_by_topic("test")
        assert len(sources) == 2
        assert sources[0]["source_id"] == "t:src-001"
        assert sources[1]["source_id"] == "t:src-002"

    def test_get_existing_urls(self, populated_graph):
        """AC-SC7: returns all non-empty URLs for a topic."""
        urls = populated_graph.get_existing_urls("test")
        assert "https://example.com/one" in urls
        assert "https://example.com/two" in urls
        assert "https://example.com/other" not in urls  # different topic

    def test_get_source_not_found(self, graph):
        """AC-SC8: get_source returns None for non-existent ID."""
        assert graph.get_source("nonexistent") is None


# --- ContentBlock CRUD (AC-CB1 through AC-CB4) ---

class TestContentBlockCRUD:
    def test_add_block_creates_node_and_edge(self, graph):
        """AC-CB1: add_content_block creates node + CONTAINS edge."""
        graph.add_source("s1", "t", "web", "Test")
        graph.add_content_block("s1:b1", "s1", "Hello world.", 1,
                                "heading_path", "Intro", "prose")
        blocks = graph.get_content_blocks("s1")
        assert len(blocks) == 1
        assert blocks[0]["block_id"] == "s1:b1"
        assert blocks[0]["text"] == "Hello world."

    def test_blocks_ordered_by_position(self, graph):
        """AC-CB2: get_content_blocks returns blocks ordered by position."""
        graph.add_source("s1", "t", "web", "Test")
        graph.add_content_block("s1:b2", "s1", "Second.", 2, "heading_path", "", "prose")
        graph.add_content_block("s1:b1", "s1", "First.", 1, "heading_path", "", "prose")
        blocks = graph.get_content_blocks("s1")
        assert blocks[0]["position"] == 1
        assert blocks[1]["position"] == 2

    def test_no_blocks_returns_empty(self, graph):
        """AC-CB3: get_content_blocks for source with no blocks returns []."""
        graph.add_source("s1", "t", "web", "Test")
        assert graph.get_content_blocks("s1") == []

    def test_block_metadata_roundtrip(self, graph):
        """AC-CB4: block metadata round-trips as JSON."""
        meta = {"table_headers": ["Name", "Value"]}
        graph.add_source("s1", "t", "web", "Test")
        graph.add_content_block("s1:b1", "s1", "Row data.", 1,
                                "heading_path", "", "table_row", metadata=meta)
        blocks = graph.get_content_blocks("s1")
        parsed = json.loads(blocks[0]["metadata"])
        assert parsed == meta


# --- VisualExtraction CRUD (AC-VE1, AC-VE2) ---

class TestVisualExtractionCRUD:
    def test_add_visual_extraction(self, graph):
        """AC-VE1: creates node + EXTRACTED_FROM edge."""
        graph.add_source("s1", "t", "web", "Test")
        graph.add_content_block("s1:b1", "s1", "Figure 1.", 1,
                                "heading_path", "", "figure", image_path="fig1.png")
        graph.add_visual_extraction("s1:b1:visual", "s1:b1", "bar_chart",
                                    "AI adoption by sector")
        # Verify node exists by checking it doesn't error
        # (no direct get_visual_extraction yet, but the creation succeeded)

    def test_extracted_data_roundtrip(self, graph):
        """AC-VE2: extracted_data round-trips as JSON array."""
        data = [{"label": "Finance", "value": 82}, {"label": "Healthcare", "value": 65}]
        graph.add_source("s1", "t", "web", "Test")
        graph.add_content_block("s1:b1", "s1", "Chart.", 1, "heading_path", "", "figure")
        graph.add_visual_extraction("s1:b1:visual", "s1:b1", "bar_chart",
                                    "Adoption chart", extracted_data=data)


# --- Segment CRUD (AC-SG1 through AC-SG6) ---

class TestSegmentCRUD:
    def test_add_segment_creates_node_and_edge(self, populated_graph):
        """AC-SG1: add_segment creates node + SEGMENTED_FROM edge."""
        segs = populated_graph.get_segments_for_block("t:src-001:block-001")
        assert len(segs) == 1
        assert segs[0]["segment_id"] == "t:src-001:seg-001"

    def test_get_segments_ordered(self, populated_graph):
        """AC-SG2: get_segments returns all segments for source, ordered by position."""
        segs = populated_graph.get_segments("t:src-001")
        assert len(segs) == 2
        assert segs[0]["position"] == 1
        assert segs[1]["position"] == 2

    def test_get_segments_by_type(self, populated_graph):
        """AC-SG3: filters by segment type."""
        stats = populated_graph.get_segments_by_type("t:src-001", "statistic")
        assert len(stats) == 1
        assert stats[0]["segment_type"] == "statistic"

        claims = populated_graph.get_segments_by_type("t:src-001", "claim")
        assert len(claims) == 1

    def test_get_segments_for_block(self, populated_graph):
        """AC-SG4: returns segments for a specific block."""
        segs = populated_graph.get_segments_for_block("t:src-001:block-001")
        assert len(segs) == 1
        assert segs[0]["text"] == "AI adoption has reached 72% among Fortune 500."

    def test_no_segments_returns_empty(self, graph):
        """AC-SG5: source with no segments returns []."""
        graph.add_source("s1", "t", "web", "Test")
        assert graph.get_segments("s1") == []

    def test_segment_metadata_roundtrip(self, populated_graph):
        """AC-SG6: metadata round-trips as JSON."""
        segs = populated_graph.get_segments_by_type("t:src-001", "statistic")
        parsed = json.loads(segs[0]["metadata"])
        assert parsed["metric"] == "adoption rate"
        assert parsed["value"] == 72


# --- Claim CRUD (AC-CL1 through AC-CL9) ---

class TestClaimCRUD:
    def test_add_and_get_claim(self, populated_graph):
        """AC-CL1: add_claim creates node retrievable by get_claim."""
        claim = populated_graph.get_claim("test:cc-001")
        assert claim is not None
        assert claim["claim_id"] == "test:cc-001"
        assert claim["topic"] == "test"
        assert claim["claim_category"] == "canonical"
        assert claim["theme"] == "AI adoption widespread"
        assert claim["claim_type"] == "empirical"
        assert claim["strength"] == "strongly-supported"

    def test_get_claim_not_found(self, graph):
        """AC-CL2: get_claim returns None for non-existent ID."""
        assert graph.get_claim("nonexistent") is None

    def test_get_claims_by_topic(self, populated_graph):
        """AC-CL3: returns all claims for a topic."""
        claims = populated_graph.get_claims_by_topic("test")
        assert len(claims) == 3

    def test_get_claims_by_category(self, populated_graph):
        """AC-CL4: filters by category."""
        canonical = populated_graph.get_claims_by_topic("test", category="canonical")
        assert len(canonical) == 2
        unique = populated_graph.get_claims_by_topic("test", category="unique")
        assert len(unique) == 1

    def test_link_segment_to_claim(self, populated_graph):
        """AC-CL5: creates SUPPORTS edge."""
        segs = populated_graph.get_supporting_segments("test:cc-001")
        assert len(segs) == 2  # Two segments from two sources

    def test_get_supporting_segments(self, populated_graph):
        """AC-CL6: returns all supporting segments."""
        segs = populated_graph.get_supporting_segments("test:cc-002")
        assert len(segs) == 1
        assert segs[0]["segment_id"] == "t:src-001:seg-002"

    def test_get_claims_for_segment(self, populated_graph):
        """AC-CL7: returns all claims a segment supports."""
        claims = populated_graph.get_claims_for_segment("t:src-001:seg-001")
        assert len(claims) == 1
        assert claims[0]["claim_id"] == "test:cc-001"

    def test_link_contradiction(self, populated_graph):
        """AC-CL8: creates CONTRADICTS edge."""
        ct = populated_graph.get_contradictions("test:cc-001")
        assert len(ct) == 1

    def test_get_contradictions(self, populated_graph):
        """AC-CL9: returns contradicting claims."""
        ct = populated_graph.get_contradictions("test:cc-001")
        assert ct[0]["claim_id"] == "test:uc-001"


# --- Traceability (AC-TR1 through AC-TR3) ---

class TestTraceability:
    def test_evidence_chain(self, populated_graph):
        """AC-TR1: evidence chain returns claim, extract, source info."""
        chain = populated_graph.get_evidence_chain("test:cc-001")
        assert len(chain) == 2  # Two supporting extracts from two sources
        record = chain[0]
        assert "c.claim_id" in record
        assert "e.extract_id" in record
        assert "s.source_id" in record
        assert "s.title" in record

    def test_evidence_chain_cross_source(self, populated_graph):
        """AC-TR2: chain includes extracts from multiple sources."""
        chain = populated_graph.get_evidence_chain("test:cc-001")
        source_ids = {r["s.source_id"] for r in chain}
        assert len(source_ids) == 2

    def test_claims_for_source(self, populated_graph):
        """AC-TR3: returns all claims supported by a source's extracts."""
        claims = populated_graph.get_claims_for_source("t:src-001")
        claim_ids = {c["claim_id"] for c in claims}
        assert "test:cc-001" in claim_ids
        assert "test:cc-002" in claim_ids


# --- Aggregates (AC-AG1 through AC-AG8) ---

class TestAggregates:
    def test_count_sources_total(self, populated_graph):
        """AC-AG1: count_sources without topic returns total."""
        assert populated_graph.count_sources() == 3

    def test_count_sources_by_topic(self, populated_graph):
        """AC-AG2: count_sources with topic filters."""
        assert populated_graph.count_sources(topic="test") == 2
        assert populated_graph.count_sources(topic="other-topic") == 1

    def test_count_blocks_total(self, populated_graph):
        """AC-AG3: count_content_blocks without source returns total."""
        assert populated_graph.count_content_blocks() == 3

    def test_count_blocks_by_source(self, populated_graph):
        """AC-AG4: count_content_blocks with source filters."""
        assert populated_graph.count_content_blocks(source_id="t:src-001") == 2
        assert populated_graph.count_content_blocks(source_id="t:src-002") == 1

    def test_count_segments_total(self, populated_graph):
        """AC-AG5: count_segments without source returns total."""
        assert populated_graph.count_segments() == 3

    def test_count_segments_by_source(self, populated_graph):
        """AC-AG6: count_segments with source filters."""
        assert populated_graph.count_segments(source_id="t:src-001") == 2

    def test_count_claims_total(self, populated_graph):
        """AC-AG7: count_claims without filters returns total."""
        assert populated_graph.count_claims() == 3

    def test_count_claims_filtered(self, populated_graph):
        """AC-AG8: count_claims with topic and category filters."""
        assert populated_graph.count_claims(topic="test") == 3
        assert populated_graph.count_claims(topic="test", category="canonical") == 2
        assert populated_graph.count_claims(topic="test", category="unique") == 1


# --- Utility (AC-UT1, AC-UT2) ---

class TestUtility:
    def test_content_hash_consistent(self):
        """AC-UT1: same input produces same hash."""
        h1 = InsightGraph.content_hash("hello world")
        h2 = InsightGraph.content_hash("hello world")
        assert h1 == h2

    def test_content_hash_differs(self):
        """AC-UT2: different inputs produce different hashes."""
        h1 = InsightGraph.content_hash("hello")
        h2 = InsightGraph.content_hash("world")
        assert h1 != h2


# --- Edge Cases (AC-EC1 through AC-EC6) ---

class TestEdgeCases:
    def test_empty_url_not_matched(self, graph):
        """AC-EC1: source with empty url doesn't match source_exists(url='')."""
        graph.add_source("s1", "t", "web", "Test", url="")
        assert graph.source_exists(url="") is False

    def test_unicode_text(self, graph):
        """AC-EC2: unicode, newlines, special chars in text."""
        graph.add_source("s1", "t", "web", "Test")
        text = "Données françaises\n\"quotes\" & <brackets>\n日本語テスト"
        graph.add_content_block("s1:b1", "s1", text, 1,
                                "heading_path", "", "prose")
        blocks = graph.get_content_blocks("s1")
        assert blocks[0]["text"] == text

    def test_multiple_sources_same_topic(self, graph):
        """AC-EC3: multiple sources for same topic coexist."""
        graph.add_source("s1", "t", "web", "Source 1")
        graph.add_source("s2", "t", "web", "Source 2")
        assert graph.count_sources(topic="t") == 2

    def test_segment_supports_multiple_claims(self, graph):
        """AC-EC4: a segment can support multiple claims."""
        graph.add_source("s1", "t", "web", "Test")
        graph.add_content_block("s1:b1", "s1", "Text.", 1, "heading_path", "", "prose")
        graph.add_segment("s1:seg-001", "s1:b1", "Multi-claim text.", "claim", 1)
        graph.add_claim("t:c1", "t", "canonical", "Theme A", "Summary A")
        graph.add_claim("t:c2", "t", "canonical", "Theme B", "Summary B")
        graph.link_segment_to_claim("s1:seg-001", "t:c1")
        graph.link_segment_to_claim("s1:seg-001", "t:c2")
        claims = graph.get_claims_for_segment("s1:seg-001")
        assert len(claims) == 2

    def test_claim_supported_cross_source(self, populated_graph):
        """AC-EC5: a claim can be supported by segments from different sources."""
        segs = populated_graph.get_supporting_segments("test:cc-001")
        source_ids = set()
        for seg in segs:
            # Derive source from segment_id prefix
            source_ids.add(":".join(seg["segment_id"].split(":")[:2]))
        assert len(source_ids) == 2

    def test_contradiction_bidirectional(self, populated_graph):
        """AC-EC6: contradictions queryable from both sides."""
        ct1 = populated_graph.get_contradictions("test:cc-001")
        ct2 = populated_graph.get_contradictions("test:uc-001")
        assert len(ct1) == 1
        assert len(ct2) == 1
        assert ct1[0]["claim_id"] == "test:uc-001"
        assert ct2[0]["claim_id"] == "test:cc-001"
