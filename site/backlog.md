# Site Backlog

Issues and improvements identified from visual review (2026-03-08).

## Bugs

- [ ] **Visuals: broken images** — `image_path` in visuals.json points to files that don't exist in `static/data/images/`. Back-end exporter needs to copy/generate the image files. Front-end path fix applied (was double-prefixing).
- [ ] **Sources: empty status column** — `sources.json` lacks `status` field. Needs re-export from back-end after graph DB update. Front-end rendering is ready.
- [ ] **Conclusions: empty page** — Shows "No conclusions available yet." despite `conclusions.json` existing. Likely a data/export issue — needs re-export.
- [ ] **Dashboard: missing data** — "Unique Claims" and "Contradictions" show 0. Either data hasn't been generated or stats.json needs update.

## Design Issues

- [ ] **Dashboard is too sparse** — Only 4 stat cards at the top, rest of page is empty. Should show more: findings summary, source type breakdown, pipeline status overview, recent activity.
- [ ] **Dashboard stat cards don't link anywhere** — Clicking "61 Sources" should navigate to the Sources tab. Same for Findings, Claims.
- [ ] **Inconsistent toolbar patterns** — Sources/Findings use category pills, Graph uses pills + dropdowns, Visuals uses only dropdowns. Should standardize: pills for primary filter, dropdown for secondary.
- [ ] **Findings category pills have long labels** — "Strategy & Transformation" wraps awkwardly on smaller screens. Consider truncation or a max-width.
- [ ] **Graph: no legend** — Node colors (orange=source, blue=claim, terracotta=finding) have no visible legend. The entity pills in the toolbar serve as a partial legend but aren't labeled as such.
- [ ] **Graph: detail panel shows raw IDs** — `ea-for-ai:source-001` should use `shortId()` formatting (S-001).
- [ ] **Visuals: placeholder icons instead of images** — Shows broken image icon where images should be. Need placeholder/fallback treatment.
- [ ] **Topic selector truncated** — Sidebar shows "Enterprise Architecture for .." with ellipsis. Consider tooltip or wider sidebar for long topic names.
- [ ] **No loading states** — Pages flash empty then populate. Should show skeleton/shimmer states during data fetch.

## Improvements

### High Priority

- [ ] **Enrich the Dashboard** — Add: source pipeline funnel (discovered→collected→extracted→analyzed counts), findings by category bar chart, source type distribution, extract type distribution, key metrics trend.
- [ ] **Add image placeholders on Visuals** — Show a styled placeholder with the visual type icon when images are missing, instead of broken img.
- [ ] **Clickable dashboard cards** — Navigate to the relevant tab on click.
- [ ] **Consistent empty states** — All pages should have the same style and include a helpful message about what data is expected.

### Medium Priority

- [ ] **Source detail drawer/panel** — Click a source row to see its extracts, claims, and findings inline (like Deep Dive but lighter).
- [ ] **Finding detail expansion** — Expand a finding to see full claim details with source quotes inline. Currently collapses/expands but could show more context.
- [ ] **Graph: node labels on hover** — Show node title as a tooltip or floating label, not just in the side panel.
- [ ] **Graph: zoom controls** — Add +/- buttons and reset-zoom, not just scroll-to-zoom.
- [ ] **Keyboard navigation** — Arrow keys to move between sources in Deep Dive, Escape to close expanded findings, Tab navigation through pills.
- [ ] **Search results highlight** — When searching, highlight matching text in results (yellow background on matched substring).
- [ ] **Breadcrumb / context indicator** — When filtering by category on Findings, show an active filter indicator that can be dismissed.

### Low Priority

- [ ] **Dark mode** — Define dark token overrides. The warm palette maps well: bg→dark brown, surface→dark gray, text→off-white.
- [ ] **Print stylesheet** — Research reports should be printable. Hide sidebar, nav, search. Use serif font for body text.
- [ ] **Export to PDF** — Let users export a finding or the full report as PDF.
- [ ] **Mobile layout** — Full responsive treatment. Current 768px breakpoint only collapses sidebar. Tables, grids, and the Deep Dive layout need mobile versions.
- [ ] **Accessibility audit** — ARIA labels on icon buttons, focus management for tab switches, screen reader testing.
- [ ] **Animation: page transitions** — Subtle fade/slide when switching tabs (Svelte transition directives).
- [ ] **Favicon** — Currently using default. Create an Insight-branded favicon.

## Technical Debt

- [ ] **Duplicate pill styles** — `.cat-pill` is defined identically in FindingsView, SourcesTable, and GraphView. Extract to `base.css` as a shared component.
- [ ] **Hardcoded colors in components** — Deep Dive uses hex values (`#3B6EC4`, `#C4841D`) instead of CSS tokens. Should reference `var(--color-claim)` etc. in the stacked bar chart.
- [ ] **`any` types in components** — Many `$derived` blocks use `(s: any)` casts instead of proper typed interfaces.
- [ ] **Graph component is monolithic** — `GraphView.svelte` is likely 400+ lines mixing D3 logic, UI, and styles. Could split into `GraphCanvas`, `GraphControls`, `GraphDetail`.
- [ ] **No component documentation** — Each component should have a brief comment block describing its props, data dependencies, and role.
