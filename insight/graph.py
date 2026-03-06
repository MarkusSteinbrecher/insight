"""
Knowledge graph interface backed by KuzuDB.

Manages schema creation, CRUD operations, and common queries
for the Insight research knowledge graph.
"""

from __future__ import annotations

import kuzu
import os
import hashlib
import json
from pathlib import Path
from datetime import date, datetime

# Default database location
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "insight.db")


class InsightGraph:
    """Interface to the Insight knowledge graph."""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.db = kuzu.Database(self.db_path)
        self.conn = kuzu.Connection(self.db)

    def init_schema(self):
        """Create node and edge tables if they don't exist."""

        # --- Node tables ---

        self.conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS Source (
                source_id STRING,
                topic STRING,
                source_type STRING,
                url STRING,
                title STRING,
                author STRING,
                publication_date STRING,
                retrieved_date STRING,
                content_hash STRING,
                language STRING DEFAULT 'en',
                metadata STRING DEFAULT '{}',
                PRIMARY KEY (source_id)
            )
        """)

        self.conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS ContentBlock (
                block_id STRING,
                text STRING,
                position INT64,
                location_type STRING,
                location_value STRING,
                format STRING,
                section_path STRING DEFAULT '',
                image_path STRING DEFAULT '',
                metadata STRING DEFAULT '{}',
                PRIMARY KEY (block_id)
            )
        """)

        self.conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS VisualExtraction (
                extraction_id STRING,
                visual_type STRING,
                visual_description STRING,
                extracted_data STRING DEFAULT '[]',
                extraction_method STRING DEFAULT 'claude-vision',
                metadata STRING DEFAULT '{}',
                PRIMARY KEY (extraction_id)
            )
        """)

        # --- Edge tables ---

        self.conn.execute("""
            CREATE REL TABLE IF NOT EXISTS CONTAINS (
                FROM Source TO ContentBlock,
                position INT64
            )
        """)

        self.conn.execute("""
            CREATE REL TABLE IF NOT EXISTS EXTRACTED_FROM (
                FROM VisualExtraction TO ContentBlock
            )
        """)

        # --- Analyzer node tables (MVP) ---

        self.conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS Segment (
                segment_id STRING,
                text STRING,
                segment_type STRING,
                section STRING DEFAULT '',
                position INT64,
                source_format STRING DEFAULT 'prose',
                metadata STRING DEFAULT '{}',
                PRIMARY KEY (segment_id)
            )
        """)

        self.conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS Claim (
                claim_id STRING,
                topic STRING,
                claim_category STRING,
                theme STRING,
                summary STRING,
                claim_type STRING DEFAULT '',
                strength STRING DEFAULT '',
                claim_description STRING DEFAULT '',
                metadata STRING DEFAULT '{}',
                PRIMARY KEY (claim_id)
            )
        """)

        # --- Analyzer edge tables (MVP) ---

        self.conn.execute("""
            CREATE REL TABLE IF NOT EXISTS SEGMENTED_FROM (
                FROM Segment TO ContentBlock
            )
        """)

        self.conn.execute("""
            CREATE REL TABLE IF NOT EXISTS SUPPORTS (
                FROM Segment TO Claim,
                representative BOOLEAN DEFAULT FALSE
            )
        """)

        self.conn.execute("""
            CREATE REL TABLE IF NOT EXISTS CONTRADICTS (
                FROM Claim TO Claim,
                claim_description STRING DEFAULT ''
            )
        """)

    def close(self):
        """Close the database connection."""
        # KuzuDB handles cleanup on garbage collection,
        # but explicit close is good practice
        self.conn = None
        self.db = None

    # --- Source operations ---

    def add_source(self, source_id: str, topic: str, source_type: str,
                   title: str, url: str = "", author: str = "",
                   publication_date: str = "", retrieved_date: str = None,
                   content_hash: str = "", language: str = "en",
                   metadata: dict = None) -> str:
        """Add a source node to the graph. Returns source_id."""
        if retrieved_date is None:
            retrieved_date = date.today().isoformat()
        meta_json = json.dumps(metadata or {})
        self.conn.execute(
            """
            CREATE (s:Source {
                source_id: $sid, topic: $topic, source_type: $stype,
                url: $url, title: $title, author: $author,
                publication_date: $pdate, retrieved_date: $rdate,
                content_hash: $chash, language: $lang, metadata: $meta
            })
            """,
            parameters={
                "sid": source_id, "topic": topic, "stype": source_type,
                "url": url, "title": title, "author": author,
                "pdate": publication_date, "rdate": retrieved_date,
                "chash": content_hash, "lang": language, "meta": meta_json,
            }
        )
        return source_id

    def source_exists(self, url: str = None, source_id: str = None) -> bool:
        """Check if a source already exists by URL or source_id."""
        if source_id:
            result = self.conn.execute(
                "MATCH (s:Source) WHERE s.source_id = $sid RETURN s.source_id",
                parameters={"sid": source_id}
            )
            return result.has_next()
        if url:
            result = self.conn.execute(
                "MATCH (s:Source) WHERE s.url = $url RETURN s.source_id",
                parameters={"url": url}
            )
            return result.has_next()
        return False

    def get_source(self, source_id: str) -> dict | None:
        """Get a source by ID. Returns dict or None."""
        result = self.conn.execute(
            "MATCH (s:Source) WHERE s.source_id = $sid RETURN s.*",
            parameters={"sid": source_id}
        )
        if result.has_next():
            row = result.get_next()
            columns = result.get_column_names()
            return {col.replace("s.", ""): val for col, val in zip(columns, row)}
        return None

    def get_sources_by_topic(self, topic: str) -> list[dict]:
        """Get all sources for a topic."""
        result = self.conn.execute(
            "MATCH (s:Source) WHERE s.topic = $topic RETURN s.* ORDER BY s.source_id",
            parameters={"topic": topic}
        )
        sources = []
        columns = result.get_column_names()
        while result.has_next():
            row = result.get_next()
            sources.append({col.replace("s.", ""): val for col, val in zip(columns, row)})
        return sources

    def get_existing_urls(self, topic: str) -> set[str]:
        """Get all URLs already collected for a topic."""
        result = self.conn.execute(
            "MATCH (s:Source) WHERE s.topic = $topic AND s.url <> '' RETURN s.url",
            parameters={"topic": topic}
        )
        urls = set()
        while result.has_next():
            urls.add(result.get_next()[0])
        return urls

    # --- ContentBlock operations ---

    def add_content_block(self, block_id: str, source_id: str, text: str,
                          position: int, location_type: str,
                          location_value: str, format: str,
                          section_path: str = "", image_path: str = "",
                          metadata: dict = None) -> str:
        """Add a content block and link it to its source. Returns block_id."""
        meta_json = json.dumps(metadata or {})
        self.conn.execute(
            """
            CREATE (b:ContentBlock {
                block_id: $bid, text: $text, position: $pos,
                location_type: $ltype, location_value: $lval,
                format: $fmt, section_path: $spath,
                image_path: $ipath, metadata: $meta
            })
            """,
            parameters={
                "bid": block_id, "text": text, "pos": position,
                "ltype": location_type, "lval": location_value,
                "fmt": format, "spath": section_path,
                "ipath": image_path, "meta": meta_json,
            }
        )
        # Create CONTAINS edge
        self.conn.execute(
            """
            MATCH (s:Source), (b:ContentBlock)
            WHERE s.source_id = $sid AND b.block_id = $bid
            CREATE (s)-[:CONTAINS {position: $pos}]->(b)
            """,
            parameters={"sid": source_id, "bid": block_id, "pos": position}
        )
        return block_id

    def get_content_blocks(self, source_id: str) -> list[dict]:
        """Get all content blocks for a source, ordered by position."""
        result = self.conn.execute(
            """
            MATCH (s:Source)-[:CONTAINS]->(b:ContentBlock)
            WHERE s.source_id = $sid
            RETURN b.*
            ORDER BY b.position
            """,
            parameters={"sid": source_id}
        )
        blocks = []
        columns = result.get_column_names()
        while result.has_next():
            row = result.get_next()
            blocks.append({col.replace("b.", ""): val for col, val in zip(columns, row)})
        return blocks

    # --- Visual Extraction operations ---

    def add_visual_extraction(self, extraction_id: str, block_id: str,
                              visual_type: str, description: str,
                              extracted_data: list = None,
                              extraction_method: str = "claude-vision",
                              metadata: dict = None) -> str:
        """Add a visual extraction linked to a content block."""
        data_json = json.dumps(extracted_data or [])
        meta_json = json.dumps(metadata or {})
        self.conn.execute(
            """
            CREATE (v:VisualExtraction {
                extraction_id: $eid, visual_type: $vtype,
                visual_description: $vdesc, extracted_data: $data,
                extraction_method: $method, metadata: $meta
            })
            """,
            parameters={
                "eid": extraction_id, "vtype": visual_type,
                "vdesc": description, "data": data_json,
                "method": extraction_method, "meta": meta_json,
            }
        )
        self.conn.execute(
            """
            MATCH (v:VisualExtraction), (b:ContentBlock)
            WHERE v.extraction_id = $eid AND b.block_id = $bid
            CREATE (v)-[:EXTRACTED_FROM]->(b)
            """,
            parameters={"eid": extraction_id, "bid": block_id}
        )
        return extraction_id

    # --- Segment operations ---

    def add_segment(self, segment_id: str, block_id: str, text: str,
                    segment_type: str, position: int,
                    section: str = "", source_format: str = "prose",
                    metadata: dict = None) -> str:
        """Add a segment and link it to its content block. Returns segment_id."""
        meta_json = json.dumps(metadata or {})
        self.conn.execute(
            """
            CREATE (sg:Segment {
                segment_id: $sgid, text: $text, segment_type: $stype,
                section: $section, position: $pos,
                source_format: $sfmt, metadata: $meta
            })
            """,
            parameters={
                "sgid": segment_id, "text": text, "stype": segment_type,
                "section": section, "pos": position,
                "sfmt": source_format, "meta": meta_json,
            }
        )
        self.conn.execute(
            """
            MATCH (sg:Segment), (b:ContentBlock)
            WHERE sg.segment_id = $sgid AND b.block_id = $bid
            CREATE (sg)-[:SEGMENTED_FROM]->(b)
            """,
            parameters={"sgid": segment_id, "bid": block_id}
        )
        return segment_id

    def get_segments(self, source_id: str) -> list[dict]:
        """Get all segments for a source, ordered by position."""
        result = self.conn.execute(
            """
            MATCH (s:Source)-[:CONTAINS]->(b:ContentBlock)<-[:SEGMENTED_FROM]-(sg:Segment)
            WHERE s.source_id = $sid
            RETURN sg.*
            ORDER BY sg.position
            """,
            parameters={"sid": source_id}
        )
        return self._collect_rows(result, "sg.")

    def get_segments_by_type(self, source_id: str, segment_type: str) -> list[dict]:
        """Get segments of a specific type for a source."""
        result = self.conn.execute(
            """
            MATCH (s:Source)-[:CONTAINS]->(b:ContentBlock)<-[:SEGMENTED_FROM]-(sg:Segment)
            WHERE s.source_id = $sid AND sg.segment_type = $stype
            RETURN sg.*
            ORDER BY sg.position
            """,
            parameters={"sid": source_id, "stype": segment_type}
        )
        return self._collect_rows(result, "sg.")

    def get_segments_for_block(self, block_id: str) -> list[dict]:
        """Get all segments extracted from a content block."""
        result = self.conn.execute(
            """
            MATCH (sg:Segment)-[:SEGMENTED_FROM]->(b:ContentBlock)
            WHERE b.block_id = $bid
            RETURN sg.*
            ORDER BY sg.position
            """,
            parameters={"bid": block_id}
        )
        return self._collect_rows(result, "sg.")

    # --- Claim operations ---

    def add_claim(self, claim_id: str, topic: str, claim_category: str,
                  theme: str, summary: str, claim_type: str = "",
                  strength: str = "", description: str = "",
                  metadata: dict = None) -> str:
        """Add a claim node. Returns claim_id."""
        meta_json = json.dumps(metadata or {})
        self.conn.execute(
            """
            CREATE (c:Claim {
                claim_id: $cid, topic: $topic, claim_category: $cat,
                theme: $theme, summary: $summary, claim_type: $ctype,
                strength: $strength, claim_description: $cdesc, metadata: $meta
            })
            """,
            parameters={
                "cid": claim_id, "topic": topic, "cat": claim_category,
                "theme": theme, "summary": summary, "ctype": claim_type,
                "strength": strength, "cdesc": description, "meta": meta_json,
            }
        )
        return claim_id

    def get_claim(self, claim_id: str) -> dict | None:
        """Get a claim by ID. Returns dict or None."""
        result = self.conn.execute(
            "MATCH (c:Claim) WHERE c.claim_id = $cid RETURN c.*",
            parameters={"cid": claim_id}
        )
        if result.has_next():
            row = result.get_next()
            columns = result.get_column_names()
            return {col.replace("c.", ""): val for col, val in zip(columns, row)}
        return None

    def get_claims_by_topic(self, topic: str, category: str = None) -> list[dict]:
        """Get claims for a topic, optionally filtered by category."""
        if category:
            result = self.conn.execute(
                """
                MATCH (c:Claim) WHERE c.topic = $topic AND c.claim_category = $cat
                RETURN c.* ORDER BY c.claim_id
                """,
                parameters={"topic": topic, "cat": category}
            )
        else:
            result = self.conn.execute(
                "MATCH (c:Claim) WHERE c.topic = $topic RETURN c.* ORDER BY c.claim_id",
                parameters={"topic": topic}
            )
        return self._collect_rows(result, "c.")

    def link_segment_to_claim(self, segment_id: str, claim_id: str,
                              representative: bool = False) -> None:
        """Create a SUPPORTS edge from a segment to a claim."""
        self.conn.execute(
            """
            MATCH (sg:Segment), (c:Claim)
            WHERE sg.segment_id = $sgid AND c.claim_id = $cid
            CREATE (sg)-[:SUPPORTS {representative: $rep}]->(c)
            """,
            parameters={"sgid": segment_id, "cid": claim_id, "rep": representative}
        )

    def get_supporting_segments(self, claim_id: str) -> list[dict]:
        """Get all segments that support a claim."""
        result = self.conn.execute(
            """
            MATCH (sg:Segment)-[:SUPPORTS]->(c:Claim)
            WHERE c.claim_id = $cid
            RETURN sg.*
            ORDER BY sg.segment_id
            """,
            parameters={"cid": claim_id}
        )
        return self._collect_rows(result, "sg.")

    def get_claims_for_segment(self, segment_id: str) -> list[dict]:
        """Get all claims that a segment supports."""
        result = self.conn.execute(
            """
            MATCH (sg:Segment)-[:SUPPORTS]->(c:Claim)
            WHERE sg.segment_id = $sgid
            RETURN c.*
            ORDER BY c.claim_id
            """,
            parameters={"sgid": segment_id}
        )
        return self._collect_rows(result, "c.")

    def link_contradiction(self, claim_id_1: str, claim_id_2: str,
                           description: str = "") -> None:
        """Create a CONTRADICTS edge between two claims."""
        self.conn.execute(
            """
            MATCH (c1:Claim), (c2:Claim)
            WHERE c1.claim_id = $cid1 AND c2.claim_id = $cid2
            CREATE (c1)-[:CONTRADICTS {claim_description: $cdesc}]->(c2)
            """,
            parameters={"cid1": claim_id_1, "cid2": claim_id_2, "cdesc": description}
        )

    def get_contradictions(self, claim_id: str) -> list[dict]:
        """Get claims that contradict the given claim (both directions)."""
        result = self.conn.execute(
            """
            MATCH (c1:Claim)-[:CONTRADICTS]-(c2:Claim)
            WHERE c1.claim_id = $cid
            RETURN c2.*
            ORDER BY c2.claim_id
            """,
            parameters={"cid": claim_id}
        )
        return self._collect_rows(result, "c2.")

    # --- Traceability queries ---

    def get_evidence_chain(self, claim_id: str) -> list[dict]:
        """Get the full evidence chain for a claim: claim → segments → blocks → sources."""
        result = self.conn.execute(
            """
            MATCH (sg:Segment)-[:SUPPORTS]->(c:Claim),
                  (sg)-[:SEGMENTED_FROM]->(b:ContentBlock),
                  (s:Source)-[:CONTAINS]->(b)
            WHERE c.claim_id = $cid
            RETURN c.claim_id, c.summary, sg.segment_id, sg.text, sg.segment_type,
                   b.block_id, b.section_path, b.location_value,
                   s.source_id, s.title, s.author, s.url
            ORDER BY s.source_id, sg.position
            """,
            parameters={"cid": claim_id}
        )
        chain = []
        columns = result.get_column_names()
        while result.has_next():
            row = result.get_next()
            chain.append(dict(zip(columns, row)))
        return chain

    def get_claims_for_source(self, source_id: str) -> list[dict]:
        """Get all claims supported by segments from a source."""
        # Two-step: get claim IDs via traversal, then fetch full claims
        result = self.conn.execute(
            """
            MATCH (s:Source)-[:CONTAINS]->(b:ContentBlock)<-[:SEGMENTED_FROM]-(sg:Segment),
                  (sg)-[:SUPPORTS]->(c:Claim)
            WHERE s.source_id = $sid
            RETURN DISTINCT c.claim_id
            ORDER BY c.claim_id
            """,
            parameters={"sid": source_id}
        )
        claim_ids = []
        while result.has_next():
            claim_ids.append(result.get_next()[0])
        return [self.get_claim(cid) for cid in claim_ids]

    # --- Stats ---

    def count_sources(self, topic: str = None) -> int:
        """Count sources, optionally filtered by topic."""
        if topic:
            result = self.conn.execute(
                "MATCH (s:Source) WHERE s.topic = $topic RETURN count(s)",
                parameters={"topic": topic}
            )
        else:
            result = self.conn.execute("MATCH (s:Source) RETURN count(s)")
        return result.get_next()[0]

    def count_content_blocks(self, source_id: str = None) -> int:
        """Count content blocks, optionally filtered by source."""
        if source_id:
            result = self.conn.execute(
                """
                MATCH (s:Source)-[:CONTAINS]->(b:ContentBlock)
                WHERE s.source_id = $sid
                RETURN count(b)
                """,
                parameters={"sid": source_id}
            )
        else:
            result = self.conn.execute("MATCH (b:ContentBlock) RETURN count(b)")
        return result.get_next()[0]

    def count_segments(self, source_id: str = None) -> int:
        """Count segments, optionally filtered by source."""
        if source_id:
            result = self.conn.execute(
                """
                MATCH (s:Source)-[:CONTAINS]->(b:ContentBlock)<-[:SEGMENTED_FROM]-(sg:Segment)
                WHERE s.source_id = $sid
                RETURN count(sg)
                """,
                parameters={"sid": source_id}
            )
        else:
            result = self.conn.execute("MATCH (sg:Segment) RETURN count(sg)")
        return result.get_next()[0]

    def count_claims(self, topic: str = None, category: str = None) -> int:
        """Count claims, optionally filtered by topic and/or category."""
        conditions = []
        params = {}
        if topic:
            conditions.append("c.topic = $topic")
            params["topic"] = topic
        if category:
            conditions.append("c.claim_category = $cat")
            params["cat"] = category
        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        result = self.conn.execute(
            f"MATCH (c:Claim){where} RETURN count(c)",
            parameters=params
        )
        return result.get_next()[0]

    # --- Utility ---

    def _collect_rows(self, result, prefix: str) -> list[dict]:
        """Collect query result rows into list of dicts, stripping column prefix."""
        rows = []
        columns = result.get_column_names()
        while result.has_next():
            row = result.get_next()
            rows.append({col.replace(prefix, ""): val for col, val in zip(columns, row)})
        return rows

    @staticmethod
    def content_hash(text: str) -> str:
        """Generate SHA-256 hash of text content."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
