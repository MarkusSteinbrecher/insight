Text Box 2, Textbox 

EA: From Automation to Autonomy 

An Enterprise Architecture Capability Model for the Agentic Enterprise 

ABSTRACT: 

Agentic AI is shifting enterprise IT from automation to autonomization – from systems that follow predefined  steps to agents that pursue goals. What does this mean for Enterprise Architecture? We discuss a new, leaner EA Capability Model for the Agentic Enterprise – built on three strategic domains: Business, Agents & Applications, and Data & Knowledge. 

 
From automation to autonomization 

For decades, the logic of enterprise software was simple: humans decide, systems execute. Automation made systems faster and us more efficient. But the fundamental pattern remained — a human defines the steps, a system follows them. 

Agentic AI breaks this pattern. 

An AI agent doesn't follow predefined steps. It pursues goals. It reasons, plans, uses tools, evaluates results, and adapts. It operates with a degree of autonomy that enterprise IT has not seen before. 

This is more than a technological shift. For Enterprise Architects and Technology Leaders designing these systems, the focus changes fundamentally: from automation to autonomization: 

Automation asks: "How do we execute this process faster? What can we automate and integrate?" 

Autonomization asks: "What is the goal? How do we define it clearly enough for an agent to achieve it on its own? And what is it allowed to do — and what not?" 

Automation = programming and integration.  

Autonomization = prompting, orchestrating, and guardrailing. 

If autonomous agents become a primary way of delivering business capabilities, then the very structure of our Enterprise Architecture models needs to evolve. Our own EA capability model is grounded in established frameworks like TOGAF and ArchiMate, built on the classic domains — Technology, Data, Application, and Business — plus a set of common capabilities. It reflects how enterprise IT has traditionally been structured for the past two decades. 

 

What changes in the age of Agentic AI? 

Based on ongoing discussions at PwC Switzerland, we propose a first evolution — not a replacement of established models, but a perspective on how they might adapt. 

Technology becomes embedded 

This is less about Agentic AI and more about trends that have been building for years: cloud, virtualisation, everything-as-a-service, zero trust. 

When infrastructure is consumed as a service — when a development team provisions compute, storage, and networking through a single API call — the architectural significance of modelling systems, networks, and virtualisation separately diminishes rapidly. With zero trust, even the network perimeter loses its relevance — security is no longer a function of topology, but of identity and policy. 

Technology architecture becomes increasingly standardized and embedded in platform choices and cloud configurations, reducing the need to treat it as a separate strategic domain in an EA capability model. 

This is a pragmatic recognition of where enterprise architecture creates the most strategic value today — no longer in server setup and network topologies, but in the design of business capabilities, agents & applications, and the data & knowledge that powers them. 

Will Agents replace Applications? 

In a radical view: yes. Why would there be applications? Humans interact directly with smart, personalized agents. Agents perform all tasks necessary — all they need is data, knowledge, and the help of other specialized agents.  

Consider what today's applications actually are: a user interface, business logic, data access, and integration points — bundled into a package. Now consider what an agent does: it interacts through natural language, reasons about business logic dynamically, accesses data through tools and APIs, and orchestrates across systems natively. 

But this is a direction, not today's reality. Legacy systems will persist for decades. New applications will still be built. And where the same tasks need to be executed efficiently, at high volume, and exactly the same way every time — applications may well keep their place. The architectural centre of gravity, however, is shifting: from applications as the primary execution layer to agents as the primary orchestration layer. 

That's why our new model doesn't separate them. It combines them into one domain: Agents & Applications — because in an agentic enterprise, the boundary between the two will blur beyond distinction. Especially once agents begin generating their own application logic, the two will merge. 

Data gets extended with Knowledge 

Data has gradually moved from a supporting role to centre stage: for decades, data was simply part of applications — stored in application databases, modelled within application logic, owned by application teams. Its emergence as a separate architectural domain reflects a long journey: from data warehousing, to master data management, to data mesh and data products. 

With agents, this trend accelerates. Agents are only as good as the data they can access — and critically, they depend not just on data, but on metadata and knowledge. This includes entirely new architectural concepts: 

Knowledge graphs and ontologies that give agents semantic understanding 

RAG architectures that ground agent responses in organisational knowledge 

Agent memory and context stores that enable agents to maintain state across interactions 

Embeddings and vector databases that make unstructured knowledge searchable 

Metadata — process descriptions, business rules, data lineage — that agents need to operate effectively 

This is why we renamed the domain from "Data Architecture" to Data & Knowledge. It's not just about storing and modelling data anymore.  

