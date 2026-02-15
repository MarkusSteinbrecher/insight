# Research Agent

An AI-supported solution for gathering and analysing information from the internet (e.g. thought leadership articles, points fo view) on a specific topic.

## What It Does

- **Baseline**: Defines a knowledge baseline for the user (either manually or automatically)
- **Research**: Gathers and organizes sources or uploaded manually (PDFs) from the web on any topic
- **Analyze**: Converts the sources into a raw structure into segments and identify claims (COMMENT - add our claims classifiers here)
- **Synthesize**: Creates findings from all sources and links them
- **Publish**: work-in-progress

## Quick Start

### Prerequisites

- [Claude Code](https://claude.com/claude-code) CLI installed
- [GitHub CLI](https://cli.github.com/) (`gh`) installed and authenticated

### Commands

```
/research <topic>    # Research a topic — gathers sources from the web
/analyze <topic>     # Analyze collected sources — extract insights
/synthesize <topic>  # Create synthesis document with key themes and angles
/kb <query>          # Search the knowledge base
/status              # View pipeline dashboard
```

### Local Development

```bash
# Build site data and serve locally
./scripts/build.sh
python3 -m http.server 8000 --directory docs/
```

## Project Structure

```
├── knowledge-base/     # Research repository organized by topic
│   └── topics/         # One directory per research topic
├── content/            # Content pipeline (ideas → drafts → ready)
├── docs/               # Static site (HTML/CSS/JS) for GitHub Pages
├── .claude/            # Commands, agents, and skills
└── scripts/            # Build and data generation scripts
```

