---
title: "Review: EA From Automation to Autonomy Blog"
type: review
target: "EA for AI Blog.md"
created: 2026-02-17
status: draft
---

# Review: "EA: From Automation to Autonomy"

## Overall Assessment

The blog is well-structured, clearly written, and puts forward a distinctive proposition — collapsing the traditional 4-domain EA model into a leaner 3-domain model for the agentic era. The "automation to autonomization" framing is effective and original. However, when measured against the 10 research findings, 24 contradictions, and 8 thought leadership positions from the synthesis, the article has significant gaps, one structural tension with the research, and several places where it could be sharpened with evidence the research already provides.

---

## Issues

### 1. The Technology dismissal contradicts Finding 8 (Infrastructure Readiness Crisis)

The blog's central structural move — demoting Technology from a strategic domain to "embedded in platform choices and cloud configurations" — directly contradicts the strongest data-backed finding in the research. Only 14% of companies are infrastructure-ready (KPMG, n=2,500). Only 17% have networks capable of handling AI demands. Only 22% have architectures that support AI without modification. The blog treats infrastructure as a solved problem ("cloud, virtualisation, everything-as-a-service") when the research shows it is the *binding constraint* on enterprise AI.

The blog's argument is logically sound for mature cloud-native organizations. But for the vast majority of enterprises, demoting Technology from the EA model while they cannot yet run AI workloads on their infrastructure sends a misleading signal. This is the most significant tension between the article and the research.

**Proposed change:** Acknowledge the infrastructure readiness gap explicitly. The Technology domain may be converging with platform choices *in direction*, but for most enterprises today, infrastructure is the bottleneck, not a solved problem. Consider a qualifying paragraph: "For organizations with mature cloud foundations, Technology increasingly becomes embedded. But survey data shows that fewer than one in five enterprises have infrastructure capable of supporting AI at production scale — for them, Technology architecture remains an urgent priority, not a background concern."

### 2. Governance treatment is thin relative to Finding 1 (Governance Speed Problem)

The blog mentions guardrails and agent governance, but treats governance primarily as an additive concern — "add guardrails to your architecture principles." The research finding is more structural: governance cycles that exceed deployment cycles create risk rather than mitigating it. The blog misses the governance speed paradox entirely — the finding that traditional governance processes are not just slow but *counterproductive* in an AI context, making decisions on stale information.

**Proposed change:** Strengthen the governance section. Add the speed dimension: "The critical governance evolution is not just *what* we govern (adding guardrails for agents) but *how fast* we govern. When governance review cycles exceed AI deployment cycles, the governance process itself becomes a source of architectural risk — approving designs that are already outdated. The shift is from periodic, committee-based governance to continuous, machine-assisted governance with exception-based human escalation."

### 3. "Business architecture IS the prompt" needs grounding in Enterprise as Code (Finding 9)

This is the blog's best line, but it floats without supporting structure. The research provides that structure through BCG's "Enterprise as Code" concept — the idea that organizations must codify their implicit operating models as executable code. The blog almost reaches this insight but stops short.

**Proposed change:** Connect the line to the Enterprise as Code concept. "Your business architecture IS the prompt — but only if it is machine-readable. Most organizations' business architecture exists in slide decks and people's heads. For agents to consume capability definitions, process models, and business rules, these must be codified as executable specifications. This is the shift from documentation to codification — what some are calling 'Enterprise as Code.'"

---

## Challenge Statements

### 4. The "Will Agents replace Applications?" section undersells the risk dimension

The blog frames agents-vs-applications as an evolutionary direction, which is reasonable. But it does not address the qualitatively new failure modes from Finding 3 — when agents influence each other's outputs through shared context, feedback loops and cascade failures become possible in ways deterministic applications never exhibited. The blog presents the merge as a clean convergence; the research shows it introduces risks that existing observability and monitoring cannot detect.

**Proposed change:** Add a risk acknowledgement: "The convergence of agents and applications also introduces new architectural risks. When agents influence each other through shared context and chained outputs, failure modes become non-linear — one agent's inaccurate output can become another's confident input. Designing for observability, blast-radius controls, and distributed tracing across agent interactions is as important as designing the agents themselves."

### 5. The model reduction from 18 to 12 capabilities implies simplification — the research suggests the opposite

The blog positions the model as "leaner." The research findings collectively suggest that the agentic era introduces *more* architectural complexity, not less: agent lifecycle management (Finding 7), multi-model orchestration (Finding 2), process redesign prerequisites (Finding 5), sovereignty constraints (Finding 10), and infrastructure readiness (Finding 8). Reducing capabilities may streamline a visual model, but the claim of leanness risks miscommunicating the actual scope of work.

**Proposed change:** Reframe. Instead of "leaner," position the model as "refocused" or "restructured" — fewer boxes on the chart does not mean less work; it means work is organized differently. A sentence like: "Reducing from 18 to 12 capabilities does not mean the job is simpler. It means the architectural centre of gravity has shifted — and new challenges (agent lifecycle management, multi-model orchestration, sovereignty compliance) emerge within the restructured domains."

### 6. Missing the process redesign prerequisite (Finding 5)

