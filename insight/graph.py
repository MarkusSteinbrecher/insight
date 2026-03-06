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
                description STRING,
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
                description: $desc, extracted_data: $data,
                extraction_method: $method, metadata: $meta
            })
            """,
            parameters={
                "eid": extraction_id, "vtype": visual_type,
                "desc": description, "data": data_json,
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

    # --- Utility ---

    @staticmethod
    def content_hash(text: str) -> str:
        """Generate SHA-256 hash of text content."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
