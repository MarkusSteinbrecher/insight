---
title: "Agentic AI Performance Claims Show Promise but Lack Independent Validation"
type: evidence
confidence: low
sources:
  - source-001
  - source-002
tags:
  - agentic-ai
  - performance-benchmarks
  - multi-agent-systems
  - evidence-quality
  - enterprise-architecture
created: 2026-02-14
---

## Insight

Both academic sources (source-001 and source-002) make specific performance claims about agentic AI systems applied to enterprise architecture tasks, but these claims require careful scrutiny. Kumar's framework (source-001) reports striking performance improvements: 96.3% threat detection accuracy versus 85.7% for traditional models, response times under 200ms versus 1.2 seconds, a false positive rate of 2.1% versus 5.4%, and computational efficiency of 78% versus 62%. These numbers, if reproducible, would represent a transformative improvement. However, the paper is a single-author proposal, the comparative benchmarks are self-generated against unnamed "traditional" and "baseline predictive" models, and no independent replication or peer validation of these specific figures is presented. The methodology for generating these comparisons is not described in sufficient detail to enable replication.

Oaj et al. (source-002) present more modest and transparent results. Their ABMA prototype generated a 5-level capability map for the insurance industry in Japan, but in the EKG-enhanced configuration, only Level 1 capabilities matched the enterprise knowledge graph -- all Level 2 and Level 3 sub-capabilities returned "No" for EKG matching. This honest reporting of limitations is more credible than Kumar's uniformly positive results, but it also reveals how early-stage agentic AI for EA really is. The LLM-only configuration produced "semantically plausible but unverified" capabilities, while the EKG-enhanced version achieved semantic alignment only at the shallowest level of the hierarchy. Both configurations remain far from production-ready.

The contrast between these two papers is itself informative. Kumar's framework proposes a comprehensive, multi-layered architecture with impressive benchmarks but limited empirical validation. Oaj et al.'s prototype is narrower in scope but more rigorous in acknowledging what does and does not work. Together, they paint a picture of a field where the architectural vision is running well ahead of demonstrated capabilities -- a pattern consistent with the Economist report's finding (source-003) that only 37% of executives believe their GenAI applications are production-ready.

## Supporting Evidence

- Proposed agentic model: 96.3% threat detection accuracy vs. 85.7% traditional and 88.5% baseline predictive (source-001)
- Proposed agentic model: <200ms response time vs. 1.2s traditional and 850ms baseline (source-001)
- Proposed agentic model: 2.1% false positive rate vs. 5.4% traditional and 4.8% baseline (source-001)
- Proposed agentic model: 78% computational efficiency vs. 62% traditional and 67% baseline (source-001)
- EKG-enhanced ABMA: only Level 1 capability "Claims Management" matched the enterprise knowledge graph; all Level 2 and Level 3 sub-capabilities returned "No" for EKG matching (source-002, Table 2, p. 7)
- LLM-only ABMA (Configuration 1): generated capabilities like "Claims Submission," "Claims Settlement" -- semantically plausible but unverified against organisational standards (source-002)
- Only 37% of executives believe their GenAI applications are production-ready (source-003), contextualising the academic claims against industry reality
- "Configuration 1 performed better at creative, unconstrained generation of the capability map, but was semantically unverified. Configuration 2 offered semantic alignment and potential ontology alignment of capabilities, but it is limited to level 1." (source-002, p. 8)

## Evidence Assessment

This insight is assessed at **low confidence** specifically regarding the quantitative performance claims from source-001. Kumar's paper presents benchmarks without sufficient methodological transparency: the "traditional" and "baseline predictive" comparisons are not independently sourced or described in detail, the testing environment and datasets are not specified for replication, and the paper is a single-author work without visible external peer validation of the specific numbers. These are not necessarily fabricated -- they may well come from simulation or proof-of-concept testing -- but they cannot be independently verified from the information provided. In contrast, Oaj et al.'s (source-002) findings are more methodologically transparent (Design Science Research, clearly described prototype, honest limitation reporting), but they demonstrate very limited capability (Level 1 matching only), making it difficult to draw strong conclusions about agentic AI's readiness for production EA tasks.

The overall evidence landscape suggests that agentic AI for enterprise architecture is in a pre-validation phase: theoretical frameworks are being proposed (source-001), prototypes are being built (source-002), but robust, independently validated performance evidence is largely absent. This is consistent with the broader AI maturity pattern identified in source-003.

## Implications

Technology leaders should approach vendor and academic claims about agentic AI performance with healthy scepticism and demand rigorous evidence before committing to architectural transformations. The gap between proposed frameworks and demonstrated capabilities is significant. Organisations should invest in small-scale pilots and proof-of-concept projects that generate their own performance data rather than relying on external benchmarks. When evaluating agentic AI platforms, enterprise architects should ask for independently validated benchmarks, replication details, and evidence from production (not lab) environments. The honest limitations reported in source-002 -- where even a well-designed multi-agent system could only match Level 1 capabilities against an enterprise knowledge graph -- should calibrate expectations about the current maturity of AI-assisted enterprise architecture. The field shows genuine promise, but the evidence base does not yet support large-scale production commitments.
