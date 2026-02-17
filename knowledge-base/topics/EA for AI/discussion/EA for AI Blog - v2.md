# EA: From Automation to Autonomy

**An Enterprise Architecture Capability Model for the Agentic Enterprise**

---

**Abstract:** Agentic AI is shifting enterprise IT from automation to autonomization -- from systems that follow predefined steps to agents that pursue goals. What does this mean for Enterprise Architecture? We propose a refocused EA Capability Model for the Agentic Enterprise -- built on three strategic domains: Business, Agents & Applications, and Data & Knowledge. We describe what changes in each EA layer, what new capabilities are needed, and how governance itself must evolve.

---

## From automation to autonomization

For decades, the logic of enterprise software was simple: humans decide, systems execute. Automation made systems faster and us more efficient. But the fundamental pattern remained -- a human defines the steps, a system follows them.

**Agentic AI breaks this pattern.**

An AI agent doesn't follow predefined steps. It pursues goals. It reasons, plans, uses tools, evaluates results, and adapts. It operates with a degree of autonomy that enterprise IT has not seen before.

This is more than a technological shift. For Enterprise Architects and Technology Leaders designing these systems, the focus changes fundamentally -- from automation to autonomization:

> **Automation** asks: *"How do we execute this process faster? What can we automate and integrate?"*
>
> **Autonomization** asks: *"What is the goal? How do we define it clearly enough for an agent to achieve it on its own? And what is it allowed to do -- and what not?"*

**Automation** = programming and integration.
**Autonomization** = prompting, orchestrating, and guardrailing.

If autonomous agents become a primary way of delivering business capabilities, then the very structure of our Enterprise Architecture models needs to evolve. Our own EA capability model is grounded in established frameworks like TOGAF and ArchiMate, built on the classic domains -- Technology, Data, Application, and Business -- plus a set of common capabilities. It reflects how enterprise IT has traditionally been structured for the past two decades.

*[Insert Classic EA Capability Model graphic]*

---

## What changes in each EA layer?

Based on ongoing research and discussions at PwC Switzerland, we propose a first evolution -- not a replacement of established models, but a perspective on how they might adapt. The shifts are different in each layer: one domain becomes embedded, one merges, one extends, and one becomes more important than ever. Here is what changes, and why.

---

### Technology becomes embedded -- but the foundation must not be neglected

This shift is less about Agentic AI and more about trends that have been building for years: cloud, virtualisation, everything-as-a-service, zero trust.

When infrastructure is consumed as a service -- when a development team provisions compute, storage, and networking through a single API call -- the architectural significance of modelling systems, networks, and virtualisation separately diminishes. With zero trust, even the network perimeter loses its relevance -- security is no longer a function of topology, but of identity and policy. Technology architecture becomes increasingly standardised and embedded in platform choices and cloud configurations.

This is a pragmatic recognition of where enterprise architecture creates the most strategic value today -- no longer in server setup and network topologies, but in the design of business capabilities, agent architectures, and the data and knowledge that powers them.

**However, "embedded" does not mean "solved."** Recent surveys paint a sobering picture: only 14% of companies are fully prepared for AI adoption. Only 17% have networks capable of handling AI demands. Only 22% have architectures that support AI workloads without modification. The gap between AI ambition and infrastructure capability remains the binding constraint for most enterprises.

For organisations with mature cloud foundations, Technology increasingly becomes embedded in platform choices. For the majority that are not yet there, Technology architecture remains an urgent priority -- not a background concern. AI workloads demand compute, networking, storage, and integration at a scale that most organisations have not yet planned for. The industry has focused on the AI "brain" -- models and agents -- while underinvesting in the "nervous system" that connects AI to enterprise systems.

#### What changes in Technology Architecture

- **AI-specific infrastructure planning** -- GPU compute, high-bandwidth networking, vector storage, and inference-scale throughput become standard requirements
- **Platform engineering replaces traditional infrastructure management** -- the goal is self-service, API-driven provisioning with built-in security and observability
- **AI sovereignty becomes a first-order constraint**, particularly for European organisations: where data resides, which models process it, and what jurisdictional rules apply now constrain cloud and vendor decisions
- **FinOps for AI emerges as a distinct discipline** -- agentic AI workloads can be orders of magnitude more expensive than traditional compute, and most organisations lack the financial governance to manage this

