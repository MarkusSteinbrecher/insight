# Site Backlog

Issues and improvements identified from visual review. Updated 2026-03-08.

## Bugs

- [ ] **Visuals: broken images** — `image_path` in visuals.json points to files that don't exist in `static/data/images/`. Back-end exporter needs to copy/generate the image files.
- [x] ~~**Sources: empty status column**~~ — Fixed: sources.json now includes `status` and `quality_status` fields.
- [ ] **Conclusions: empty page** — Shows "No conclusions available yet." despite `conclusions.json` existing. Likely a data/export issue.
- [x] ~~**Dashboard: missing data**~~ — Fixed: dashboard now shows donut charts, pipeline, top sources. Some stats still depend on data export.

## Completed (2026-03-08)

- [x] **Dashboard enriched** — Donut charts (status + types), pipeline progress, top sources by relevance scoring, key findings
- [x] **Dashboard stat cards link** — Clicking cards navigates to corresponding tab
- [x] **Theme persistence** — Custom themes saved to localStorage with restore-to-default in Style Guide
- [x] **Three color themes** — Warm, Cool, Yello with light/dark mode; entity colors redesigned for distinguishability
- [x] **Dark mode** — Full dark palette for all three themes
- [x] **Radius tokens in Style Guide** — Sliders with descriptions of affected elements
- [x] **Source quality indicators** — `quality_status` column with colored dots, hover tooltips, quality filtering
- [x] **Graph: transitive links** — Shows indirect links through hidden extract nodes
- [x] **Graph: layered layout** — Sources top, claims/extracts middle, findings bottom
- [x] **Graph: source impact sizing** — Node radius proportional to finding-reaching claims
- [x] **Graph: align-by** — Target icon on entity pills to pull type to center
- [x] **Graph: smart extract filtering** — Only shows chain extracts (connected to claims), not 5000+ leaf nodes
- [x] **Graph: theme-aware colors** — Links and nodes read from CSS tokens, update with theme
- [x] **Graph: tooltips on hover** — Shows type + label on hover regardless of selection
- [x] **Graph: stats counter** — Toolbar shows node/link/indirect counts
- [x] **WIP badge** — "Work in progress" next to page title
- [x] **GitHub Pages deployment** — `/insight` base path, visuals excluded from build
- [x] **About page** — Project overview with animated traceability chain SVG, page navigation cards
- [x] **Library (Deep Dive) rename** — Tab label changed, dev-only

## Design Issues

- [ ] **Findings category pills have long labels** — "Strategy & Transformation" wraps awkwardly on smaller screens.
- [ ] **Graph: detail panel shows raw IDs** — Should use `shortId()` formatting (S-001).
- [ ] **Visuals: placeholder icons instead of images** — Need placeholder/fallback treatment.
- [ ] **Topic selector truncated** — Consider tooltip or wider sidebar for long topic names.
- [ ] **No loading states** — Pages flash empty then populate. Should show skeleton/shimmer states.

## Improvements

### High Priority

- [ ] **Add image placeholders on Visuals** — Styled placeholder with visual type icon when images are missing.
- [ ] **Consistent empty states** — All pages should have the same style with helpful messages.

### Medium Priority

- [ ] **Source detail drawer/panel** — Click a source row to see extracts, claims, findings inline.
- [ ] **Graph: zoom controls** — Add +/- buttons and reset-zoom.
- [ ] **Keyboard navigation** — Arrow keys in Deep Dive, Escape to close, Tab through pills.
- [ ] **Search results highlight** — Yellow highlight on matched substring.
- [ ] **Breadcrumb / context indicator** — Active filter indicator on Findings.

### Low Priority

- [ ] **Print stylesheet** — Research reports should be printable.
- [ ] **Export to PDF** — Export finding or full report.
- [ ] **Mobile layout** — Full responsive treatment beyond sidebar collapse.
- [ ] **Accessibility audit** — ARIA labels, focus management, screen reader testing.
- [ ] **Animation: page transitions** — Subtle fade/slide on tab switch.
- [ ] **Favicon** — Create an Insight-branded favicon.

## Technical Debt

- [ ] **Duplicate pill styles** — `.cat-pill` defined in FindingsView, SourcesTable, GraphView. Extract to `base.css`.
- [ ] **Hardcoded colors in Deep Dive** — Should use `var(--color-claim)` tokens in stacked bar chart.
- [ ] **`any` types in components** — Many `$derived` blocks use `(s: any)` instead of typed interfaces.
- [ ] **Graph component is monolithic** — Could split into `GraphCanvas`, `GraphControls`, `GraphDetail`.
