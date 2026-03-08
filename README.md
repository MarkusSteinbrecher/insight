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

- **Dashboard** — overview stats, source breakdown, pipeline progress, and top contributing sources
- **Sources** — sortable table with quality indicators, status tracking, and type/quality filtering
- **Findings** — expandable findings with linked claims, source quotes, and category grouping
- **Graph** — force-directed knowledge graph with layered layout, transitive links, source impact sizing, and align-by controls
- **Conclusions** — recommendations and thought leadership angles backed by the evidence chain
- **About** — project overview with animated traceability chain diagram

Three color themes (Warm, Cool, Yello) with light/dark mode. Theme customization persists via localStorage with restore-to-default.

## Built With

- [SvelteKit](https://kit.svelte.dev/) with Svelte 5 (runes-only)
- [D3.js](https://d3js.org/) for graph visualization
- [KuzuDB](https://kuzudb.com/) embedded graph database
- Static adapter → GitHub Pages (`/insight`)