It's about curating the metadata and the knowledge fabric that agents reason on. 

Business stays dominant 

While technology fades and applications get absorbed, the Business Architecture domain remains as relevant as ever. Arguably more so. 

Agents need clear business intent to function. They need value drivers to understand what matters. Capability definitions to know what the organisation can and should do. Process and interaction models to understand how work flows — and where they fit in. 

The key evolution: capability definitions must now explicitly capture who or what delivers each capability — a human, a system, an agent, or a hybrid. And process models must accommodate goal-driven, non-deterministic flows alongside traditional sequential processes. 

In a fully agentic future, agents may not need applications. But they need metadata: process descriptions, business rules, capability definitions — these become the instructions that agents consume. 

Your business architecture IS the prompt. 

The Agentic EA Capability Model 

Based on these shifts, we have developed an alternative Agentic EA Capability Model: leaner and more structured, reduced from 18 to 12 capabilities, with a clear dual logic: 

Vertically, four domains: Common, Business, Agents & Apps, and Data & Knowledge 

Horizontally, three phases: Define (the what), Architect (the how), and Transform (the where to) 

The Technology domain is integrated into platform choices and cloud configuration. The Application domain has merged with Agents into a combined domain. Data has been extended with Knowledge. And Business remains the anchor. 

 This model is a starting point, not a final answer. We invite the EA community to challenge and evolve it with us. And in practice, both models will coexist — the classic for today's landscapes, the agentic for where we're heading.  

EA Management, Governance and Repository 

Architecture development is only one part of the picture. An enterprise also needs capabilities for EA management, the maintenance of the EA repository, and governance. Management and repository don't change fundamentally in an agentic world — but governance does. 

Two critical additions: Guardrails — machine-enforceable boundaries that constrain agent behaviour in real-time — become a first-class governance concept. And Agent & Data Governance addresses the new accountability questions: who owns an agent, who is responsible for its decisions, and how do we ensure compliance. 

 

 

Conclusion 

Enterprise Architecture must evolve — from a planning discipline to one that both enables and governs autonomous agents. 

The classic model with its four domains served us well for two decades. The new model — with Business, Agents & Apps, and Data & Knowledge as the three strategic domains — reflects where enterprise IT is heading. It is a first proposal, and it will evolve. In practice, we will use both models side by side, wherever each fits best. 

The question is no longer: "How do we manage our IT landscape?" It is: "How do we architect an enterprise where humans and autonomous agents collaborate to create value?" 

Organisations that answer this question early will have a significant advantage — not because they have more agents, but because their agents operate within a well-designed architecture: effectively, safely, and in service of clear business goals. 

This model is a starting point for that conversation. We invite you to challenge it. 

 

 

OLD TEXT & FRAGMENTS 

The vertical logic: Four dimensions 

Dimension 

Purpose 

Common 

Overarching architecture capabilities that apply across all dimensions 

Business 

Defining and structuring business intent, value, and processes 

Agents & Apps 

Designing, architecting, and validating the autonomous execution layer 

Data & Knowledge 

Modelling, structuring, and governing the knowledge fabric 

The horizontal logic: Define → Architect → Transform 

Every dimension follows the same left-to-right progression: 

Step 

Question 

Activity 

Define 

What are the core elements? 

Identify and define the fundamental building blocks 

Architect 

How do they relate and work together? 

Model the structures, relationships, and patterns 

Transform 

Where are we going and how do we get there? 

Plan the evolution, validate readiness, drive change 

This creates a clean, intuitive 4×3 matrix: 

[Insert Agentic Model graphic] 

Shape 

The 12 capabilities explained 

Common 

Define 

Architect 

Transform 

Architecture Vision Development 

Architecture View Creation 

Transformation Planning 

Define the architectural ambition, including the target level of agent autonomy and the role of AI in the future enterprise 

Create architectural views and representations that make complexity manageable – including new views like Agent Landscape Maps and Decision Authority Matrices 

Plan the transformation from current to future state – roadmaps, migration paths, transition architectures 

Business 

Define 

Architect 

Transform 

Strategic Value Driver Definition 

Capability Definition 

Process & Interaction Modelling 

Identify what drives business value – including AI-enabled value streams and agent-driven efficiency gains 

Define business capabilities and explicitly map whether each is delivered by humans, systems, agents, or hybrids 

Model business processes and human-agent interaction patterns – from sequential workflows to goal-driven, adaptive flows 

Agents & Apps 

Define 

Architect 

Transform 

