---
title: "7 Architecture Considerations for Generative AI"
url: "https://www.accenture.com/us-en/blogs/cloud-computing/7-generative-ai-architecture-considerations"
author: "Accenture (with Atish Ray, Chief AI Architect)"
date: "2023-06-04"
type: article
relevance: 4
tags:
  - generative-ai-architecture
  - foundation-models
  - enterprise-readiness
  - data-architecture
  - responsible-ai
  - accenture
---

## Key Takeaways
- Gen AI fundamentally changes enterprise architecture: instead of hundreds of purpose-built AI models, organizations can fine-tune a small collection of pre-trained foundation models
- Seven key architectural questions: (1) which foundation model, (2) how to access/deploy models, (3) how to adapt models to proprietary data, (4) overall enterprise readiness, (5) environmental impact, (6) how to industrialize Gen AI app development, (7) how to manage the entire Gen AI lifecycle
- Model access has two principal approaches: "full control" (deploy on own infrastructure) vs. "speed and simplicity" (managed cloud service)
- Data adaptation follows "buy, build, or boost" — off-the-shelf with in-context learning, fine-tuning with own data, or building ground-up
- A modern data foundation as part of the enterprise digital core is a prerequisite for extracting value from Gen AI
- Enterprise readiness requires addressing security, reliability, responsibility, integration/interoperability, and trust — including Responsible AI governance
- Environmental impact of AI must be considered upfront, especially for pre-training and fine-tuning at scale
- Industrializing Gen AI requires new frameworks: vector databases, domain knowledge graphs, prompt management, and orchestration layers

## Summary
Written in June 2023 during the early wave of enterprise generative AI adoption, this Accenture article presents seven foundational architectural questions that business leaders must address to scale Gen AI securely, responsibly, and cost-effectively. Accenture's Chief AI Architect Atish Ray frames the core architectural shift: when pre-trained foundation models replace hundreds of purpose-built models, the emphasis shifts from data science to domain expertise, and the architecture must change accordingly.

The seven considerations span the full stack: model selection (pure-play vendors, open source, hyperscaler-hosted), deployment approach (self-hosted vs. managed service), data adaptation strategy ("buy, build, or boost"), enterprise readiness (security, trust, Responsible AI), environmental impact (energy consumption of training and fine-tuning), industrialization of AI app development (vector databases, knowledge graphs, orchestration), and lifecycle management (monitoring, versioning, retraining). Each consideration has distinct architectural implications.

A particularly relevant insight is that enterprise readiness goes beyond technical requirements to encompass trust and Responsible AI governance. The article argues that adopting Gen AI is an ideal time to review overall AI governance standards and operating models. The environmental consideration — often overlooked in enterprise architecture discussions — adds an important sustainability dimension.

## Notable Quotes
> "Like any new foundational technology, you need to make sure you can scale Gen AI securely, responsibly, cost-effectively and in a way that delivers real value to the business." — Atish Ray, Chief AI Architect, Accenture

> "The emphasis shifts from data science to domain expertise. And that's something every successful business has in abundance."

## Relevance to Topic
This article provides a practical, action-oriented framework for enterprise architects evaluating generative AI readiness. The seven-question structure maps well to TOGAF's architecture development method phases and provides concrete decision frameworks for each layer of the AI technology stack. While written early in the Gen AI cycle (June 2023), the fundamental architectural questions remain relevant and have been validated by subsequent enterprise adoption patterns. The "buy, build, or boost" model adaptation framework and the emphasis on modern data foundations as prerequisites are particularly useful for EA practitioners.