---

### Applications and Agents converge

In a radical view: why would there be applications? Humans interact directly with smart, personalised agents. Agents perform all tasks necessary -- all they need is data, knowledge, and the help of other specialised agents.

Consider what today's applications actually are: a user interface, business logic, data access, and integration points -- bundled into a package. Now consider what an agent does: it interacts through natural language, reasons about business logic dynamically, accesses data through tools and APIs, and orchestrates across systems natively.

But this is a direction, not today's reality. Legacy systems will persist for decades. New applications will still be built. And where the same tasks need to be executed efficiently, at high volume, and exactly the same way every time -- applications may well keep their place. The architectural centre of gravity, however, is shifting: **from applications as the primary execution layer to agents as the primary orchestration layer.**

That is why our new model does not separate them. It combines them into one domain: **Agents & Applications** -- because in an agentic enterprise, the boundary between the two will blur beyond distinction.

This convergence also introduces **new architectural risks.** When multiple agents collaborate through shared context, chained outputs, or collaborative decision-making, failure modes become qualitatively different from those of deterministic applications. One agent's inaccurate output can become another agent's confident input, triggering cascading errors that existing monitoring tools were not designed to detect. Designing for observability, blast-radius controls, and distributed tracing across agent interactions is as important as designing the agents themselves.

#### What changes in Application / Agent Architecture

- **New communication patterns** -- agent-to-agent, agent-to-system, and agent-to-human interactions replace traditional point-to-point integration. Protocol abstraction layers (not commitment to a single protocol) provide architectural agility as standards like MCP and A2A mature
- **Model selection becomes a per-task decision**, not a platform default: foundation models are commoditising, and a fine-tuned small model often outperforms a frontier model on well-scoped enterprise tasks at a fraction of the cost. Design for model portability -- the ability to switch your primary LLM provider rapidly
- **Agent lifecycle management emerges as a new discipline**: agents need onboarding, performance monitoring (accuracy, cost, drift detection), versioning, and retirement -- requirements that map to neither ITIL nor traditional HR frameworks
- **The application portfolio becomes an agent-and-application registry** that catalogues autonomy levels, tool access, decision authority, data inputs, and accountable human owners

---

### Data extends to Knowledge

Data has gradually moved from a supporting role to centre stage. For decades, data was simply part of applications -- stored in application databases, modelled within application logic, owned by application teams. Its emergence as a separate architectural domain reflects a long journey: from data warehousing, to master data management, to data mesh and data products.

With agents, this trend accelerates. Agents are only as good as the data they can access -- and critically, they depend not just on data, but on **metadata and knowledge**. This includes entirely new architectural concepts:

- **Knowledge graphs and ontologies** that give agents semantic understanding of the organisation
- **RAG architectures** that ground agent responses in organisational knowledge
- **Agent memory and context stores** that enable agents to maintain state across interactions
- **Embeddings and vector databases** that make unstructured knowledge searchable
- **Metadata** -- process descriptions, business rules, data lineage -- that agents need to operate effectively

This is why we renamed the domain from "Data Architecture" to **Data & Knowledge**. It is not just about storing and modelling data anymore. It is about curating the knowledge fabric that agents reason on.

The **enterprise knowledge graph** deserves particular attention. It is the critical differentiator between agents that operate on generic knowledge and agents that understand *your* organisation. Agents without a shared semantic context are like employees without a common language -- generating activity without alignment. Investing in knowledge infrastructure before agent infrastructure may seem counterintuitive, but it determines whether agents produce organisational value or generic outputs.

For European organisations, **data and AI sovereignty** adds another dimension. 82% of EMEA organisations are already refining their cloud approach due to geopolitical and regulatory change. Where data resides, which models process it, and what jurisdictional rules apply are no longer compliance checkboxes -- they are first-order architecture constraints that must be embedded by default into every data and knowledge architecture decision.

#### What changes in Data Architecture

- **The domain expands** from structured data management to include knowledge graphs, ontologies, vector stores, RAG architectures, and agent memory
- **Data quality requirements intensify** -- agents amplify both the value of good data and the cost of bad data, making data governance a prerequisite rather than a parallel workstream
- **Metadata becomes operational infrastructure**: process descriptions, business rules, and data lineage are no longer documentation for humans -- they are instructions that agents consume
- **Sovereignty must be designed in from the start**: data residency, model provenance, and jurisdictional constraints inform every architectural choice

