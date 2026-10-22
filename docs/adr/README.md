# Architecture Decision Records Index

This directory contains Architecture Decision Records (ADRs) for RAGBench. Each ADR documents a significant architectural decision, its context, alternatives considered, and consequences.

## ADR List

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [ADR-001](ADR-001-initial-technology-stack.md) | Initial Technology Stack | Accepted | 2026-10-22 |
| [ADR-002](ADR-002-rag-pipeline-boundaries.md) | RAG Pipeline Boundaries | Accepted | 2026-10-22 |
| [ADR-003](ADR-003-provider-abstraction.md) | Provider Abstraction for Embeddings and Generation | Accepted | 2026-10-22 |
| [ADR-004](ADR-004-evaluation-metrics.md) | Evaluation Metrics Strategy | Accepted | 2026-10-22 |
| [ADR-005](ADR-005-background-processing.md) | Background Processing (Celery/Redis) | Proposed | 2026-10-22 |

## ADR Format

Each ADR follows this structure:

```markdown
# ADR-XXX: Title

**Status:** Proposed | Accepted | Superseded | Rejected
**Date:** YYYY-MM-DD
**Deciders:** [Names/roles]
**Technical Story:** [Link to issue/PR]

## Context
[Background and problem statement]

## Decision
[What was decided]

## Alternatives Considered
[Other options and why they were rejected]

## Consequences
### Positive
[Benefits]
### Negative
[Drawbacks/risks]
### Risks
[Mitigation strategies]

## Implementation Notes
[Key implementation details]

## Related ADRs
[Links to related decisions]
```

## Process

1. **Propose:** Create ADR in `Proposed` state when a significant decision is needed
2. **Discuss:** Team reviews (async or sync)
3. **Decide:** Update to `Accepted` with deciders recorded
4. **Implement:** Code follows the decision
5. **Supersede:** If decision changes, new ADR supersedes old (never delete)

## When to Create an ADR

- Technology selection (language, framework, database, cloud service)
- Architectural pattern (microservices vs modular monolith, event-driven vs sync)
- Data model changes affecting multiple components
- Security boundaries and trust zones
- Evaluation/metrics methodology
- Any decision with significant maintenance or migration cost

## When NOT to Create an ADR

- Minor implementation details
- Code style preferences (use linter config)
- Library version upgrades (unless breaking)
- Temporary workarounds (document in code comments)