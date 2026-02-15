---
title: "Agent Reasoning Architecture Requires Explicit Tradeoff Analysis"
type: pattern
source_claims:
  - cc-163  # Agent reasoning approaches taxonomy
  - cc-004  # Right-sizing models to tasks
  - cc-089  # Model size ≠ business value
  - uc-123  # Self-consistency technique
sources:
  - source-055  # Akka — primary
  - source-001  # Kumar — supporting
finding_links:
  - finding-2  # The Model Is the Commodity
  - finding-3  # Multi-Agent Architecture
created: 2026-02-15
---

# Agent Reasoning Architecture Requires Explicit Tradeoff Analysis

## Insight

The choice of reasoning approach for an AI agent — symbolic, chain-of-thought, or planning — is an architectural decision with order-of-magnitude cost and performance implications that most organizations are not making deliberately.

## Evidence Chain

Source-055 articulates a three-part reasoning taxonomy:

1. **Symbolic reasoning** (rule-based logic): rigid but fast, lower token cost, longer development time, does not handle novel scenarios well (seg-021, seg-022, seg-043).
2. **Chain-of-thought** (LLM-based step-by-step): flexible but expensive, multiple LLM round-trips per task, performs well on new tasks with minimal additional training (seg-023, seg-024, seg-025, seg-042).
3. **Planning** (goal-directed task decomposition): selects and orders steps from initial state to goal state, balances structure with adaptability (seg-028).

The cost dimension is significant: chain-of-thought can involve "many back and forth LLM queries" (seg-042), while symbolic reasoning "will require fewer LLM tokens" (seg-043). Combined with uc-124's claim that agentic tasks can be 100,000x more expensive than database costs, reasoning approach selection becomes one of the highest-leverage cost decisions in agent architecture.

This connects to the broader model right-sizing theme (cc-004, cc-089): just as organizations should route tasks to the smallest adequate model, they should route to the cheapest adequate reasoning approach. The self-consistency extension (uc-123) — running the same query multiple times and returning the most common result — trades additional cost for reliability, representing yet another explicit tradeoff.

## Significance

The reasoning approach decision sits at the intersection of cost, accuracy, flexibility, and development time. Organizations defaulting to chain-of-thought for all agent tasks (the path of least development resistance) are paying orders of magnitude more than necessary for tasks that symbolic or planning approaches could handle. This mirrors the model over-provisioning pattern identified in Finding 2.

## Gap

No source provides a decision framework for selecting reasoning approaches based on task characteristics, nor cost benchmarks comparing approaches on equivalent enterprise tasks.
