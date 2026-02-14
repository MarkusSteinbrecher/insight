# Research Agent - Claude Code Project Instructions

## Architecture Overview

This project is a Claude Code-powered system for creating thought leadership content (POVs, presentations, blogs) focused on Technology and AI topics. It consists of four main components:

### 1. Knowledge Base (`knowledge-base/`)
Structured research repository organized by topic. Each topic contains sources (web research notes), insights (extracted analysis), and a synthesis document.

### 2. Content Pipeline (`content/`)
Three-stage pipeline: `ideas/` → `drafts/` → `ready/`. Content moves through stages via commands.

### 3. Hugo Site (`site/`)
Static site published to GitHub Pages. Uses the Paper theme. Content types: blog posts, POVs/whitepapers, about page. Custom pages: Dashboard (knowledge graph), Insights (critical analysis), Sources (table).

### 4. Commands, Agents & Skills (`.claude/`)
- **Commands** (`commands/`): User-invoked slash commands for the workflow pipeline
- **Agents** (`agents/`): Subagent definitions for parallel research and analysis
- **Skills** (`skills/`): Auto-triggered contextual behaviors

## Research Phases

Each topic progresses through four phases. Per-topic progress is tracked in the topic's `_index.md` frontmatter (`phase` and `completed_steps` fields).

### Phase 0 — Data Gathering
Collect raw material from the web and uploaded documents.

| Step | Description | Command | Output |
|------|-------------|---------|--------|
| 0.1 | Web research — search the web, gather 8-12 sources per angle | `/research <topic>` | `sources/source-NNN.md` |
| 0.2 | Document ingestion — process uploaded PDFs/docs into structured source notes | `/ingest <topic>` | `sources/source-NNN.md`, `documents/` |

### Phase 1 — Data Analysis
Structured extraction and cross-referencing of all gathered sources.

| Step | Description | Command | Output |
|------|-------------|---------|--------|
| 1.1 | Raw segmentation — break each source into numbered segments, classify each (claim, statistic, evidence, etc.), calculate composition | `/analyze <topic>` | `raw/source-NNN-raw.yaml` |
| 1.2 | Cross-source claim alignment — deduplicate claims across raw files, identify consensus, unique positions, contradictions | `/analyze <topic>` | `extractions/claim-alignment.yaml` |
| 1.3 | Critical analysis — score each canonical claim (verdict, platitude/actionability/novelty scores, critique) | `/analyze <topic>` | `extractions/critical-analysis-part*.yaml` |
| 1.4 | Cross-source comparison — generate narrative comparison across all sources | `/analyze <topic>` | `extractions/cross-source-analysis.md` |

### Phase 2 — Insight Refinement
Human-in-the-loop refinement and deeper pattern extraction.

| Step | Description | Command | Output |
|------|-------------|---------|--------|
| 2.1 | Interactive discussion — walkthrough critical findings with user, capture decisions | `/discuss <topic>` | `discussion/discussion-YYYY-MM-DD.yaml` |
| 2.2 | Insight extraction — distill patterns, evidence chains, contradictions, knowledge gaps | `/analyze <topic>` | `insights/insight-NNN.md` |
| 2.3 | Synthesis — comprehensive synthesis document with integrated analysis | `/synthesize <topic>` | `synthesis.md` |

### Phase 3 — Conclusion ("So What?")
Take the reader's perspective. The synthesis tells us what the research found — Phase 3 asks what a practitioner should actually *do* about it, what will get in their way, and what positions are worth owning.

| Step | Description | Command | Output |
|------|-------------|---------|--------|
| 3.1 | Reader perspective — review the synthesis as the target audience: what's actionable, what challenges will they face, what's missing for them to act on this? | `/conclude <topic>` | `synthesis.md` (updated with actionability analysis) |
| 3.2 | Recommendations — prioritized, concrete actions for the target audience, sequenced by dependency and effort | `/conclude <topic>` | `synthesis.md` (recommendations section) |
| 3.3 | Thought leadership angles — identify unique perspectives, contrarian positions, and content hooks worth owning | `/conclude <topic>` | `synthesis.md` (angles section) |

### Content Creation (downstream)
Producing deliverables from completed research. Separate from the research phases.

| Step | Description | Command | Output |
|------|-------------|---------|--------|
| Ideation | Generate content ideas from synthesis | `/ideate <topic>` (future) | `content/ideas/` |
| Drafting | Create content draft (blog, POV, presentation) | `/draft <type>` (future) | `content/drafts/` |
| Validation | Run quality/accuracy checklist | `/validate <slug>` (future) | checklist report |
| Publishing | Publish to Hugo site and deploy | `/publish <slug>` (future) | `site/content/` |