---

### Business Architecture becomes the instruction set

While technology becomes embedded and applications get absorbed, the Business Architecture domain remains as relevant as ever. Arguably more so.

Agents need clear business intent to function. They need value drivers to understand what matters. Capability definitions to know what the organisation can and should do. Process and interaction models to understand how work flows -- and where they fit in.

**The key evolution:** capability definitions must now explicitly capture *who or what* delivers each capability -- a human, a system, an agent, or a hybrid. And process models must accommodate goal-driven, non-deterministic flows alongside traditional sequential processes.

In a fully agentic future, agents may not need applications. But they will always need metadata: process descriptions, business rules, capability definitions -- these become the instructions that agents consume.

> **Your business architecture IS the prompt.**

But only if it is machine-readable. Most organisations' business architecture exists in slide decks, Visio diagrams, and people's heads. For agents to consume capability definitions, process models, and business rules, these must be codified as executable specifications -- not as documentation for quarterly reviews, but as operational code that agents can interpret and act on. This is the shift from documentation to codification, from intuition-based operations to specification-based ones -- what some are calling **"Enterprise as Code."**

#### From code specifications to business specifications

We can already observe this pattern in software development. AI-assisted coding tools -- from code completion to autonomous coding agents -- are most effective when guided by clear specifications: requirements documents, acceptance criteria, architecture constraints, interface definitions, and test cases. Without specifications, AI generates generic code. With specifications, it generates purposeful, testable, reviewable code. The specification is the prompt -- and the quality of the output is directly proportional to the quality of the specification.

We hypothesise that this same pattern will define how AI agents execute business processes. Just as a software specification tells a coding agent *what* to build, *how* to structure it, and *how to verify* the result, a **business process specification** will tell a business agent *what* outcome to achieve, *within what boundaries*, and *how to know it succeeded*.

What would such a specification look like? We propose that a business architect defining a process for agent execution would need to provide:

- **Goal and success criteria** -- not a step-by-step procedure, but a measurable outcome definition. What does "done" look like? What are the quality thresholds? This is the equivalent of acceptance criteria in software development.
- **Inputs, outputs, and data contracts** -- which data objects flow in, what the agent produces, and in what format. Analogous to API contracts and interface definitions.
- **Decision rules and business logic** -- codified, not implicit. When to approve, reject, escalate, or defer. Today these rules live in people's experience; for agents, they must be explicit and machine-interpretable.
- **Guardrails and constraints** -- what the agent must *not* do. Spending limits, compliance boundaries, data access restrictions, escalation triggers. The equivalent of security policies and architectural constraints in software.
- **Context and knowledge references** -- which knowledge bases, policies, regulations, and organisational standards apply. The agent needs to know where to look, not just what to do.
- **Autonomy level and escalation paths** -- at what point human judgment is required. Not every decision should be autonomous; the specification must define the boundary explicitly.
- **Verification and audit criteria** -- how the organisation validates that the process was executed correctly. The equivalent of test cases -- but for business outcomes rather than code behaviour.

This is a fundamental shift in what business architecture *produces*. Today, a process model is a communication tool -- it helps humans understand how work flows. Tomorrow, a process specification is an *execution instruction* -- it tells an agent how to deliver a business outcome. The rigour required is closer to software engineering than to traditional process documentation: ambiguity that a human can resolve through judgment becomes a failure mode when an agent encounters it.

The implication for business architects is significant. Their deliverable evolves from descriptive models (boxes and arrows that illustrate a process) to **prescriptive specifications** (structured, testable definitions that agents can execute and that humans can audit). Business architects will need to think like specification writers: defining not just the happy path, but the edge cases, exceptions, and verification criteria that make the difference between an agent that handles a process and an agent that handles it *well*.

This is "Enterprise as Code" made concrete -- and it positions business architecture as the discipline that translates organisational intent into agent-executable instructions.

