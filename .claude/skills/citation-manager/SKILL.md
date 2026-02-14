# Citation Manager Skill

## Activation

This skill is auto-triggered when writing content that references sources from the knowledge base.

## Citation Styles by Content Type

### Blog Posts — Inline Hyperlinks
Use descriptive anchor text linked directly to the source URL:
```markdown
According to [a recent Gartner report](https://example.com/report), 60% of enterprises...
```

### POVs/Whitepapers — Numbered Endnotes
Use numbered references in the text with a bibliography section at the end:
```markdown
Enterprise adoption of AI agents has accelerated significantly [1], though concerns
about reliability persist [2].

---

## References

[1] Smith, J. "AI Agent Adoption in the Enterprise." Gartner, March 2024. https://example.com/report
[2] Chen, L. "Reliability Challenges in Autonomous AI Systems." ACM, June 2024. https://example.com/paper
```

### Presentations — Slide Footnotes
Brief attribution at bottom of relevant slides:
```markdown
Source: Gartner, "AI Agent Adoption in the Enterprise," March 2024
```

### LinkedIn Posts — Inline Attribution
Minimal attribution woven into the text:
```markdown
Gartner reports that 60% of enterprises are now piloting AI agents...
```

### Executive Briefs — Footnotes
Numbered footnotes with abbreviated citations:
```markdown
AI agent adoption grew 40% YoY.¹

---
¹ Gartner, March 2024
```

## Behaviors

1. **Source Verification**: Before citing a source, verify it exists in `knowledge-base/topics/{topic}/sources/`. If not, flag it.
2. **Attribution Format**: Use the appropriate format for the content type being created.
3. **Bibliography Generation**: For endnote-style content, generate a complete bibliography section sorted by reference number.
4. **Cross-Reference Check**: When multiple sources support a claim, cite the most authoritative or recent one primarily, and note supporting sources.
5. **Quote Attribution**: Direct quotes must include author name and source title.

## Source Quality Hierarchy

When multiple sources are available, prefer (in order):
1. Primary research / original data
2. Peer-reviewed publications
3. Industry analyst reports (Gartner, Forrester, McKinsey, etc.)
4. Official documentation / technical blogs from vendors
5. Reputable tech journalism (InfoQ, The New Stack, etc.)
6. Blog posts from recognized practitioners
7. Social media / informal sources

## Reference Format Templates

See `references/citation-formats.md` for detailed format templates.
