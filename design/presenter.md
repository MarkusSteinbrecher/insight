# Component: Presenter

Parent: [v2 Architecture](v2-architecture.md)
Status: **Design — TODO**

---

## Purpose

Static website with an interactive graph explorer. Renders knowledge graph data for human consumption. Built from JSON exported from the graph at build time. Deployed to GitHub Pages.

## Key Responsibilities

- Graph explorer: interactive visualization of the knowledge graph with traversal
- Findings view: high-level findings with drill-down to evidence chains
- Sources view: source browser with metadata and content block preview
- Claims view: critical analysis with filtering and sorting
- Build pipeline: graph → JSON export → static site

## Topics to Specify

- Framework choice (Svelte vs React vs other)
- Page/view inventory and information architecture
- Graph explorer interaction design (click, filter, traverse, search)
- JSON export format (what queries produce the site data)
- Build and deployment pipeline
- Responsive design requirements
- Accessibility considerations
