# /kb <query>

Search the knowledge graph for sources, claims, findings, and connections.

## Arguments

$ARGUMENTS — The search query (e.g., "governance", "AI agents", "enterprise adoption")

## Process

1. **Search the graph**:
   ```python
   from insight.graph import InsightGraph
   g = InsightGraph()
   ```

2. **Organize results by type**:

   **Sources**: Search source titles and authors
   - Show: source ID, title, author, type, extract count

   **Claims**: Search claim summaries
   - Show: claim ID, summary, source count, theme

   **Findings**: Search finding titles and descriptions
   - Show: finding ID, title, category, claim count

3. **Present results** in a clear, scannable format

4. **Suggest related queries** based on themes found

## Example

```
/kb enterprise AI adoption
```