The blog discusses what the new EA model looks like but does not address *how organizations get there*. Finding 5 — the strongest practitioner-validated finding in the research — says that process redesign must precede AI deployment. BCG's 10/20/70 rule quantifies this: 70% of AI transformation work is people and processes, 20% technology backbone, 10% algorithms. The blog's "Five practical steps" section partially addresses this, but the main article body does not.

**Proposed change:** Add a paragraph acknowledging the process prerequisite, even briefly: "A critical prerequisite: before agents can deliver on this model, organizations must understand and redesign their processes for agent strengths. Research consistently shows that inserting agents into human-designed workflows — with sequential approvals, handoff points, and periodic checkpoints — delivers marginal value. The real gains come from redesigning processes from scratch for what agents do well: parallel execution, consistent attention, and continuous availability."

---

## Additional Insights to Incorporate

### 7. Model commoditization and multi-model architecture (Finding 2)

The blog does not mention that foundation models are commoditizing and that competitive advantage lies in proprietary data, domain knowledge, and integration quality. The Agents & Apps domain would benefit from acknowledging that model selection is becoming a per-task decision, not a platform-level default, and that designing for model portability (the 8-hour swap test) is an architectural principle worth calling out.

**Suggested addition:** Within the Agents & Apps description, note: "A key architectural principle: treat AI models as swappable commodity. Design for model portability — the ability to switch your primary LLM provider rapidly — and right-size models to tasks. A fine-tuned small model often outperforms a frontier model on well-scoped enterprise tasks at a fraction of the cost."

### 8. Agent Management as an emerging discipline (Finding 7)

The blog mentions agent governance but does not address agent lifecycle management — the fact that agents need onboarding, performance management, versioning, retraining, and decommissioning. At scale (50+ agents), this becomes a formal discipline that maps to neither ITIL nor traditional HR frameworks. The Agent Registry mentioned in the practical steps deserves elevation into the model itself.

**Suggested addition:** In the governance section: "Beyond governance, agent *management* is an emerging discipline. Agents require onboarding (testing, validation, access provisioning), performance monitoring (accuracy, cost, drift detection), and lifecycle management (versioning, retraining, retirement). No existing framework — ITIL, HR, or otherwise — fully addresses these needs. Organizations scaling beyond a handful of agents will need to develop this discipline, starting with a comprehensive Agent Registry."

### 9. AI Sovereignty (Finding 10)

The blog has no mention of sovereignty. For a PwC Switzerland publication targeting European enterprises, this is a notable gap. 82% of EMEA organizations are refining their cloud approach due to geopolitics (PwC EMEA). 54% prioritize data and AI sovereignty (Capgemini). Where data resides, which models process it, and what jurisdictional rules apply are first-order architecture constraints that the model should acknowledge.

**Suggested addition:** A brief paragraph in the Data & Knowledge section or conclusion: "For European organizations, AI sovereignty is now a first-order architecture constraint. Where data resides, which models process it, and what jurisdictional rules apply constrain every architectural choice. Sovereignty should be embedded by default — not treated as a post-hoc compliance step."

### 10. The C-Suite expectation gap (Finding 6)

The blog does not address the misalignment between CEO expectations (revenue growth) and CIO expectations (cost savings) from AI investments. This is relevant because the EA model the blog proposes will be evaluated differently by different stakeholders. Mentioning this gap, even briefly, strengthens the Business domain section.

**Suggested addition:** In the Business section: "A practical challenge: alignment on what AI should deliver. When the CEO expects revenue growth and the CIO expects cost savings, every AI project risks underperforming against at least one sponsor's criteria. The Business domain must make this explicit — structuring the AI portfolio with distinct value buckets and distinct success metrics."

---

## Minor Observations

- **"OLD TEXT & FRAGMENTS" section:** Should be removed from any published version. The useful content (12 capabilities explained, governance comparison table, role evolution table, five practical steps) should be integrated into the main text or cut.
- **"Your business architecture IS the prompt":** Strong line but needs the Enterprise as Code grounding mentioned above. Without it, the claim is provocative but unsubstantiated.
- **The "five practical steps" in the old text section are strong** and should be promoted into the main article body. They ground the conceptual model in actionable advice. Consider adding "Invest in process redesign" as a step.
- **SEO keywords:** Consider adding "AI sovereignty," "infrastructure readiness," and "Enterprise as Code" given their prominence in the research.

---

## Summary of Proposed Changes

| # | Type | Description |
|---|------|-------------|
| 1 | **Issue** | Qualify the Technology dismissal with infrastructure readiness data |
| 2 | **Issue** | Strengthen governance section with the speed paradox |
| 3 | **Issue** | Ground "business architecture IS the prompt" in Enterprise as Code |
| 4 | **Challenge** | Add risk dimension to agents-replacing-applications narrative |
| 5 | **Challenge** | Reframe "leaner" as "refocused" — complexity is shifting, not shrinking |
| 6 | **Challenge** | Add process redesign prerequisite (Finding 5, 10/20/70 rule) |
| 7 | **Insight** | Add model commoditization and multi-model architecture |
| 8 | **Insight** | Elevate agent lifecycle management as emerging discipline |
| 9 | **Insight** | Add AI sovereignty for European audience |
| 10 | **Insight** | Mention C-Suite expectation gap in Business domain |
