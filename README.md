# Insight

Insight is a research analysis tool that helps consultants build defensible, sourced positions on complex topics. It collects sources from across the web, aligns claims across them, and surfaces findings and contradictions — all traceable back to the original source material.

## How It Works

Every insight traces back to a specific location in a specific source:

```
Source → Extract → Claim → Finding → Recommendation
```

- **Sources** are collected from web articles, PDFs, and YouTube videos
- **Extracts** are atomic units of information (assertions, statistics, evidence)
- **Claims** are positions that multiple sources independently support
- **Findings** are higher-level patterns that emerge from related claims
- **Recommendations** are actionable conclusions backed by the evidence chain

## The Dashboard

The interactive dashboard lets you explore the research landscape:

- **Dashboard** — overview stats and key findings
- **Sources** — sortable table of all collected sources
- **Findings** — expandable findings with linked claims and source quotes
- **Graph** — force-directed knowledge graph visualization
- **Deep Dive** — source-by-source inspector with embedded preview and extracts
- **Conclusions** — recommendations and thought leadership angles

## Built With

- [SvelteKit](https://kit.svelte.dev/) with Svelte 5
- [D3.js](https://d3js.org/) for graph visualization
- [KuzuDB](https://kuzudb.com/) embedded graph database
