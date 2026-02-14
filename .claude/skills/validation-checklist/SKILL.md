# Validation Checklist Skill

## Activation

This skill is auto-triggered when validating content before publishing. It will be fully wired up with the `/validate` command in a future phase.

## Purpose

Ensures content meets quality, accuracy, and publishing standards before it goes live. The checklist covers five dimensions: accuracy, argumentation, originality, quality, and publishing readiness.

## Usage

When validating content, work through each section of the checklist in `references/checklist.md`. For each item:
- **Pass**: The item meets the standard
- **Flag**: The item needs attention — note the specific issue
- **N/A**: Not applicable to this content type

Generate a validation report summarizing:
1. Overall assessment (ready / needs revision / major issues)
2. Items flagged with specific issues and suggested fixes
3. Strengths worth highlighting

## Validation Report Format

```yaml
---
content: "path/to/content-file.md"
date: YYYY-MM-DD
overall: ready | needs-revision | major-issues
---

## Summary
Brief overall assessment.

## Flags
- [ ] **[Category]**: Description of issue. Suggested fix.

## Strengths
- Notable quality or strength of the piece.
```
