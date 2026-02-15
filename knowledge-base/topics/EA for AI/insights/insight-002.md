---
title: "Agent Memory Is an Underappreciated Infrastructure Concern"
type: pattern
source_claims:
  - cc-164  # Agent memory architecture
  - cc-078  # Enterprise knowledge graph
  - cc-136  # Knowledge graph as differentiator
sources:
  - source-055  # Akka — primary
  - source-001  # Kumar — supporting
finding_links:
  - finding-3  # Multi-Agent Architecture
  - finding-4  # AI-Augmented EA
  - finding-8  # Infrastructure Readiness Crisis
created: 2026-02-15
---

# Agent Memory Is an Underappreciated Infrastructure Concern

## Insight

Agent memory — both short-term (task context) and long-term (cross-session persistence) — is a distinct infrastructure requirement that existing enterprise architectures do not account for, and its absence constrains agent capability as much as model quality or reasoning sophistication.

## Evidence Chain

Source-055 establishes the foundational constraint: LLMs are stateless and retain no memory of a conversation (seg-029). Systems must implement external memory to give agents context (seg-030). The source distinguishes:

- **Short-term memory**: held during the current task, providing conversation context (seg-031).
- **Long-term memory**: persists across sessions — user preferences, historical patterns, closed ticket solutions (seg-032, seg-033).

Source-001 extends this with technical implementations: vectorized memory using pgvector and Pinecone, RAG as a memory retrieval mechanism. The enterprise knowledge graph (cc-078, cc-136) represents the organizational-scale version of long-term memory — shared context that enables agents to understand the specific enterprise they operate in.

The infrastructure implications are substantial: memory requires dedicated storage (vector databases, graph databases, caching layers), introduces latency at retrieval time, consumes tokens through context injection, and creates data governance obligations (what is stored, for how long, under what privacy constraints).

## Significance

The corpus extensively discusses model selection, agent orchestration, and governance frameworks. Agent memory receives far less attention despite being a prerequisite for agent effectiveness. An agent without adequate memory is stateless — it cannot learn from prior interactions, personalize responses, or build organizational context. Memory architecture sits in the same underinvested category as infrastructure (Finding 8): foundational, unglamorous, and binding.

## Gap

No source in the corpus addresses: shared memory architectures for multi-agent systems, memory governance frameworks (staleness management, GDPR compliance for persistent agent memory), or the cost economics of context injection at scale.