Agent & Application Definition 

Agent & Application Architecture Modelling 

Agent & Application Validation & Testing 

Catalogue all agents and applications. Define agent types, autonomy levels (L0–L5), tool access, and ownership. This is the new "Application Portfolio" – extended with agent metadata 

Model how agents and applications are structured, how they integrate, how they communicate (agent-to-agent, agent-to-system, agent-to-human), and which LLMs and tools they use 

Validate that agent architectures meet requirements. Test agent behaviour against guardrails. Plan releases and migrations from legacy applications to agent-based solutions 

Data & Knowledge 

Define 

Architect 

Transform 

Data & Knowledge Asset Definition 

Data & Knowledge Architecture 

Data Flow & Pipeline Modelling 

Identify and define data objects, knowledge assets, ontologies, metadata structures, and the content that agents will consume 

Design the overall data and knowledge architecture – including knowledge graphs, RAG architectures, vector stores, agent memory, and traditional data models 

Model how data and knowledge flows through the landscape – ETL/ELT pipelines, AI training pipelines, prompt chains, reasoning traces, and feedback loops 

 

 

 

 

 

(older fragments – DO NOT CONSIDER – maybe still integrated later …) 

What about Governance? 

Architecture development is only half the picture. The model's governance layer – Architecture Governance, Communication & Change – evolves significantly: 

Classic 

Agentic 

Standards, Policies, Principles, Guidelines 

Standards, Policies, Principles, Guidelines, & Guardrails 

– 

Agent & Data Governance (NEW) 

Architecture Training 

Architecture Training (extended with AI literacy) 

Communication & Change Management 

Communication & Change Management 

Architecture Compliance Evaluation 

Architecture Compliance Evaluation (extended to real-time) 

Architecture Review Board 

Architecture Review Board (extended with AI expertise) 

Two critical additions: 

Guardrails become a first-class governance concept. Unlike traditional policies that humans interpret, guardrails are machine-enforceable boundaries that constrain agent behaviour in real-time. They define what an agent is allowed to do, what decisions it can make autonomously, and when it must escalate to a human. 

Agent & Data Governance addresses the new accountability questions: Who owns an agent? Who is responsible when an agent makes a wrong decision? How do we audit agent behaviour? How do we ensure data quality for agent consumption? How do we comply with the EU AI Act? 

Shape 

The role of the Enterprise Architect evolves 

This new model doesn't just change boxes on a chart. It changes what it means to be an Enterprise Architect: 

Classic role 

Agentic role 

Blueprint designer 

Ecosystem shaper 

Technology standardiser 

Agent boundary designer 

Governance enforcer 

Guardrail architect 

Documentation author 

Behaviour modeller 

Periodic reviewer 

Continuous monitor 

The Enterprise Architect of the future doesn't primarily design systems. They design the rules of the game within which autonomous agents operate. 

Shape 

Getting started: Five practical steps 

Assess your current EA model – Map your existing capabilities against the agentic model. Where are the gaps? 

Build an Agent Registry – Start cataloguing AI agents in your organisation. Many already exist in shadow IT. Make them visible. 

Define autonomy levels – Not every agent needs full autonomy. Create an autonomy framework (L0: human-controlled → L5: fully autonomous) and assign levels deliberately. 

Extend your governance – Add guardrails to your architecture principles. Define who can deploy agents and under what conditions. 

Invest in Data & Knowledge architecture – This is the foundation. Agents without quality data and well-structured knowledge are powerful but directionless. 

Shape 

Shape 

[Author information] [Contact details] [PwC Switzerland branding] 

Shape 

Notes for internal review 

Tone & positioning 

The article positions PwC Switzerland as thought leader, not just framework provider 

It's deliberately provocative in places ("Why would applications exist?") but always balanced ("this won't happen overnight") 

The practical steps at the end ground the vision in actionable advice 

Suggested visuals 

Classic EA Capability Model (existing slide) 

Agentic EA Capability Model (new slide) 

Optional: Side-by-side comparison showing what changed 

Optional: The autonomy levels framework (L0–L5) as a simple graphic 

Suggested length 

Current draft: ~2,000 words 

Recommended for PwC blog: Could be shortened to ~1,500 or split into a two-part series: 

Part 1: The shifts (Automation → Autonomization, what changes) 

Part 2: The model (the new capability model in detail) 

Key phrases for SEO / LinkedIn 

Agentic Enterprise Architecture 

From automation to autonomization 

EA Capability Model 

Agent governance 

Enterprise Architecture for AI agents 

 

 
