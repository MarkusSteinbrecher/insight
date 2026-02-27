# insight

An AI-supported solution for gathering and analysing information from the internet (e.g. thought leadership articles, points of view) on a specific topic.

Note, this is still all work in progress.

## What It Does

- **Research**: Gathers and organizes sources from the web or uploaded documents (PDFs) on any topic
- **Baseline**: Defines a common-knowledge baseline to assess claim novelty
- **Analyze**: Breaks sources into segments, classifies claims, aligns them across sources, and critically assesses each
- **Synthesize**: Creates findings from all sources, identifies tensions, and produces a comprehensive synthesis
- **Conclude**: Assesses actionability, generates prioritised recommendations, and identifies thought leadership angles
- **Publish**: Static site with findings, recommendations, claims, and sources (work-in-progress content pipeline)

## Phases

Each topic progresses through four phases. Per-topic progress is tracked in the topic's `_index.md` frontmatter (`phase` and `completed_steps` fields).

### Phase 0 — Data Gathering

Collect raw material from the web and uploaded documents.

| Step | Description | Command | Output |
|------|-------------|---------|--------|
| 0.1 | Web research — initial 3-angle sweep for new topics, or criteria-based search for existing topics | `/research <topic>` | `sources/source-NNN.md` |
| 0.2 | Document ingestion — process uploaded PDFs/docs into structured source notes | `/ingest <topic>` | `sources/source-NNN.md`, `documents/` |
| 0.3 | Topic baseline — establish common knowledge via web search, evaluate claim novelty | `/baseline <topic>` | `baseline.md`, `extractions/baseline-evaluation.yaml` |

### Phase 1 — Data Analysis

Structured extraction and cross-referencing of all gathered sources.

| Step | Description | Command | Output |
|------|-------------|---------|--------|
| 1.1 | Raw segmentation — break each source into numbered segments, classify each (claim, statistic, evidence, etc.) | `/analyze <topic>` | `raw/source-NNN-raw.yaml` |
| 1.2 | Cross-source claim alignment — deduplicate claims, identify consensus, unique positions, contradictions | `/analyze <topic>` | `extractions/claim-alignment.yaml` |
| 1.3 | Critical analysis — assess each canonical claim (critique, practical value, action steps, bottom line) | `/analyze <topic>` | `extractions/critical-analysis.yaml` |
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
| 3.1 | Reader perspective — actionability assessment per finding: what's actionable, what barriers exist, what's missing | `/conclude <topic>` | `extractions/conclusions.yaml` |
| 3.2 | Recommendations — prioritized, concrete actions sequenced by dependency and effort | `/conclude <topic>` | `extractions/conclusions.yaml` |
| 3.3 | Thought leadership angles — unique perspectives, contrarian positions, and content hooks worth owning | `/conclude <topic>` | `extractions/conclusions.yaml` |

### Content Creation (downstream)

Producing deliverables from completed research. Separate from the research phases.

| Step | Description | Command | Output |
|------|-------------|---------|--------|
| Ideation | Generate content ideas from synthesis | `/ideate <topic>` (future) | `content/ideas/` |
| Drafting | Create content draft (blog, POV, presentation) | `/draft <type>` (future) | `content/drafts/` |
| Validation | Run quality/accuracy checklist | `/validate <slug>` (future) | checklist report |
| Publishing | Publish to site and deploy | `/publish <slug>` (future) | `docs/` |

## Quick Start

### Prerequisites

- [Claude Code](https://claude.com/claude-code) CLI installed
- [GitHub CLI](https://cli.github.com/) (`gh`) installed and authenticated

### Commands

```
/research <topic>    # Research a topic — gathers sources from the web
/ingest <topic>      # Ingest uploaded documents (PDFs, reports)
/baseline <topic>    # Establish common-knowledge baseline
/analyze <topic>     # Analyze collected sources — segment, align, critique
/discuss <topic>     # Interactive discussion of findings
/synthesize <topic>  # Create synthesis document with findings and angles
/conclude <topic>    # Generate recommendations and thought leadership angles
/kb <query>          # Search the knowledge base
/status              # View pipeline dashboard
```

### Local Development

```bash
# Build site data and serve locally
bash scripts/build.sh serve
```

## Project Structure

```
├── knowledge-base/     # Research repository organized by topic
│   └── topics/         # One directory per research topic
├── content/            # Content pipeline (ideas → drafts → ready)
├── docs/               # Static site (HTML/CSS/JS) for GitHub Pages
├── scripts/            # Build and data generation scripts
└── .claude/            # Commands, agents, and skills
```
