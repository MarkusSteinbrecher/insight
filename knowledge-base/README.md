# Knowledge Base

Structured research repository for Technology and AI topics.

## Structure

```
knowledge-base/
├── topics/                        # One directory per research topic
│   └── {topic-slug}/
│       ├── _index.md              # Topic metadata
│       ├── sources/               # Web research source notes
│       │   ├── source-001.md
│       │   └── ...
│       ├── insights/              # Extracted insights and analysis
│       │   ├── insight-001.md
│       │   └── ...
│       └── synthesis.md           # Comprehensive synthesis
└── connections/
    └── graph.md                   # Cross-topic relationship map
```

## Topic Lifecycle

1. **Researching** — `/research <topic>` creates the topic directory and gathers sources
2. **Analyzed** — `/analyze <topic>` extracts insights from collected sources
3. **Synthesized** — `/synthesize <topic>` creates a comprehensive synthesis document
4. **Active** — Topic is being used for content creation

## File Formats

### Topic `_index.md`
```yaml
---
title: "Topic Title"
slug: topic-slug
status: researching | analyzed | synthesized | active
created: 2024-01-15
updated: 2024-01-15
tags: [tag1, tag2]
related_topics: [other-topic-slug]
---

Brief description of the topic and research focus.
```

### Source Note (`sources/source-NNN.md`)
```yaml
---
title: "Source Title"
url: https://example.com/article
author: "Author Name"
date: 2024-01-10
type: article | report | paper | blog | video | podcast
relevance: 4  # 1-5 scale
---

## Key Takeaways
- Takeaway 1
- Takeaway 2

## Notable Quotes
> "Quote from the source" — Author

## Data Points
- Statistic or data point

## Notes
Additional observations.
```

### Insight (`insights/insight-NNN.md`)
```yaml
---
claim: "The core claim or finding"
confidence: low | medium | high
type: pattern | contradiction | gap | trend | evidence
sources: [source-001, source-003]
---

## Evidence
Supporting evidence for this insight.

## Implications
What this means for the field.
```