**A critical prerequisite sits beneath this shift:** processes must be redesigned for agent strengths *before* they are automated. The most common anti-pattern in enterprise AI today is taking a human-designed workflow -- complete with sequential approval chains, specialist handoff points, and periodic review checkpoints -- and bolting an AI agent onto it. The agent inherits all the constraints of the human workflow while exploiting none of its own strengths: parallel processing, consistent attention, comprehensive recall, and continuous availability. Research consistently shows that 70% of AI transformation work is people and processes, 20% is technology backbone, and only 10% is algorithms. The real value comes not from automating what exists, but from redesigning how work is done.

**A practical challenge sits above it:** alignment on what AI should deliver. When the CEO expects AI to drive revenue growth and the CIO expects productivity savings, every AI project risks underperforming against at least one sponsor's criteria. The Business Architecture domain must make this explicit -- structuring the AI portfolio with distinct value buckets and distinct success metrics, and ensuring the platform architecture can evolve from early productivity use cases to higher-value, revenue-generating applications.

#### What changes in Business Architecture

- **Capability definitions** must capture who or what delivers each capability: human, system, agent, or hybrid -- and at what level of autonomy
- **Process models** must accommodate goal-driven, non-deterministic agent flows alongside traditional sequential workflows -- and processes should be redesigned for agent strengths before automation
- **Business rules and decision logic** must be codified in machine-readable formats that agents can interpret -- the shift from documentation to executable specification
- **Process specifications replace process models** as the primary deliverable: structured, testable definitions with goal criteria, decision rules, guardrails, context references, and verification criteria -- the business equivalent of software specifications that AI coding agents already consume
- **Value driver definitions** must explicitly address the AI expectation gap: separate value streams for productivity, revenue growth, and cost optimisation, each with appropriate KPIs

---

## The Agentic EA Capability Model

Based on these shifts, we have developed an Agentic EA Capability Model: **refocused and restructured**, reduced from 18 to 12 capabilities, with a clear dual logic:

- **Vertically**, four domains: Common, Business, Agents & Apps, and Data & Knowledge
- **Horizontally**, three phases: Define (the what), Architect (the how), and Transform (the where to)

The Technology domain is integrated into platform choices and cloud configuration -- with the caveat that infrastructure readiness remains a prerequisite that most organisations have not yet met. The Application domain has merged with Agents into a combined domain. Data has been extended with Knowledge. And Business remains the anchor.

**Reducing from 18 to 12 capabilities does not mean the job is simpler.** It means the architectural centre of gravity has shifted -- and new challenges (agent lifecycle management, multi-model orchestration, knowledge architecture, sovereignty compliance) emerge within the restructured domains.

*[Insert Agentic EA Capability Model graphic]*

This model is a starting point, not a final answer. We invite the EA community to challenge and evolve it with us. And in practice, both models will coexist -- the classic for today's landscapes, the agentic for where we are heading.

---

### The 12 capabilities

#### Common

| Phase | Capability | Description |
|-------|-----------|-------------|
| Define | **Architecture Vision Development** | Define the architectural ambition, including the target level of agent autonomy and the role of AI in the future enterprise |
| Architect | **Architecture View Creation** | Create architectural views and representations that make complexity manageable -- including new views like Agent Landscape Maps and Decision Authority Matrices |
| Transform | **Transformation Planning** | Plan the transformation from current to future state -- roadmaps, migration paths, transition architectures |

#### Business

| Phase | Capability | Description |
|-------|-----------|-------------|
| Define | **Strategic Value Driver Definition** | Identify what drives business value -- including AI-enabled value streams and agent-driven efficiency gains, with explicit separation of productivity and revenue objectives |
| Architect | **Capability Definition** | Define business capabilities and explicitly map whether each is delivered by humans, systems, agents, or hybrids -- and at what autonomy level |
| Transform | **Process & Interaction Modelling** | Model business processes and human-agent interaction patterns -- from sequential workflows to goal-driven, adaptive flows. Evolve process models into agent-executable specifications: goal criteria, decision rules, guardrails, context references, and verification criteria |

#### Agents & Apps

