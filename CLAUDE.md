# Research Agent - Claude Code Project Instructions

## Architecture Overview

This project is a Claude Code-powered system for creating thought leadership content (POVs, presentations, blogs) focused on Technology and AI topics. It consists of four main components:

### 1. Knowledge Base (`knowledge-base/`)
Structured research repository organized by topic. Each topic contains sources (web research notes), insights (extracted analysis), and a synthesis document.

### 2. Content Pipeline (`content/`)
Three-stage pipeline: `ideas/` → `drafts/` → `ready/`. Content moves through stages via commands.

### 3. Hugo Site (`site/`)
Static site published to GitHub Pages. Uses the Paper theme. Content types: blog posts, POVs/whitepapers, about page.

### 4. Commands, Agents & Skills (`.claude/`)
- **Commands** (`commands/`): User-invoked slash commands for the workflow pipeline
- **Agents** (`agents/`): Subagent definitions for parallel research and analysis
- **Skills** (`skills/`): Auto-triggered contextual behaviors

## Workflow Pipeline

```
/research <topic>  → Gather 8-12 sources per angle from the web
/ingest <topic>    → Process uploaded documents (PDFs, etc.) into structured source notes
/analyze <topic>   → Extract insights, patterns, contradictions from sources
/synthesize <topic> → Create comprehensive synthesis with thought leadership angles
/ideate <topic>    → (Future) Generate content ideas from synthesis
/draft <type>      → (Future) Create content draft from idea
/validate <slug>   → (Future) Run quality/accuracy checklist
/publish <slug>    → (Future) Publish to Hugo site and deploy
```

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
├── documents/         # Raw input files (PDFs, reports, screenshots, etc.)
│   └── ...            # Drop files here manually for processing
├── sources/           # Structured source notes (from web research AND document ingestion)
│   ├── source-001.md
│   └── ...
├── insights/          # Extracted insights
│   ├── insight-001.md
│   └── ...
└── synthesis.md       # Comprehensive synthesis document
```

### Topic Status Values
- `researching` — Sources being gathered
- `analyzed` — Insights extracted from sources
- `synthesized` — Synthesis document complete
- `active` — Being used for content creation

## Hugo Site Configuration

- **Theme**: Paper (`site/themes/paper`)
- **Base URL**: Set in `site/hugo.toml` (update after GitHub Pages setup)
- **Content sections**: `blog/`, `pov/`, `about/`
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
