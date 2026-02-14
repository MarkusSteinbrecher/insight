# Research Agent

A Claude Code-powered system for creating thought leadership content on Technology and AI topics.

## What It Does

- **Research**: Gathers and organizes sources from the web on any tech/AI topic
- **Analyze**: Extracts insights, patterns, and contradictions from collected sources
- **Synthesize**: Creates comprehensive synthesis documents with thought leadership angles
- **Publish**: Generates blog posts, POVs, and presentations published to GitHub Pages

## Quick Start

### Prerequisites

- [Claude Code](https://claude.com/claude-code) CLI installed
- [Hugo](https://gohugo.io/installation/) (extended edition) installed
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
# Build the Hugo site locally
./scripts/build.sh

# Or directly
hugo server --source site/
```

## Project Structure

```
├── knowledge-base/     # Research repository organized by topic
│   ├── topics/         # One directory per research topic
│   └── connections/    # Cross-topic relationship map
├── content/            # Content pipeline (ideas → drafts → ready)
├── site/               # Hugo static site for GitHub Pages
├── .claude/            # Commands, agents, and skills
└── scripts/            # Build helpers
```

## License

Private repository — all rights reserved.