### Utility Commands
- `/kb <query>` — Search across the knowledge base
- `/status` — View pipeline dashboard and suggested next actions

## Content Types

| Type | Length | Format |
|------|--------|--------|
| Blog post | 1200-2000 words | Markdown, conversational, SEO-optimized |
| POV/Whitepaper | 3000-5000 words | Structured sections, numbered citations |
| Presentation | 10-15 slides | Outline with speaker notes |
| LinkedIn post | 150-300 words | Short-form, hook-driven |
| Executive brief | 1 page | Summary with key recommendations |

## Key Conventions

### File Formats
- All content files use Markdown with YAML frontmatter
- Topic slugs: lowercase, hyphens, no special characters (e.g., `ai-agents-enterprise`)
- Source notes include: title, URL, author, date, type, relevance (1-5), takeaways, quotes
- Raw documents (PDFs, etc.) go in `knowledge-base/topics/{topic}/documents/` — these are gitignored by default due to size

### Citation Style
- **Blog posts**: Inline hyperlinks `[claim](url)`
- **POVs/Whitepapers**: Numbered endnotes `[1]` with bibliography section
- **All types**: Sources must exist in `knowledge-base/topics/{topic}/sources/`

### Topic Directory Structure
```
knowledge-base/topics/{topic-slug}/
├── _index.md          # Topic metadata (title, status, dates, tags)
├── sources-queue.yaml # User-added web sources awaiting processing
├── documents/         # Raw input files (PDFs, reports, screenshots, etc.)
│   └── ...            # Drop files here manually for processing
├── sources/           # Human-readable source summaries
│   ├── _overview.md   # Source table with metadata, types, institutions
│   ├── source-001.md
│   └── ...
├── raw/               # Full segment-level source breakdowns (Phase 1.1)
│   ├── source-001-raw.yaml
│   ├── source-002-raw.yaml
│   └── ...
├── extractions/       # Cross-source analysis (Phase 1.2+)
│   ├── claim-alignment.yaml   # Cross-source claim deduplication
│   ├── critical-analysis-part*.yaml  # Critical analysis with verdicts
│   └── cross-source-analysis.md
├── insights/          # Distilled insights (Phase 2.2)
│   ├── insight-001.md
│   └── ...
├── discussion/        # Interactive discussion notes (Phase 2.1)
│   └── discussion-YYYY-MM-DD.yaml
└── synthesis.md       # Comprehensive synthesis document (Phase 2.3+)
```

### Raw Segmentation Schema (`raw/source-NNN-raw.yaml`)

Each source is broken down into **segments** — logical content units that preserve the full source content. Nothing is discarded.

#### Segmentation Rules
| Content type | Rule |
|---|---|
| Regular prose | One segment per sentence |
| Headings/subheadings | One segment each |
| Bullet/numbered lists | One segment per bullet |
| Tables | One segment per row (or per meaningful cell) |
| Figures/graphs | Synthetic segments: extracted data points + description. Image path in metadata if available. |
| Block quotes | One segment |
| Captions/labels | One segment |

#### Segment Classification Taxonomy (10 types)
| Type | Description |
|---|---|
| `claim` | An assertion or argument (normative, empirical, predictive, or definitional) |
| `statistic` | A quantified data point with numbers |
| `evidence` | Data or example supporting a claim |
| `definition` | Defining or explaining a term/concept |
| `recommendation` | Prescriptive/actionable statement |
| `context` | Background information, scene-setting |
| `methodology` | How something was studied or done |
| `example` | Illustrative case or anecdote |
| `attribution` | Citing or referencing another source |
| `noise` | Filler, transitions, marketing language, boilerplate, structural headings |

#### Raw File Format
```yaml
source_id: source-001
title: "Enterprise AI Architecture Report"
url: "https://..."
author: "McKinsey"
date: 2025-06-15
total_segments: 145

# Auto-calculated composition breakdown
composition:
  claim: { count: 42, pct: 29.0 }
  statistic: { count: 18, pct: 12.4 }
  evidence: { count: 23, pct: 15.9 }
  definition: { count: 8, pct: 5.5 }
  recommendation: { count: 12, pct: 8.3 }
  context: { count: 25, pct: 17.2 }
  methodology: { count: 3, pct: 2.1 }
  example: { count: 5, pct: 3.4 }
  attribution: { count: 4, pct: 2.8 }
  noise: { count: 5, pct: 3.4 }

signal_ratio: 96.6  # percentage of non-noise segments

segments:
  - id: seg-001
    text: "Enterprise AI adoption has reached 72% among Fortune 500 companies."
    type: statistic
    section: "Introduction"
    position: 1
    source_format: prose  # prose | bullet | heading | table | figure | quote | caption
    metadata:            # optional, type-specific enrichment
      metric: "AI adoption rate"
      value: 72
      unit: "%"
      population: "Fortune 500"

  - id: seg-045
    text: "AI maturity distribution: Level 1 (Experimental) 35%, Level 2 (Operational) 40%, Level 3 (Transformational) 25%"
    type: statistic
    section: "Maturity Assessment"
    position: 45
    source_format: figure
    metadata:
      extracted_from: "Figure 3: AI Maturity Distribution"
      image_path: "documents/source-001-fig3.png"
      data_points:
        - { label: "Level 1 (Experimental)", value: 35, unit: "%" }
        - { label: "Level 2 (Operational)", value: 40, unit: "%" }
        - { label: "Level 3 (Transformational)", value: 25, unit: "%" }
```

