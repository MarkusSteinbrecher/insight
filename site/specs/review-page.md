# Spec: Source Extraction Review Page — Front-end

**Status:** Proposed
**Priority:** High
**Type:** Dev-only feature (`import.meta.env.DEV`)
**Companion spec:** `~/Code/insight-private/design/specs/review-tool.md` (back-end)

## Problem

Researchers need to validate that source content was correctly extracted by the analysis pipeline. Currently there's no way to see what was extracted from each source, identify gaps or errors, and provide structured feedback.

## Solution

A dev-only **Review** tab in the SvelteKit site with two views:

1. **Source list** — all sources with review status, filterable
2. **Review page** — three-panel layout for side-by-side validation

## Data Source

The back-end exporter generates:

```
site/static/data/{topic}/
  review.json                    # Source index with metadata
  review/
    source-001.json              # Full blocks + extracts per source
    source-004.json
    ...
    documents/                   # PDFs (gitignored, local only)
      source-001.pdf
    feedback/                    # Written by this page (gitignored)
      source-001.json
      source-004.json
```

### review.json (index)

```json
{
  "topic": "ea-for-ai",
  "generated": "2026-03-09",
  "sources": [
    {
      "source_id": "ea-for-ai:source-004",
      "title": "From AI Pilots to Production Reality",
      "url": "https://...",
      "type": "web",
      "status": "extracted",
      "block_count": 115,
      "extract_count": 124,
      "noise_count": 12,
      "quality_status": "ok"
    }
  ]
}
```

### review/source-{NNN}.json (per source)

```json
{
  "source_id": "ea-for-ai:source-004",
  "title": "From AI Pilots to Production Reality",
  "url": "https://...",
  "type": "web",
  "document_path": null,
  "content_blocks": [
    {
      "block_id": "ea-for-ai:source-004:block-001",
      "position": 1,
      "text": "A Beginning-of-Year Reflection...",
      "format": "heading",
      "section_path": "",
      "image_path": null,
      "extracted_as": ["ea-for-ai:source-004:extract-001"]
    }
  ],
  "extracts": [
    {
      "extract_id": "ea-for-ai:source-004:extract-001",
      "position": 1,
      "text": "A Beginning-of-Year Reflection...",
      "extract_type": "context",
      "section_path": "",
      "claims": ["ea-for-ai:cc-018"]
    }
  ]
}
```

## Page Structure

### Route: `/review`

Dev-only (gated behind `import.meta.env.DEV`). Add to nav with `devOnly: true`.

### Source list view (`/review`)

Table of all sources with:

| Column | Source |
|--------|--------|
| ID | Short format (S-004) |
| Title | Clickable, links to review page |
| Type | web / pdf / youtube icon |
| Blocks | Count |
| Extracts | Count |
| Noise | Count (red if high) |
| Quality | Status dot (reuse from Sources tab) |
| Review | Status badge: Not reviewed / In progress / Approved / Needs refinement |

- Review status read from `localStorage` (keyed by source_id)
- Sortable columns, filter by type / quality / review status
- "Export All Feedback" button (downloads combined JSON)

### Review page (`/review/{source_id}`)

Three-panel layout, resizable:

#### Panel 1: Original Source (left, ~40%)

- **Web sources**: `<iframe src="{url}">` with fallback message if blocked by X-Frame-Options. "Open in new tab" link always visible.
- **PDF sources**: `<embed src="/data/{topic}/review/documents/{filename}.pdf" type="application/pdf">`. Fallback: download link.
- **YouTube**: `<iframe src="https://www.youtube-nocookie.com/embed/{video_id}">` extracted from URL.

#### Panel 2: Content Blocks (center, ~30%)

Reconstructed source content from `content_blocks[]`, styled by `format`:

| Format | Rendering |
|--------|-----------|
| `heading` | `<h3>` or `<h4>` |
| `prose` | `<p>` |
| `bullet` | `<li>` in `<ul>` |
| `quote` | `<blockquote>` |
| `table_row` / `table_cell` | `<table>` |
| `figure` | `<img>` with alt text |
| `caption` | `<figcaption>` |

**Color coding** based on `extracted_as[]`:
- **Green left border**: block was extracted (has entries in `extracted_as`)
- **No highlight**: block was skipped (potential gap — clickable to flag as missing)
- **Red left border**: block was extracted as `noise` type

Clicking a block scrolls to its extract in Panel 3. Clicking an un-extracted block opens a "Flag missing" form.

#### Panel 3: Extracts (right, ~30%)

Ordered by `position`. Each extract card shows:

- **Type badge** (color-coded): claim, evidence, context, recommendation, noise, etc.
- **Section path** breadcrumb (muted)
- **Text** (editable on double-click or edit button)
- **Linked claims** as pills (if any)
- **Actions**: Edit text, Change type (dropdown), Delete, Add comment

Clicking an extract highlights its matched block(s) in Panel 2.