| Phase | Capability | Description |
|-------|-----------|-------------|
| Define | **Agent & Application Definition** | Catalogue all agents and applications. Define agent types, autonomy levels (L0-L5), tool access, model dependencies, and ownership. This is the new "Application Portfolio" -- extended with agent metadata and model portability requirements |
| Architect | **Agent & Application Architecture Modelling** | Model how agents and applications are structured, how they integrate, how they communicate (agent-to-agent, agent-to-system, agent-to-human), protocol abstraction layers, and blast-radius controls for multi-agent interaction |
| Transform | **Agent & Application Validation & Testing** | Validate that agent architectures meet requirements. Test agent behaviour against guardrails. Plan releases and migrations from legacy applications to agent-based solutions. Manage agent lifecycle: onboarding, monitoring, retraining, retirement |

#### Data & Knowledge

| Phase | Capability | Description |
|-------|-----------|-------------|
| Define | **Data & Knowledge Asset Definition** | Identify and define data objects, knowledge assets, ontologies, metadata structures, and the content that agents will consume -- including sovereignty classification for each asset |
| Architect | **Data & Knowledge Architecture** | Design the overall data and knowledge architecture -- including knowledge graphs, RAG architectures, vector stores, agent memory, traditional data models, and sovereignty-compliant deployment patterns |
| Transform | **Data Flow & Pipeline Modelling** | Model how data and knowledge flows through the landscape -- ETL/ELT pipelines, AI training pipelines, prompt chains, reasoning traces, and feedback loops |

---

## Governance must change speed, not just scope

Architecture development is only one part of the picture. An enterprise also needs capabilities for EA management, the maintenance of the EA repository, and governance. Management and repository don't change fundamentally in an agentic world -- but **governance does**. And the change is not just in *what* we govern, but in *how fast* we govern.

Here is the structural problem: **when governance review cycles exceed AI deployment cycles, the governance process itself becomes a source of architectural risk** -- approving designs that are already outdated. A review board that meets monthly to evaluate architectures designed three weeks ago and deployed the following week is not governing -- it is making decisions on information that has already expired. The fix is not faster meetings or shorter review cycles. It is closing the governance loop: pushing routine governance decisions into automated or near-instant channels so that human judgment is concentrated where it actually adds value.

| Classic | Agentic |
|---------|---------|
| Standards, Policies, Principles, Guidelines | Standards, Policies, Principles, Guidelines, **& Guardrails** |
| -- | **Agent & Data Governance** (NEW) |
| Architecture Training | Architecture Training (extended with AI literacy) |
| Communication & Change Management | Communication & Change Management |
| Architecture Compliance Evaluation | Architecture Compliance Evaluation (extended to **continuous, machine-assisted**) |
| Architecture Review Board | Architecture Review Board (extended with AI expertise and **automated pre-screening**) |

**Three critical evolutions:**

1. **Guardrails become a first-class governance concept.** Unlike traditional policies that humans interpret, guardrails are machine-enforceable boundaries that constrain agent behaviour in real-time. They define what an agent is allowed to do, what decisions it can make autonomously, and when it must escalate to a human. This is governance that operates at the speed of the systems it governs.

2. **Agent & Data Governance** addresses the new accountability questions: Who owns an agent? Who is responsible when an agent makes a wrong decision? How do we audit agent behaviour? How do we ensure data quality for agent consumption? How do we comply with the EU AI Act?

3. **Agent management emerges as a discipline in its own right.** Beyond governance, agents require onboarding (testing, validation, access provisioning), performance monitoring (accuracy, cost, drift detection), and lifecycle management (versioning, retraining, retirement). An organisation running five agents can manage them ad hoc. At fifty, structured processes become necessary. At five hundred -- a scale that several projections place within three to five years for large enterprises -- a formal discipline is needed. No existing framework -- ITIL, HR, or otherwise -- fully addresses these requirements. The Agent Registry is the minimum viable foundation.

---

## Getting started: Six practical steps

1. **Assess your current EA model** -- Map your existing capabilities against the agentic model. Where are the gaps? Where does your current model already cover new requirements, and where does it fall short?

2. **Assess your infrastructure readiness** -- Map each planned AI workload to its compute, network, storage, and integration requirements. Compare against current capacity. The delta is your infrastructure investment gap -- and it is likely larger than your AI team has estimated.

3. **Redesign before you automate** -- Before approving your next AI agent deployment, verify that the target process has been redesigned for agent strengths, not just automated as-is. Invest in process mining and quantitative process understanding first.

4. **Build an Agent Registry** -- Start cataloguing AI agents in your organisation. Many already exist in shadow IT. Make them visible. For every agent, document its role, autonomy level, access permissions, data inputs, model dependencies, decision authority, and accountable human owner.

