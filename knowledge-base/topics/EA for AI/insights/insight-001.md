---
title: "The Enterprise AI Readiness Gap: Near-Universal Adoption, Minimal Architectural Preparedness"
type: evidence
confidence: high
sources:
  - source-001
  - source-003
tags:
  - enterprise-architecture
  - AI-readiness
  - infrastructure
  - data-architecture
  - adoption-gap
created: 2026-02-14
---

## Insight

A striking and well-evidenced contradiction defines the current state of enterprise AI: while adoption is near-universal, the underlying enterprise architectures are overwhelmingly unprepared to support AI workloads at scale. The Economist Impact/Databricks survey (source-003) provides the strongest quantitative evidence for this gap, finding that 85% of organisations are using GenAI in at least one business function (97% among enterprises with revenue over US$10bn), yet only 22% say their current architecture can support AI workloads without modification. This is not merely a technology gap -- it is an architectural one. Nearly half (48%) of data engineers spend most of their time resolving data source connections, pointing to fundamental plumbing problems that no amount of AI model sophistication can overcome.

Kumar's academic framework (source-001) corroborates this gap from a design perspective, arguing that 80-90% of enterprise data is unstructured and that traditional architectures were never built to handle the event-driven, real-time, multi-agent workloads that AI-native systems demand. The convergence of these two very different sources -- one a large-scale industry survey, the other a technical architecture proposal -- strengthens the claim that the readiness gap is real and structural, not merely a matter of incremental upgrades. The Economist Impact data further specifies the most critical infrastructure gaps: real-time data processing (47%), robust data pipelines (42%), and security (39%).

This readiness gap has direct strategic implications. Only 37% of executives (and just 29% of practitioners) believe their GenAI applications are production-ready, suggesting that the gap between experimentation and enterprise-grade deployment is where most organisations are stuck. The evidence points to a systemic underinvestment in foundational data infrastructure -- the "Victorian-era plumbing" metaphor used by the Economist report -- even as AI spending grew over 6x from 2023 to 2024.

## Supporting Evidence

- 85% of organisations actively use GenAI in at least one business function; 97% among companies with revenue over US$10bn (source-003, survey of 1,100 respondents across 19 countries)
- Only 22% of organisations say their current architecture can support AI workloads without modifications (source-003)
- Only 37% of executives believe their GenAI applications are production-ready; 29% among practitioners (source-003)
- 48% of data engineers spend most of their time resolving data source connections (source-003)
- Top architecture capability gaps: real-time data processing (47%), robust data pipelines (42%), security (39%) (source-003)
- 80-90% of enterprise data is unstructured, requiring new architectural approaches (source-001, citing industry data)
- AI spending grew over 6x from 2023 to 2024 (source-001, citing McKinsey)
- 65% of businesses report regularly using AI in operations as of 2024, nearly double the percentage ten months prior (source-001, citing McKinsey)
- "You can have all the AI in the world, but if it's on a shaky data foundation, then it's not going to bring you any value." -- Carol Clements, JetBlue (source-003)

## Evidence Assessment

This insight rests on **strong evidence**. The Economist Impact/Databricks survey (source-003) provides the most robust data: a sample of 1,100 respondents across 19 countries and 8 industries, supplemented by 28 C-suite interviews. The survey methodology is transparent, the sample is large and geographically diverse, and the findings are internally consistent. The McKinsey statistics cited in source-001 (65% adoption, 6x spending growth) corroborate the adoption figures from an independent source.

The main limitation is that the Economist Impact report was commissioned by Databricks, which has a commercial interest in enterprises investing in data infrastructure. While this does not invalidate the findings (the methodology appears sound), it suggests the framing may emphasize infrastructure problems that Databricks' products address. The 22% readiness figure should be interpreted carefully -- the definition of "AI-ready architecture" may vary significantly across respondents. Despite these caveats, the convergence of multiple independent data points across two very different source types (industry survey vs. academic paper) makes the overall readiness gap claim highly credible.

## Implications

Enterprise architects and technology leaders should treat AI readiness as primarily an infrastructure and data architecture challenge, not a model selection or AI talent problem. The evidence suggests that the majority of enterprises need to invest in foundational capabilities -- real-time data processing, unified data pipelines, security architectures -- before they can achieve production-grade AI deployment. Organisations that rush to deploy AI models on top of fragmented data architectures risk creating what multiple sources describe as "shaky foundations." The 3+ year ROI timeline cited in the Economist report (source-003) reinforces the need for patient, infrastructure-first investment strategies. Enterprise architecture teams should position themselves as the critical enablers of AI readiness, not as downstream consumers of AI tools.
