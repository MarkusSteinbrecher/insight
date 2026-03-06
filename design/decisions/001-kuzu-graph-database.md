# ADR-001: Use KuzuDB as Embedded Graph Database

**Date:** 2026-03-06
**Status:** Accepted

## Context

Insight v2 needs a graph database to store the knowledge graph (sources, claims, findings, relationships). Requirements: embedded (no server), Python bindings, graph-native queries, local-only is fine (site reads exported JSON).

## Options Considered

1. **SQLite + graph schema** — Proven, zero dependencies. But graph traversal requires recursive CTEs — workable but not ergonomic for multi-hop queries.
2. **KuzuDB** — Embedded graph database with Cypher queries. Python bindings, local files, purpose-built for graph workloads.
3. **DuckDB** — Fast analytical database with WASM build. Same graph traversal limitations as SQLite.
4. **NetworkX** — In-memory Python graph. No persistence beyond serialization. No query language.
5. **Neo4j** — Full graph database. Requires running a server — overkill for this project.

## Decision

Use **KuzuDB**. It's embedded like SQLite, supports Cypher natively, and is purpose-built for the graph queries we need (evidence chains, contradiction detection, concept traversal).

## Consequences

- `pip install kuzu` adds a dependency (~4MB wheel)
- Cypher queries are natural for our traversal patterns
- No browser-side querying — site reads exported JSON (acceptable)
- Younger project than SQLite — smaller community, potential API changes
- Schema migrations need manual handling (no built-in migration tool)
