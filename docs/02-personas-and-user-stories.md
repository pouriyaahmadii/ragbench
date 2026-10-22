# RAGBench — Personas and User Stories

**Version:** 1.0  
**Date:** 2026-10-22  
**Status:** Phase 1 deliverable

---

## Primary Personas

### 1. AI/LLM Engineering Hiring Manager (Primary)
**Role:** Evaluates technical portfolios for LLM engineering positions  
**Goals:**
- Quickly assess RAG implementation quality
- Verify evaluation rigor (not just "it works")
- Check security awareness and reproducibility
- Understand architecture decisions without reading all code

**Pain Points:**
- Most RAG demos are black boxes with no metrics
- Hard to distinguish junior vs senior engineering
- No evidence of systematic evaluation methodology
- Security often ignored in portfolio projects

**User Stories:**
- As a hiring manager, I can run `make up` and see a working demo in <5 minutes without API keys
- As a hiring manager, I can inspect the evaluation dataset and see explicit ground truth
- As a hiring manager, I can run `make eval` and see deterministic metrics (Precision@k, Recall@k, MRR)
- As a hiring manager, I can compare two experiment configurations and see measured deltas
- As a hiring manager, I can read the threat model and see prompt injection mitigations documented

---

### 2. Backend/Platform Engineer (Secondary)
**Role:** Reviews API design, data model, infrastructure, CI/CD  
**Goals:**
- Assess modularity and separation of concerns
- Verify provider abstraction pattern
- Check database schema and migration strategy
- Evaluate Docker Compose and deployment readiness

**User Stories:**
- As a platform engineer, I can see explicit pipeline stage modules (ingestion, chunking, embeddings, retrieval, generation, citations)
- As a platform engineer, I can verify provider interfaces with Mock/Ollama/OpenAI implementations
- As a platform engineer, I can inspect Alembic migrations and see versioned schema
- As a platform engineer, I can run `make test` and see unit/integration/contract tests pass
- As a platform engineer, I can review GitHub Actions CI and see secret scanning included

---

### 3. Applied ML Engineer (Secondary)
**Role:** Interested in chunking strategies, embedding models, retrieval parameters, experiment comparison  
**Goals:**
- Understand how to run controlled experiments
- See deterministic vs judge-based metrics separation
- Verify index versioning when embedding model changes
- Reproduce evaluation results

**User Stories:**
- As an ML engineer, I can change chunking config and see a new index version created automatically
- As an ML engineer, I can run the same dataset against different embedding models and compare retrieval metrics
- As an ML engineer, I can see that failed evaluation samples are reported, not silently dropped
- As an ML engineer, I can inspect the experiment config manifest and see all provider/model/version details recorded

---

### 4. Technical Reviewer / Researcher (Tertiary)
**Role:** Clones repo, runs local demo, reads docs to understand approach  
**Goals:**
- Run the system locally without paid services
- Understand the RAG pipeline stages
- Verify claims match implementation
- Learn from the architecture

**User Stories:**
- As a reviewer, I can follow README and have a working system in <5 minutes
- As a reviewer, I can upload a PDF, ask a question, and click a citation to see the source page
- As a reviewer, I can ask an unanswerable question and see "insufficient evidence" response
- As a reviewer, I can read the glossary and understand all terminology
- As a reviewer, I can see that no metrics are fabricated — only measured results reported

---

## User Journey Map

### Journey 1: First-Time Demo (Hiring Manager / Reviewer)
```
Clone repo → Read README → cp .env.example .env → make up
    → Open http://127.0.0.1:3000 → See Dashboard
    → Upload policy.pdf → Watch ingestion: validating → parsing → chunking → embedding → indexing → ready
    → Go to Chat → Ask "What is the retention period?" → See answer with citation
    → Click citation → Drawer opens with page 3, excerpt "30 days"
    → Ask "What is the CEO's favorite color?" → See "insufficient evidence"
    → Go to Evaluations → Select ragbench-demo v1.0.0 → Run evaluation
    → See Precision@5=0.72, Recall@5=0.68, MRR=0.81
    → Go to Experiments → Compare baseline vs chunk-size-800 → See deltas
```

### Journey 2: Configuration Experiment (ML Engineer)
```
Select corpus → Create experiment config (chunk=800, overlap=100, embedding=mock)
    → Run evaluation → System creates new index version automatically
    → Compare with baseline experiment → See config diff + metric deltas
    → Drill into sample-level changes → See which queries improved/regressed
```

### Journey 3: Code Inspection (Platform Engineer)
```
Read docs/05-system-architecture.md → See C4 diagrams
    → Read docs/adr/ADR-003-provider-abstraction.md → See protocol definitions
    → Browse services/backend/app/providers/ → See Mock/Ollama/OpenAI implementations
    → Run make test-unit → See chunking, metrics, citation validation tests
    → Run make test-integration → See parser→chunks, Qdrant upsert/query tests
```

---

## Assumptions

| Assumption | Validation |
|------------|------------|
| Reviewer has Docker Desktop installed | Documented in README prerequisites |
| 4+ GB RAM available | Standard for modern laptops |
| No GPU required for Mock mode | Verified: Mock providers CPU-only |
| English-only documents/queries for MVP | Explicit in scope |
| Single-user local deployment | No auth in MVP |
| Synthetic fixtures sufficient for demo | CC0 licensed, in `data/samples/` |

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Docker not installed | Medium | High | Clear prerequisites in README; alternative: run services locally |
| Port conflicts (3000, 8000) | Low | Medium | Document `lsof -ti:3000,8000 | xargs kill` fix |
| Qdrant/PostgreSQL startup race | Low | Medium | Healthchecks with `condition: service_healthy` |
| Mock mode too trivial to impress | Medium | High | Design Mock to exercise full pipeline; document limitations |
| Reviewer expects real LLM quality | Medium | High | Clear "Mock Provider" badges; document optional Ollama/OpenAI |
| Fabricated metrics suspected | Low | Critical | Deterministic fixtures; `make eval` reproducible; CI runs same |

---

## Success Criteria for Phase 1

- [x] Workspace audit completed (git status, directory structure verified)
- [x] Product vision documented (`docs/01-product-vision.md`)
- [x] Scope and MVP boundaries explicit (`docs/02-scope-and-mvp.md`)
- [x] Personas and user stories documented (this file)
- [x] Success metrics defined (see `docs/03-success-metrics.md`)
- [x] Glossary created (see `docs/04-glossary.md`)
- [x] README.md exists with "in development" status
- [x] No unimplemented capabilities described as complete
- [x] No fabricated badges, benchmarks, or demo links
- [x] Existing user work preserved (original SPEC files in repo root)