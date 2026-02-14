---
title: "The Agentic Enterprise - The IT Architecture for the AI-Powered Future"
url: "https://architect.salesforce.com/fundamentals/agentic-enterprise-it-architecture"
author: "Salesforce (Agentforce)"
date: "2024"
type: report
relevance: 5
tags:
  - agentic-ai
  - enterprise-architecture
  - reference-architecture
  - knowledge-graphs
  - agent-orchestration
  - zero-trust
  - composable-architecture
---

## Key Takeaways

- Traditional enterprise IT architecture cannot support widespread AI agent deployment due to information silos, manual work dependencies, and misaligned organizational incentives
- Proposes a comprehensive 11-layer reference architecture for the "Agentic Enterprise"
- Four-level maturity model: Information Retrieval → Simple Single-Domain Orchestration → Multi-Domain Orchestration → Multi-Agent Enterprise Orchestration
- Enterprise Knowledge Graphs are positioned as critical for providing unified semantic understanding across domains
- AI models should be treated as shared enterprise capabilities with unified lifecycle tooling and governance
- Open standards and interoperability (MCP, A2A protocols) are essential to avoid vendor lock-in

## Summary

Salesforce's Agentforce division published this comprehensive reference architecture for organizations transitioning to "Agentic Enterprises" that integrate digital AI workers with human employees. The document argues that current enterprise IT architectures are fundamentally insufficient for widespread agent deployment and proposes a ground-up rethinking.

The centerpiece is an 11-layer architecture model spanning Experience, Agentic, AI/ML, Enterprise Orchestration, Application Services, Semantic, Data, Infrastructure, Integration, IT Operations & Observability, and Security layers. Each layer is described with specific capabilities, dependencies, and design principles. Key design principles include composability and modularity, data and semantic-first approach, embedded observability, trust throughout, agent-first with human oversight, and AI-ready infrastructure.

The document also proposes a phased maturity approach, recommending organizations establish foundation layers (data governance, semantic models, AI/ML centralization, observability) before deploying agents at scale. Notably, it emphasizes hybrid orchestration combining centralized governance with decentralized agent choreography.

## Notable Quotes

> "To realize this vision, organizations must undergo a business and IT transformation to become Agentic Enterprises."

> "While traditional architecture may support sub-scale deployments of AI agents today, it cannot fully deliver the business capabilities."

> "Embedding this functionality directly in today's static and deterministic application architecture would introduce unnecessary architectural complexity and risk."

## Relevance to Topic

The most detailed vendor-produced reference architecture for agentic enterprise systems. The 11-layer model provides a concrete counterpoint to the 8-layer academic framework in source 1 (Kumar), and the maturity model adds practical adoption guidance missing from the academic sources.
