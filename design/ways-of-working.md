# Ways of Working

How we build Insight. Updated as we learn.

---

## Roles

| Role | Who | Responsibility |
|------|-----|----------------|
| Product Sponsor | User | Direction, priorities, scope approval, acceptance |
| Product Manager | Claude Code | Roadmap, specs, backlog management, status reporting |
| Architect | Claude Code | Technology decisions, component design, ADRs |
| Developer | Claude Code | Implementation, tests, code quality |
| QA | Claude Code | Test coverage, acceptance validation |

## Development Workflow

```
1. Design    — Component design doc (intent, rationale, high-level)
2. Spec      — Detailed specification (interfaces, contracts, acceptance criteria)
3. Review    — Sponsor reviews spec, approves or adjusts
4. Test      — Write tests from acceptance criteria
5. Code      — Implement to pass the tests
6. Validate  — All tests pass, integration verified
7. Document  — Update CLAUDE.md, backlog, ADRs as needed
```

### Rules

- **No code without a spec.** The spec defines what "done" means.
- **Acceptance criteria are testable.** If you can't write a test for it, rewrite the AC.
- **Tests before or alongside code.** Not after.
- **Read before write.** Always read existing code before modifying.
- **Specs are living documents.** Update them when implementation reveals a better approach. Note the change and rationale.

## Decision Making

- **Architecture decisions** → ADR in `design/decisions/`. Documents context, options, decision, consequences.
- **Scope decisions** → Confirm with sponsor before expanding scope beyond what was asked.
- **Technology choices** → ADR for significant choices (database, framework, major library).
- **Implementation details** → Developer discretion, following existing patterns.

## Documentation

| Document | Location | Purpose | Updated when |
|----------|----------|---------|--------------|
| Architecture overview | `design/v2-architecture.md` | System-level view, milestone status | Milestone changes |
| Component designs | `design/{component}.md` | Intent, rationale, decisions | Design changes |
| Specifications | `design/specs/{component}.md` | Contracts, interfaces, ACs | Before implementation |
| ADRs | `design/decisions/` | Significant decisions | When decisions are made |
| Product guide | `CLAUDE.md` | Project conventions, current status | Each milestone |
| Backlog | `backlog.md` | Work items and priorities | Each session |
| Ways of working | `design/ways-of-working.md` | This document | When process changes |

## Status Reporting

- Use `/status` command to generate current project status
- Report covers: milestone progress, test status, graph stats, blockers
- Sponsor can request status at any time

## Lessons Learned

Captured here as they emerge. Updated across sessions.

### 2026-03-06 — Session 1

- **Start with specs, not code.** Initial impulse was to start coding immediately. Better to specify interfaces and acceptance criteria first — caught several design issues (discovery/extraction split, source storage model) during spec writing that would have required refactoring.
- **The sponsor sets the quality bar.** "Weekend project" vs "comprehensive solution" are fundamentally different approaches. Clarify expectations early.
- **Design docs and specs are different things.** Design docs capture intent and rationale (why). Specs capture contracts and acceptance criteria (what, precisely). Both are needed.