### Toolbar

- Source title + metadata
- Navigation: Previous / Next source buttons
- Status: dropdown to set review status (Not reviewed / In progress / Approved / Needs refinement)
- Save button (saves feedback to localStorage + triggers file write)
- "View Original" button (opens source URL in new tab)

## Feedback Mechanism

### Storage

Feedback is stored in **two places**:

1. **localStorage** — immediate persistence, survives page refreshes
2. **File on disk** — via SvelteKit dev-only server route

### SvelteKit server route (dev-only)

```
src/routes/api/review/feedback/+server.ts
```

- `POST` — receives feedback JSON, writes to `static/data/{topic}/review/feedback/{source-short}.json`
- `GET` — reads existing feedback for a source (if file exists)
- Only active in dev mode (`import.meta.env.DEV` check)

```typescript
// +server.ts
import { dev } from '$app/environment';
import { json, error } from '@sveltejs/kit';
import { writeFileSync, readFileSync, existsSync, mkdirSync } from 'fs';
import { join } from 'path';

export async function POST({ request }) {
    if (!dev) throw error(404);

    const feedback = await request.json();
    const sourceShort = feedback.source_id.split(':').pop(); // "source-004"
    const dir = join('static/data', feedback.topic, 'review/feedback');
    mkdirSync(dir, { recursive: true });
    writeFileSync(join(dir, `${sourceShort}.json`), JSON.stringify(feedback, null, 2));

    return json({ ok: true });
}
```

### Feedback JSON format

```json
{
  "source_id": "ea-for-ai:source-004",
  "topic": "ea-for-ai",
  "reviewed_at": "2026-03-09T14:30:00Z",
  "status": "needs-refinement",

  "extract_feedback": [
    {
      "extract_id": "ea-for-ai:source-004:extract-005",
      "action": "reclassify",
      "original_type": "claim",
      "revised_type": "context",
      "comment": "Background info, not a claim"
    },
    {
      "extract_id": "ea-for-ai:source-004:extract-012",
      "action": "edit",
      "revised_text": "Corrected text here...",
      "comment": "Was cut off mid-sentence"
    },
    {
      "extract_id": "ea-for-ai:source-004:extract-020",
      "action": "delete",
      "comment": "Cookie consent boilerplate"
    }
  ],

  "missing_content": [
    {
      "block_ids": ["ea-for-ai:source-004:block-045"],
      "suggested_type": "evidence",
      "comment": "Case study was missed"
    }
  ],

  "source_comments": [
    "Overall good but too many noise extracts from sidebar"
  ]
}
```

### Action types for extract_feedback

| Action | Fields | Meaning |
|--------|--------|---------|
| `reclassify` | `original_type`, `revised_type` | Change extract type |
| `edit` | `revised_text` | Fix extract text |
| `delete` | — | Mark for removal |
| `split` | `split_at` (char index) | Split into two extracts |
| `merge` | `merge_with` (extract_id) | Combine with another extract |
| `flag` | — | Flag for agent review without specific fix |

## Gitignore additions

Add to public repo `.gitignore`:

```
# Review tool (dev-only, generated by back-end)
site/static/data/*/review/
```

## Component structure

```
site/src/
  routes/
    review/
      +page.svelte              # Source list
      +page.ts                  # Load review.json
      [source_id]/
        +page.svelte            # Review page (3-panel)
        +page.ts                # Load source-NNN.json
    api/
      review/
        feedback/
          +server.ts            # POST/GET feedback (dev-only)
  lib/
    components/
      ReviewSourceList.svelte   # Source list table
      ReviewPanel.svelte        # 3-panel layout container
      OriginalContent.svelte    # iframe/embed/player
      ContentBlocks.svelte      # Reconstructed blocks with highlights
      ExtractList.svelte        # Extract cards with actions
      ExtractCard.svelte        # Single extract with edit/reclassify/delete
      FeedbackForm.svelte       # Comment and missing content forms
```

## Acceptance criteria

1. `/review` page appears in nav only during `npm run dev`
2. Source list loads from `review.json`, shows all sources with review status
3. Clicking a source opens the three-panel review page
4. Original source displayed correctly for web (iframe), PDF (embed), YouTube (player)
5. Content blocks rendered with extraction-status highlighting
6. Extract cards show type, text, section path, and linked claims
7. Double-click extract text to edit inline
8. Type dropdown allows reclassification
9. Delete button marks extract for removal
10. Clicking un-extracted block opens "flag missing" form
11. Save writes feedback JSON via dev-only server route
12. Previous/Next navigation between sources
13. Review status persisted in localStorage and shown on source list
14. "Export All Feedback" downloads combined JSON

## Non-goals (v1)

- No real-time re-extraction (batch via back-end `/refine`)
- No diff view between original and edited text
- No multi-user collaboration
- No annotation overlay on the iframe/PDF (too complex for v1)
