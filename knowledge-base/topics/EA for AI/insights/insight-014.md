---
title: "Reference Architecture Proliferation: Competing Layered Models Converge on Common Structural Principles"
type: evidence
confidence: medium
sources:
  - source-005
  - source-004
  - source-001
  - source-011
  - source-012
tags:
  - reference-architecture
  - layered-architecture
  - composability
  - modularity
  - enterprise-architecture
  - interoperability
created: 2026-02-14
---

## Insight

Across the full source set, at least four distinct layered reference architectures for enterprise AI have been proposed, yet a careful cross-source comparison reveals that these competing models converge on a remarkably consistent set of structural principles despite differing in layer counts, terminology, and emphasis. Source-001 (Kumar) proposes an 8-layer composable agentic architecture. Source-005 (Salesforce) presents an 11-layer reference architecture spanning Experience through Security. Source-011 (Ipung) integrates three frameworks (TOGAF, BADIR, INSIGHT) into a multi-layer decision pipeline. Source-012 (Wairagade & Govindarajan) evaluates SOA, EDA, and Microservices as architectural patterns for AI integration. Even source-004 (Mohan), while not proposing a formal layered model, describes six architectural imperatives (modular architecture, governance, data-centric platforms, multi-model orchestration, zero-trust security, resilience) that map directly onto the layers proposed by others.

The convergent structural principles across these competing models are: (1) a semantic or data foundation layer that makes enterprise data AI-accessible; (2) an orchestration layer that coordinates AI models, agents, or services; (3) an observability and governance layer providing visibility into AI system behaviour; (4) a security layer with zero-trust principles applied to AI-specific risks; and (5) a composability requirement where components are loosely coupled and independently replaceable. Source-004's litmus test -- "can your primary LLM provider be swapped within eight hours?" -- captures the composability principle concisely. Source-005's emphasis on open standards (MCP, A2A) and source-001's A2A communication protocols both point to interoperability as the mechanism for achieving composability.

This convergence is significant because it suggests the field is moving toward a de facto consensus on architectural structure even as formal framework standardisation remains incomplete. The variation in layer counts (8 vs 11 vs multi-framework synthesis) reflects different levels of granularity and scope rather than fundamental disagreements about what an enterprise AI architecture must contain. The pattern is analogous to how cloud reference architectures evolved from competing models (AWS, Azure, GCP each with different layer definitions) toward broadly shared principles (compute, storage, networking, security, management) that transcend vendor-specific implementations.

## Supporting Evidence

- 8-layer composable agentic architecture with A2A communication protocols (source-001)
- 11-layer reference architecture: Experience, Agentic, AI/ML, Enterprise Orchestration, Application Services, Semantic, Data, Infrastructure, Integration, IT Operations & Observability, Security (source-005)
- Six architectural imperatives: modular architecture, governance, data-centric platforms, multi-model orchestration, zero-trust security, resilience (source-004)
- Multi-framework synthesis (TOGAF + BADIR + INSIGHT) for translating business capabilities to decisions through data architecture (source-011)
- Three EA patterns evaluated for AI integration: SOA, EDA, Microservices (source-012)
- Open standards (MCP, A2A) positioned as essential for avoiding vendor lock-in (source-005)
- "Every component of your AI stack should be replaceable without cascading changes" (source-004)
- LLM swap litmus test: can the primary provider be swapped within 8 hours? (source-004)
- Design principles: composability, data/semantic-first, embedded observability, trust throughout, agent-first with human oversight (source-005)
- Convergent layers across models: data/semantic foundation, orchestration, observability/governance, security, composability

## Evidence Assessment

The convergence finding is analytically derived from cross-source comparison rather than empirically measured, so it reflects the analyst's synthesis rather than primary evidence. This is appropriate for a pattern-identification insight but should be stated transparently. The individual reference architectures vary in evidence quality: source-005 (Salesforce) is a vendor-produced document designed to support product positioning; source-001 (Kumar) is a single-author academic paper with limited empirical validation; source-011 (Ipung) is a peer-reviewed but primarily conceptual framework; source-012 (Wairagade & Govindarajan) evaluates patterns but does not provide production deployment data. The strongest evidence for the convergence claim comes from the independence of the sources -- a vendor (Salesforce), an academic (Kumar), IEEE researchers (Ipung, Wairagade & Govindarajan), and a practitioner (Mohan) arriving at similar structural conclusions through different methodologies and with different commercial motivations. The composability principle is the most widely shared (appearing in 4 of 5 sources), suggesting it is the most robust finding. The specific layer counts and boundaries remain fluid, indicating the field has not yet settled on canonical terminology or decomposition.

## Implications

Enterprise architects designing AI-capable architectures should focus on the convergent structural principles rather than adopting any single vendor's or academic's layered model wholesale. The five consistent principles identified -- semantic data foundation, orchestration, observability and governance, security, and composability -- should serve as architectural requirements regardless of which specific reference model an organisation follows. The composability requirement deserves particular emphasis: source-004's "8-hour swap test" provides a practical, measurable criterion for architectural resilience that can be incorporated into design reviews and architectural fitness functions. Organisations should also invest in emerging open standards (MCP, A2A) as source-005 recommends, to ensure their architectural choices remain interoperable as the field consolidates. For thought leadership, the convergence finding is valuable because it allows authors to transcend the "which framework is best" debate and instead articulate the shared principles that any sound enterprise AI architecture must embody -- a more durable and vendor-neutral contribution than advocating for any single model.