5. **Extend your governance for speed and scope** -- Add guardrails to your architecture principles and codify them for machine enforcement. Measure your governance cycle time: if it exceeds your deployment cadence, automate the routine decisions and reserve human review for exceptions.

6. **Invest in Data & Knowledge architecture** -- This is the foundation. Agents without quality data and well-structured knowledge are powerful but directionless. Start with the knowledge assets, metadata structures, and ontologies that agents will need to reason effectively -- and design in sovereignty from day one.

---

## Conclusion

Enterprise Architecture must evolve -- not just in what it covers, but in how it operates. The shift is from a planning discipline to one that enables, orchestrates, and governs autonomous agents -- at the speed those agents demand.

The classic model with its four domains served us well for two decades. The refocused model -- with Business, Agents & Apps, and Data & Knowledge as the three strategic domains -- reflects where enterprise IT is heading. It is a first proposal, and it will evolve. In practice, we will use both models side by side, wherever each fits best.

The question is no longer: *"How do we manage our IT landscape?"* It is: ***"How do we architect an enterprise where humans and autonomous agents collaborate to create value?"***

Organisations that answer this question early will have a significant advantage -- not because they have more agents, but because their agents operate within a well-designed architecture: effectively, safely, and in service of clear business goals.

**This model is a starting point for that conversation. We invite you to challenge it.**

---

*[Author information] [Contact details] [PwC Switzerland branding]*

---

## Notes for internal review

### Changes from v1

- Technology section now acknowledges the infrastructure readiness gap (only 14% prepared) alongside the "embedded" argument -- positions it as directional, not solved
- Each EA domain now includes an explicit **"What changes"** summary describing concrete shifts
- "Business architecture IS the prompt" is now grounded in the **Enterprise as Code** concept -- from documentation to codification
- Added **process redesign prerequisite** (10/20/70 rule) -- the strongest finding from the underlying research
- Added **multi-agent risk dimension** (cascading failures, non-linear error propagation) to the Agents & Apps section
- Added **model commoditisation and portability** as architectural principles
- Added **agent lifecycle management** as an emerging discipline alongside governance
- Added **AI sovereignty** throughout -- critical for European audience (82% EMEA orgs adjusting cloud approach)
- Added **C-Suite expectation gap** in Business section
- Added **"From code specifications to business specifications"** angle: draws on the pattern that AI in software development is most valuable when guided by specifications, and hypothesises the equivalent for business process architecture
- Reframed "leaner" as **"refocused"** -- new challenges emerge within restructured domains
- Governance section expanded with the **speed paradox**: governance slower than deployment creates risk, not safety
- Practical steps expanded from five to six, adding infrastructure readiness assessment and process redesign
- 12 capabilities now described inline with updated descriptions reflecting new themes

### Tone & positioning

- The article positions PwC Switzerland as thought leader, not just framework provider
- It is deliberately provocative in places (*"Why would applications exist?"*, *"Your business architecture IS the prompt"*) but always balanced with evidence and caveats
- New data points from KPMG, PwC EMEA, Capgemini, and BCG surveys ground the arguments in research
- The practical steps ground the vision in actionable advice

### Suggested visuals

- Classic EA Capability Model (existing slide)
- Agentic EA Capability Model (new slide -- updated to reflect "refocused" framing)
- Side-by-side comparison: what changes in each EA layer (new visual summarising the four "What changes" boxes)
- Optional: The autonomy levels framework (L0-L5) as a simple graphic
- Optional: Governance comparison table (classic vs. agentic)

### Suggested length

- Current draft: ~3,200 words
- Could be shortened to ~2,000 by condensing the "What changes" boxes into bullet lists within each section
- Alternative: split into a two-part series:
  - **Part 1:** The shifts -- what changes in each EA layer (automation to autonomization, the four domain shifts)
  - **Part 2:** The model -- the capability model, governance, and practical steps

### Key phrases for SEO / LinkedIn

- Agentic Enterprise Architecture
- From automation to autonomization
- EA Capability Model
- Agent governance
- Enterprise Architecture for AI agents
- Enterprise as Code
- AI sovereignty
- Infrastructure readiness
- Agent lifecycle management
