# /kb <query>

Search across the knowledge base for topics, insights, sources, and connections.

## Arguments

$ARGUMENTS — The search query (e.g., "AI agents", "enterprise adoption", "transformer architecture")

## Process

1. **Search the knowledge base**:
   Use Grep to search across all files in `knowledge-base/` for the query term(s).

2. **Organize results by type**:

   **Topics**:
   - Search `knowledge-base/topics/*/_ index.md` files
   - Show: topic title, status, source count, insight count

   **Insights**:
   - Search `knowledge-base/topics/*/insights/*.md` files
   - Show: claim, confidence level, type, and file path

   **Sources**:
   - Search `knowledge-base/topics/*/sources/*.md` files
   - Show: title, relevance score, and file path

3. **Present results**:
   Format results in a clear, scannable way:

   ```
   ## Topics matching "{query}"
   - **{topic-title}** [{status}] — {source_count} sources, {insight_count} insights
     Path: knowledge-base/topics/{slug}/

   ## Insights matching "{query}"
   - [{confidence}] {claim}
     Type: {type} | Sources: {source-list}
     Path: knowledge-base/topics/{slug}/insights/{file}

   ## Sources matching "{query}"
   - {title} [relevance: {N}/5]
     Path: knowledge-base/topics/{slug}/sources/{file}

   ```

4. **Suggest related topics**:
   Based on the search results and topic tags in `_index.md` files, suggest related topics the user might want to explore.

## Example

```
/kb enterprise AI adoption
```

Searches all knowledge base files for "enterprise AI adoption" and returns organized results.
