# Component: Knowledge Graph

Parent: [v2 Architecture](v2-architecture.md)
Status: **Design — TODO**

---

## Purpose

Central data store backed by KuzuDB. All components read from and write to the graph. Provides a Python interface for CRUD operations, traversal queries, and JSON export.

## Key Responsibilities

- Define and enforce the schema (node types, edge types, constraints)
- Provide a Python API for all graph operations
- Export graph data as JSON for the Presenter
- Support schema versioning and migrations
- Migrate v1 YAML data into the graph

## Topics to Specify

- Complete node type catalog with properties and constraints
- Complete edge type catalog with cardinality rules
- Cypher query patterns for common operations (evidence chains, contradictions, concept clusters)
- Python module interface (`insight.graph`)
- Schema versioning strategy
- JSON export format and queries
- v1-to-v2 data migration mapping
