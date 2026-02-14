---
title: "The TOGAF Adaptation Spectrum: From Rejection to Extension, a Field Without Consensus"
type: contradiction
confidence: high
sources:
  - source-001
  - source-006
  - source-007
  - source-010
  - source-011
  - source-012
tags:
  - TOGAF
  - framework-evolution
  - enterprise-architecture
  - governance
  - ADM
created: 2026-02-14
---

## Insight

Existing insight-007 identified the "TOGAF divide" between replacement and extension camps based on the three PDF sources. The web sources (004-012) dramatically expand and complicate this picture, revealing not a binary divide but a full spectrum of positions -- from outright rejection to deep integration -- that the field has not reconciled. This contradiction is now the most extensively documented tension in the dataset, with at least six sources taking distinct positions.

At one pole, Kumar (source-001) explicitly rejects TOGAF as insufficient for agentic AI, arguing it cannot accommodate "continuous learning cycles, distributed agentic behaviors, and dynamic performance characteristics." At the other pole, Fitriani et al. (source-010) propose expanding TOGAF's domains to explicitly incorporate AI capabilities across all layers, treating the framework as fundamentally sound but incomplete. Between these extremes, source-006 (Stender) cites University of Melbourne research proposing specific TOGAF modifications -- iterative ADM feedback loops, AI lifecycle artifacts, drift detection, explainability modules -- suggesting targeted surgery rather than wholesale replacement. Source-007 (Krause) maps AI capabilities directly onto TOGAF ADM phases (process mining for Phases B-C, compliance monitoring for Phase G, change management for Phase H), treating TOGAF as the organizing scaffold for AI integration. Source-011 (Ipung) takes a synthesis approach, integrating TOGAF with BADIR and INSIGHT frameworks to create a hybrid methodology. Source-012 (Wairagade & Govindarajan) evaluates established architectural patterns (SOA, EDA, Microservices) for AI adoption, operating within the spirit of traditional EA without being TOGAF-specific.

The contradiction deepens when examining what each position actually advocates. The "extend TOGAF" sources (006, 007, 010) agree that TOGAF needs modification but propose very different modifications: Melbourne's research adds AI lifecycle artifacts and drift detection; Krause maps AI onto existing ADM phases; Fitriani et al. expand the domain model itself. These are not complementary proposals -- they represent different theories about where TOGAF's gaps lie. Meanwhile, Kumar's replacement framework and Ipung's multi-framework synthesis both implicitly argue that no amount of TOGAF modification is sufficient on its own.

What no source provides is empirical evidence that any approach -- replacement, extension, or synthesis -- has been validated at enterprise scale. The debate remains entirely theoretical and prescriptive. This is a field arguing about maps while the territory remains unexplored.

## Evidence

- Kumar (source-001): TOGAF and ITIL are "insufficient" -- proposes entirely new 8-layer composable framework
- Stender/Melbourne (source-006): Proposes specific TOGAF modifications -- iterative ADM loops, AI lifecycle artifacts, drift detection, explainability modules
- Krause (source-007): Maps AI onto TOGAF ADM phases -- process mining (B-C), compliance monitoring (G), change management (H)
- Fitriani et al. (source-010): Expands TOGAF domains to explicitly incorporate AI capabilities across all EA layers
- Ipung (source-011): Integrates TOGAF with BADIR and INSIGHT into novel NAEF framework, implying TOGAF alone is insufficient
- Wairagade & Govindarajan (source-012): Evaluates SOA/EDA/Microservices for AI adoption without relying on TOGAF specifically
- Salesforce (source-005): Proposes 11-layer reference architecture that does not reference TOGAF, building from agent-first principles
- No source provides empirical evidence comparing outcomes of TOGAF replacement vs. extension in real enterprise AI implementations

## Significance

This is the central methodological question for the EA for AI field: should organizations work within their existing TOGAF-based governance and extend it for AI, or should they adopt fundamentally new architectural frameworks? The answer has enormous practical consequences -- for training and certification, tooling ecosystems, governance processes, and organizational change management. The fact that six sources across academic papers, practitioner articles, and vendor reports take six distinguishable positions on this question reveals a field without methodological consensus. For thought leadership, this creates an opportunity to propose a pragmatic resolution: perhaps the answer depends on organizational maturity, with TOGAF extension suitable for organizations beginning their AI journey and more radical approaches needed for AI-native transformation at scale. But this hypothesis itself lacks empirical validation.

## Questions to Explore

- Has any organization documented a comparative analysis of TOGAF-extended vs. TOGAF-replaced approaches to AI architecture?
- Is The Open Group (TOGAF's custodian) actively developing AI-specific extensions, and if so, do they align with any of the proposals in the academic literature?
- Could a "TOGAF compatibility layer" be defined that allows organizations to map between TOGAF and newer agentic frameworks, easing transition?
- What percentage of enterprises currently using TOGAF are attempting AI-specific adaptations, and what do those adaptations look like in practice?
- Does the TOGAF debate distract from the more fundamental question of whether any top-down EA framework can keep pace with the rate of AI evolution?
