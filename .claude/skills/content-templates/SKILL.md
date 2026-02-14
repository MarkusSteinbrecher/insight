# Content Templates Skill

## Activation

This skill is auto-triggered when creating content drafts. It provides templates for each content type.

## Available Templates

| Template | File | Target Length |
|----------|------|---------------|
| Blog Post | `templates/blog-post.md` | 1200-2000 words |
| POV/Whitepaper | `templates/pov-whitepaper.md` | 3000-5000 words |
| Presentation Outline | `templates/presentation-outline.md` | 10-15 slides |
| LinkedIn Post | `templates/linkedin-post.md` | 150-300 words |
| Executive Brief | `templates/executive-brief.md` | 1 page |

## Usage

When creating a draft, select the appropriate template and fill in:
1. YAML frontmatter (title, date, tags, topic, etc.)
2. Content sections following the template structure
3. Citations using the citation-manager skill conventions

## Content Quality Guidelines

- **Originality**: Lead with non-obvious insights, not summaries of common knowledge
- **Evidence**: Every major claim should be backed by a source from the knowledge base
- **Voice**: Authoritative but accessible — expert speaking to informed peers
- **Structure**: Clear narrative arc from hook through insight to implication
- **Actionability**: Reader should leave with a changed perspective or clear next step

## Frontmatter Standard

All content files use this base frontmatter:
```yaml
---
title: "Content Title"
date: YYYY-MM-DD
draft: true
type: blog | pov | presentation | linkedin | brief
topic: topic-slug
tags: [tag1, tag2]
summary: "One-sentence summary for SEO and previews"
---
```
