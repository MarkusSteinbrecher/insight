# /status

View the pipeline dashboard — topics, content, and suggested next actions.

## Arguments

No arguments required.

## Process

1. **Scan knowledge base topics**:
   - List all directories in `knowledge-base/topics/`
   - For each topic, read `_index.md` to get: title, status, source_count, insight_count, updated date
   - Sort by last updated date (most recent first)

2. **Scan content pipeline** (future — check if directories have content):
   - `content/ideas/` — count idea files
   - `content/drafts/` — count draft files
   - `content/ready/` — count ready files

3. **Scan published content**:
   - `site/content/blog/` — count published blog posts (excluding _index.md)
   - `site/content/pov/` — count published POVs (excluding _index.md)

4. **Present dashboard**:

   ```
   # Pipeline Status

   ## Knowledge Base
   | Topic | Status | Sources | Insights | Updated |
   |-------|--------|---------|----------|---------|
   | Topic Title | synthesized | 24 | 12 | 2024-01-15 |
   | Other Topic | researching | 8 | 0 | 2024-01-14 |

   ## Content Pipeline
   - Ideas: N
   - Drafts: N
   - Ready to publish: N

   ## Published
   - Blog posts: N
   - POVs: N

   ## Suggested Next Actions
   - {Contextual suggestions based on pipeline state}
   ```

5. **Generate suggestions**:
   Based on the current state, suggest logical next actions:
   - Topics in "researching" → suggest `/analyze {topic}`
   - Topics in "analyzed" → suggest `/synthesize {topic}`
   - Topics in "synthesized" → suggest creating content
   - Empty knowledge base → suggest `/research <topic>` with example topics
   - Drafts ready → suggest validation and publishing

## Example Output

```
# Pipeline Status

## Knowledge Base
No topics yet. Get started with:
  /research AI agents in the enterprise
  /research platform engineering trends
  /research LLM fine-tuning strategies

## Content Pipeline
Empty — research a topic first, then create content from your synthesis.

## Published
No published content yet.
```
