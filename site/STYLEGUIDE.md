# Insight Site — Style Guide

## Design Philosophy

Warm, minimal, research-focused. Inspired by Claude.ai's aesthetic: generous whitespace, muted earth-tone palette, subtle interactions, and clear information hierarchy. The site is a tool for consultants — it should feel professional and trustworthy, not flashy.

## Color System

### Base Palette (tokens.css)

| Token | Hex | Usage |
|-------|-----|-------|
| `--color-bg` | `#F5F3EE` | Page background (warm off-white) |
| `--color-sidebar` | `#F0ECE4` | Sidebar background |
| `--color-surface` | `#FFFFFF` | Cards, panels, table backgrounds |
| `--color-text` | `#1B1B18` | Primary text |
| `--color-text-secondary` | `#64635E` | Descriptions, metadata |
| `--color-text-tertiary` | `#9B9A95` | Hints, counts, placeholders |
| `--color-border` | `#E5E2DB` | Input borders, dividers |
| `--color-border-light` | `#EDEAE4` | Card borders, subtle separators |

### Accent / Primary

| Token | Hex | Usage |
|-------|-----|-------|
| `--color-primary` | `#D97757` | Accent (terracotta) — use sparingly |
| `--color-primary-text` | `#B34D2B` | Link text, primary labels |
| `--color-primary-light` | `#FAE6DD` | Selection highlight, primary badge bg |

### Entity Colors

Each data entity type has a consistent color pair (foreground + background):

| Entity | Color | Background | Token prefix |
|--------|-------|------------|-------------|
| Source | `#C4841D` amber | `#FEF3D7` | `--color-source` |
| Extract | `#7C6F9B` purple | `#EEEBF5` | `--color-extract` |
| Claim | `#3B6EC4` blue | `#E3EDF8` | `--color-claim` |
| Finding | `#D97757` terracotta | `#FAE6DD` | `--color-finding` |

### Semantic Colors

| Token | Hex | Usage |
|-------|-----|-------|
| `--color-success` | `#3D8B37` | Positive status, analyzed |
| `--color-warning` | `#C4841D` | Caution, in-progress |
| `--color-error` | `#C62828` | Failed, contradictions |
| `--color-info` | `#3B6EC4` | Informational |

## Typography

- **Font**: Inter (Google Fonts), fallback to system-ui
- **Scale**: xs (12px), sm (13px), base (15px), lg (17px), xl (20px), 2xl (24px), 3xl (32px)
- **Weights**: normal (400), medium (500), semibold (600)
- **Line heights**: tight (1.25) for headings, normal (1.6) for body

### Conventions

- Page titles: `font-size-xl`, `font-weight-semibold`
- Section titles: `font-size-lg`, `font-weight-semibold`
- Table headers: `font-size-xs`, `font-weight-semibold`, uppercase, `letter-spacing: 0.05em`
- Body text: `font-size-sm`, `color-text-secondary`
- Metadata/captions: `font-size-xs`, `color-text-tertiary`

## Spacing

8-point grid via `--space-N` tokens:

| Token | Value | Common usage |
|-------|-------|-------------|
| `--space-1` | 4px | Inline gaps, badge padding |
| `--space-2` | 8px | Small gaps, compact padding |
| `--space-3` | 12px | Standard inner padding, toolbar gaps |
| `--space-4` | 16px | Card gaps, grid gaps, section margin |
| `--space-5` | 20px | Card inner padding, tab bar margin |
| `--space-6` | 24px | Content padding, generous card padding |
| `--space-8` | 32px | Section separators |

## Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `--radius-sm` | 8px | Badges, inputs, small cards |
| `--radius-md` | 12px | Cards, panels, tables |
| `--radius-lg` | 16px | Large containers |
| `--radius-full` | 9999px | Pills, circular elements |

## Shadows

| Token | Usage |
|-------|-------|
| `--shadow-sm` | Default card resting state |
| `--shadow-md` | Card hover state |
| `--shadow-lg` | Modals, popovers (reserved) |

## Components

### Cards

Standard content container used across all pages:

```css
background: var(--color-surface);
border: 1px solid var(--color-border-light);
border-radius: var(--radius-md);
box-shadow: var(--shadow-sm);
/* hover: box-shadow: var(--shadow-md); */
```

### Badges

Inline labels for types, categories, statuses:

```html
<span class="badge badge-{variant}">{text}</span>
```

Variants: `primary`, `success`, `warning`, `info`, `source`, `extract`, `claim`, `finding`

### Category Pills

Horizontal filter navigation (Findings, Sources, Graph pages):

```css
.cat-pill — rounded pill button with count
.cat-pill.active — dark fill (--color-text bg, --color-surface text)
```

Always include count in a `.cat-count` span.

### Toolbars

Shared filter bar pattern:

```html
<div class="toolbar">
  <Icon name="filter" />
  <select>...</select>
  <span class="spacer"></span>
  <span class="toolbar-count">N results</span>
</div>
```

### Tables

Use global `<table>` styles from base.css. Wrap in a container for scroll:

```html
<div class="table-wrap">  <!-- background, border, radius, shadow -->
  <table>...</table>
</div>
```

### Empty States

```html
<div class="empty-state"><p>No data available.</p></div>
```

Centered text, generous padding, secondary color.

## Icons

Custom inline SVGs via `Icon.svelte`. Lucide-inspired designs.

- Default size: 18px (nav), 15px (inline), 11-12px (small indicators)
- Stroke: `currentColor`, width 1.75, round caps/joins
- Nav icons have CSS hover animations (scale, rotate, bounce easing)
- Add `icon-{name}` class automatically for targeted animations

## Interactions

### Transitions

- **Default**: `0.15s` for color, border, shadow
- **Nav icons**: `0.25s cubic-bezier(0.34, 1.56, 0.64, 1)` (bouncy spring)
- **Bar charts**: `0.3s` for width transitions

### Hover Patterns

- Cards: `shadow-sm` -> `shadow-md`
- Nav items: background shift to `--color-sidebar-hover`
- Links: color shift + underline
- Buttons/pills: border-color or background shift

### Active States

- Nav item: `--color-sidebar-active` background
- Tab: bottom border `--color-finding`
- Pill: inverted (dark bg, light text)

## Layout

### Page Structure

```
Sidebar (240px fixed) | Main area (flex: 1)
                        Top bar (56px, title + search)
                        Content (padded, max-width 1400px)
```

### Content Max Width

Default `--max-width: 1400px`. Override with `:global(.content:has(...)) { max-width: none; }` for full-width pages (e.g., Deep Dive).

### Responsive

- Sidebar collapses to 52px on screens < 768px
- Icon-only mode, labels hidden
- Tables get horizontal scroll

## Naming Conventions

- **CSS classes**: kebab-case (`.stat-card`, `.extract-header`)
- **CSS tokens**: `--color-{semantic}`, `--space-{scale}`, `--font-size-{scale}`
- **Component files**: PascalCase (`FindingsView.svelte`)
- **Icon names**: kebab-case (`deep-dive`, `arrow-up`)
- **Entity badges**: `badge-{entity}` matching token prefix