Segment IDs are scoped to the source file (seg-001, seg-002, ...). Cross-source references use `source-001:seg-045` format.

### Claim Alignment Schema (`extractions/claim-alignment.yaml`)

Built on top of the raw segmentation. References segment IDs from `raw/` files for full traceability.

Three output categories:
- **Canonical claims** (`cc-NNN`): Themes where 2+ sources agree. Fields: theme, summary, source_segments (with segment IDs + representative quote), strength (strongly-supported/supported), claim_type (normative/empirical/predictive/definitional).
- **Unique claims** (`uc-NNN`): Positions held by only one source. Fields: source, theme, summary, segments, significance (why it matters that only one source makes this claim).
- **Contradictions** (`ct-NNN`): Where sources disagree. Fields: theme, description, each source's position with segment IDs and stance, resolution (analysis of the disagreement).

### Critical Analysis Schema (`extractions/critical-analysis-part*.yaml`)

Each canonical claim critically analyzed with: verdict (genuine_insight/partial_insight/important_but_obvious/platitude), platitude/actionability/novelty scores (1-10), critique, practical value, concrete action steps, and bottom line.

### Observed Composition Patterns

From test runs, source type strongly affects segment composition:
- **Academic papers**: Claim-heavy (~55-60%), with examples, statistics, and evidence. Include methodology.
- **Vendor reports**: Definition-heavy (~25%), recommendation-heavy (~20%), zero statistics. More prescriptive.
- **Noise floor**: Section headings account for ~4-6% noise. Academic papers may include restated conclusions that could inflate claim counts.

### Build Scripts (`scripts/`)
- **`build-dashboard-data.py`** — Reads extraction YAMLs + claim alignment, outputs `site/static/data/dashboard.json` for the knowledge graph visualization
- **`build-insights-data.py`** — Reads critical analysis YAMLs, outputs `site/static/data/insights.json` for the insights page

### Hugo Custom Pages
- **Dashboard** (`/dashboard/`) — D3.js force-directed knowledge graph showing findings, claims, concepts, statistics, frameworks, and sources with cross-source edges
- **Insights** (`/insights/`) — Critical analysis page: each finding with verdict, scores, critique, practical value, action steps. Filterable by verdict, sortable by scores.
- **Sources** (`/sources/`) — Table of all research sources with metadata

### Topic Status Values
Status corresponds to the current phase:
- `phase-0` — Data gathering in progress (researching sources)
- `phase-1` — Data analysis in progress (extractions, alignment, critical analysis)
- `phase-2` — Insight refinement in progress (discussion, insights, synthesis)
- `phase-3` — Drawing conclusions (findings, recommendations, angles)
- `complete` — Research phases finished, ready for content creation

### Per-Topic Progress Tracking
Each topic's `_index.md` frontmatter tracks phase progress:
```yaml
phase: 1
completed_steps:
  - "0.1"  # Web research
  - "0.2"  # Document ingestion
  - "1.1"  # Per-source extraction
current_step: "1.2"  # Cross-source claim alignment
```

## Hugo Site Configuration

- **Theme**: Paper (`site/themes/paper`)
- **Base URL**: Set in `site/hugo.toml` (update after GitHub Pages setup)
- **Content sections**: `blog/`, `pov/`, `about/`, `dashboard/`, `insights/`, `sources/`
- **Taxonomies**: tags, topics
- **Build command**: `hugo --source site/` or `./scripts/build.sh`

## Available MCP Servers

- **Playwright**: Use for JavaScript-heavy pages that WebFetch can't render properly
- **GitHub**: Use for repository operations when `gh` CLI is insufficient

## Important Notes

- Always read existing files before modifying them
- When creating source notes, use sequential numbering (source-001.md, source-002.md, etc.)
- When creating insights, use sequential numbering (insight-001.md, insight-002.md, etc.)
- Keep the connections graph (`knowledge-base/connections/graph.md`) updated when synthesizing topics
- Run `/status` to see the current state of all pipeline stages
