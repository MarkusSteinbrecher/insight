# Knowledge Base Management Skill

## Activation

This skill is auto-triggered when working with files under `knowledge-base/`.

## Conventions

### Topic Slugs
- Lowercase, hyphens only, no special characters
- Examples: `ai-agents-enterprise`, `llm-fine-tuning`, `platform-engineering`

### Topic `_index.md` Format
```yaml
---
title: "Human-Readable Topic Title"
slug: topic-slug
status: researching | analyzed | synthesized | active
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [tag1, tag2, tag3]
related_topics: [other-topic-slug]
source_count: 0
insight_count: 0
---

Brief description of the research focus and scope for this topic.
```

### Source Note Format (`sources/source-NNN.md`)

For web-researched sources:
```yaml
---
title: "Source Title"
url: https://example.com/article
author: "Author Name"
date: YYYY-MM-DD
type: article | report | paper | blog | video | podcast | documentation
relevance: 4  # 1-5 scale (5 = highly relevant)
---
```

For ingested documents (PDFs, uploaded files):
```yaml
---
title: "Source Title"
document: "filename.pdf"  # References file in documents/ folder
author: "Author Name"
date: YYYY-MM-DD
type: pdf | report | paper | presentation | spreadsheet
relevance: 4  # 1-5 scale (5 = highly relevant)
---
```

Both formats share the same body structure:
```markdown
## Key Takeaways
- Takeaway 1
- Takeaway 2
- Takeaway 3

## Notable Quotes
> "Direct quote from the source" — Author Name

## Data Points
- Specific statistic or data point with context

## Notes
Additional context, observations, or connections to other sources.
```

### Insight Format (`insights/insight-NNN.md`)
```yaml
---
claim: "A clear, specific claim or finding"
confidence: low | medium | high
type: pattern | contradiction | gap | trend | evidence
sources: [source-001, source-003]
---

## Evidence
Detailed supporting evidence drawn from the referenced sources.

## Implications
What this insight means for practitioners, strategists, or the industry.

## Questions
Open questions raised by this insight.
```

### Synthesis Format (`synthesis.md`)
```yaml
---
title: "Synthesis: Topic Title"
date: YYYY-MM-DD
sources_analyzed: N
insights_extracted: N
---

## Executive Summary
2-3 paragraph overview of the topic landscape.

## Key Themes
### Theme 1: Title
Description and supporting evidence.

### Theme 2: Title
Description and supporting evidence.

## Consensus Areas
Points of broad agreement across sources.

## Active Debates
Areas of disagreement or tension.

## Knowledge Gaps
Questions that current sources don't adequately address.

## Thought Leadership Angles
Promising angles for original content — non-obvious insights, contrarian positions, or synthesis across themes.

## Bibliography
Numbered list of all sources with full attribution.
```

## Behaviors

1. **Creating a topic**: Generate slug from title, create directory with `_index.md`, empty `documents/`, `sources/`, and `insights/` directories
2. **Adding sources**: Use sequential numbering (source-001, source-002, etc.), update `source_count` in `_index.md`
3. **Adding insights**: Use sequential numbering (insight-001, insight-002, etc.), update `insight_count` in `_index.md`
4. **Status transitions**: Update `status` and `updated` date in `_index.md` when stage completes
5. **Cross-references**: When a source or insight relates to another topic, note it in the `related_topics` field of `_index.md`

## Taxonomy Reference

See `references/taxonomy.md` for the full topic taxonomy.
