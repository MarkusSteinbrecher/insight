# /session-writeup

Write a session log summarizing the current Claude Code session's work.

## Process

1. **Review conversation history**: Scan the full conversation to identify all tasks completed, files created/modified, and decisions made.

2. **Check existing session logs**: Read files in `knowledge-base/sessions/` to determine the correct filename:
   - If today's date already has a log, append a suffix: `2026-02-16-s2.md`, `2026-02-16-s3.md`, etc.
   - If no log exists for today, use `YYYY-MM-DD.md`

3. **Write the session log** following this structure:

```markdown
---
date: YYYY-MM-DD
topic: "Primary topic worked on"
sessions: N
status: complete | in-progress
next_action: "What should happen next"
---

# Session Log — YYYY-MM-DD

## Overview
2-3 sentence summary of what was accomplished.

## What happened
### 1. [Task Name]
Description of what was done, key decisions, outputs produced.
Include tables for structured data (insights, claims, use cases, etc.).

### 2. [Next Task]
...

## Key Stats
Table of relevant metrics (sources, claims, findings, etc.)

## Pending Work
### Next Step
1. Immediate next action

### Then
2-5 follow-up items

## Files Created
- List of new files with brief descriptions

## Files Modified
- List of modified files with what changed
```

4. **Guidelines**:
   - Be specific: include counts, file names, claim IDs where relevant
   - Capture decisions and rationale, not just actions
   - Note any errors encountered and how they were resolved
   - Include key stats in a table for quick reference
   - List pending work so the next session can resume efficiently
   - Do NOT include git operations in the log unless they were significant (e.g., resolving conflicts)

5. **Inform the user** of the log file path when complete.
