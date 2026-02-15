---
title: "A Roadmap for Scaling AI Agents in the Modern Enterprise"
url: "https://www.pwc.ch/en/insights/digital/scaling-ai-agents.html"
author: "Sebastian Ahrens, Lilia Christofi, Johnny Chivers, Aidan Caffrey (PwC Switzerland / PwC UK)"
date: "2025-06-02"
type: article
relevance: 5
tags:
  - agentic-ai
  - event-driven-architecture
  - Kafka
  - BPMN
  - scalability
  - regulatory-compliance
  - PwC
---

## Summary

PwC Switzerland proposes an event-driven architecture combining Apache Kafka messaging with BPMN-based process orchestration (e.g., Camunda 8/Zeebe) to overcome enterprise AI agent scaling challenges. The architecture addresses three key challenges: state management across multiple agents, scalability bottlenecks from synchronous integrations, and regulatory compliance requiring transaction auditability and explainability.

Core design principles: loose coupling (agents subscribe to Kafka topics, process events, publish results), independent scaling (components scale based on throughput without affecting the system), separation of concerns (BPMN manages process logic while AI agents focus on analysis), and fault tolerance (event logs enable recovery and replay).

Three case studies illustrate the architecture: conversational AI at scale (Azure Speech Services processing thousands of concurrent sessions), direct voice-to-voice AI (Google WaveNet, OpenAI Whisper, Meta SeamlessM4T with Redis for session memory), and regulatory compliance in banking (Basel III/IV reporting with fully auditable pipeline, Kubernetes auto-scaling).

A technology decision matrix covers nine components: Apache Kafka (event bus), Kafka Streams (real-time transformation), Camunda 8/Zeebe (BPMN orchestration), Apache Flink (stateful event processing), Redis + Streams (in-memory caching), ClickHouse/PostgreSQL (auditing), Ray Serve (distributed inference), Hugging Face Endpoints (model deployment), and ONNX Runtime (model optimization).

## Key Takeaways

- Event-driven architecture (Kafka + BPMN) recommended for scaling AI agents
- Loose coupling enables independent optimization of AI tasks and compliance steps
- Three case studies: conversational AI, voice-to-voice AI, banking compliance
- Nine-component technology decision matrix for implementation
- Separation of concerns: BPMN for process logic, AI agents for analysis
- Redis for session state management in conversational systems
- Fully auditable event trails required for regulatory compliance
