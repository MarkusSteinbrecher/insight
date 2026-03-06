# Component: Analyzer

Parent: [v2 Architecture](v2-architecture.md)
Status: **Design — TODO**

---

## Purpose

All intelligence in the system. Takes content blocks from the graph, segments them, extracts claims, aligns across sources, critiques, synthesizes, and generates insights. Operates incrementally — each operation works against the current graph state.

## Key Responsibilities

- Segmentation: break content blocks into typed segments (claim, statistic, evidence, etc.)
- Claim alignment: match segments across sources, identify consensus, contradictions, unique positions
- Critical analysis: assess claims for strength, novelty, practical value
- Baseline comparison: evaluate claims against common knowledge
- Synthesis: generate narrative documents from graph state
- Interactive refinement: human-in-the-loop discussion and insight tuning

## Topics to Specify

- Operation catalog (each atomic analysis operation)
- Input/output contract per operation (what it reads, what it writes to graph)
- Incremental alignment algorithm
- Claude API prompt design per operation
- Interaction model for human-in-the-loop refinement
- Segment classification taxonomy (carry forward from v1 or revise)
