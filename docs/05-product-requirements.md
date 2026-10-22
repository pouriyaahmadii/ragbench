# RAGBench — Product Requirements Document (PRD)

**Version:** 1.0  
**Date:** 2026-10-22  
**Status:** Phase 2 deliverable

---

## Product Summary

RAGBench is a **local-first Retrieval-Augmented Generation (RAG) application and evaluation lab**. It enables users to ingest a controlled collection of documents (PDF, TXT, Markdown), ask questions grounded in those documents, inspect source citations that resolve to actual stored chunks, construct versioned evaluation datasets with explicit ground truth, run reproducible experiments comparing retrieval and generation configurations, and honestly report limitations.

The product demonstrates both **application engineering** (document ingestion, metadata persistence, API design, provider abstractions, UI, containerization, security) and **evaluation engineering** (fixed datasets, explicit ground truth, independent retrieval and generation metrics, reproducible experiment configurations, honest reporting of limitations).

---

## Goals (MVP)

| Goal | Description |
|------|-------------|
| G1 | **Document Ingestion** — Accept PDF, TXT, Markdown; preserve metadata; explicit ingestion states |
| G2 | **Configurable Pipeline** — Chunking, embedding, retrieval, generation all configurable and versioned |
| G3 | **Grounded Answers** — Citations validated server-side against retrieved chunks; abstention when evidence insufficient |
| G4 | **Reproducible Evaluation** — Versioned datasets with ground truth; deterministic metrics (Precision@k, Recall@k, MRR, nDCG, Citation Validity) |
| G5 | **Experiment Comparison** — Immutable experiment configs; side-by-side comparison with deltas and config diff |
| G6 | **Zero-Credential Demo** — Deterministic Mock mode works without paid APIs or model downloads |
| G7 | **Local-First Deployment** — Docker Compose with loopback binding; no public ports for DB/vector store |
| G8 | **Professional Quality** — Tests, CI, linting, type checking, security scanning, documentation |

---

## Non-Goals (MVP)

| Non-Goal | Reason |
|----------|--------|
| Public multi-tenant SaaS deployment | Out of scope; requires auth, TLS, rate limiting |
| Unrestricted public URL crawling | Security risk; MVP is local document upload only |
| Executing instructions/code from documents | Safety; documents treated as untrusted data |
| Guaranteeing factual correctness of all answers | System abstains when evidence insufficient; no hallucination elimination claim |
| Complete protection against prompt injection | Defense-in-depth only; adversarial tests document limits |
| Fine-tuning or training foundation models | Not an ML training platform |
| Large-scale distributed indexing | Single-node local MVP |
| Mandatory paid model/embedding/evaluator APIs | Mock mode required for CI/demo |
| Multimodal (image/audio/video) RAG | Text-only MVP |
| Complex agentic research workflows | Single-turn grounded QA is MVP |
| Arbitrary document archive ingestion | PDF/TXT/MD only in MVP |
| Automatic publication/external actions | Human-in-the-loop for MVP |

---

## Target Audience

| Audience | What They Evaluate |
|----------|-------------------|
| AI/LLM Engineering Hiring Managers | Architecture quality, evaluation rigor, security posture, reproducibility |
| Backend/Platform Engineers | API design, data model, provider abstractions, containerization, CI/CD |
| Applied ML Engineers | Chunking strategies, embedding models, retrieval parameters, experiment comparison |
| Technical Reviewers | Ability to run locally, understand code, verify claims without secrets |

---

## User Stories (Consolidated from docs/02-personas-and-user-stories.md)

### Hiring Manager (Primary)
- **US-HM-1:** Run `make up` and see working demo in <5 min without API keys
- **US-HM-2:** Inspect evaluation dataset and see explicit ground truth
- **US-HM-3:** Run `make eval` and see deterministic metrics (Precision@k, Recall@k, MRR)
- **US-HM-4:** Compare two experiment configurations and see measured deltas
- **US-HM-5:** Read threat model and see prompt injection mitigations documented

### Platform Engineer (Secondary)
- **US-PE-1:** See explicit pipeline stage modules (ingestion, chunking, embeddings, retrieval, generation, citations)
- **US-PE-2:** Verify provider interfaces with Mock/Ollama/OpenAI implementations
- **US-PE-3:** Inspect Alembic migrations and see versioned schema
- **US-PE-4:** Run `make test` and see unit/integration/contract tests pass
- **US-PE-5:** Review GitHub Actions CI and see secret scanning included

### ML Engineer (Secondary)
- **US-ME-1:** Change chunking config and see new index version created automatically
- **US-ME-2:** Run same dataset against different embedding models and compare retrieval metrics
- **US-ME-3:** See failed evaluation samples reported, not silently dropped
- **US-ME-4:** Inspect experiment config manifest with all provider/model/version details

### Technical Reviewer (Tertiary)
- **US-TR-1:** Follow README and have working system in <5 minutes
- **US-TR-2:** Upload PDF, ask question, click citation to see source page
- **US-TR-3:** Ask unanswerable question and see "insufficient evidence" response
- **US-TR-4:** Read glossary and understand all terminology
- **US-TR-5:** See no fabricated metrics — only measured results reported

---

## Functional Requirements Summary

Detailed in `docs/06-functional-requirements.md`. Key areas:

| Domain | Requirements | Priority |
|--------|--------------|----------|
| Document Ingestion (DOC) | DOC-001 through DOC-006 | P0 |
| Chunking (CHK) | CHK-001 through CHK-004 | P0/P1 |
| Embeddings (EMB) | EMB-001 through EMB-003 | P0 |
| Vector Indexing (IDX) | IDX-001 through IDX-003 | P0 |
| Retrieval (RET) | RET-001 through RET-003 | P0/P1 |
| Generation (GEN) | GEN-001 through GEN-003 | P0 |
| Citations (CIT) | CIT-001, CIT-002 | P0 |
| Evaluation (EVAL) | EVAL-001 through EVAL-004 | P0/P1 |
| Experiments (EXP) | EXP-001, EXP-002 | P0 |
| Operations (OPS) | OPS-001, OPS-002 | P0 |
| Security (SEC) | SEC-001, SEC-002 | P0 |
| UI (UI) | UI-001 | P0 |
| Observability (OBS) | OBS-001 | P1 |
| Performance (PERF) | PERF-001 | P1 |
| CI/CD (CI) | CI-001 | P0 |

---

## Non-Functional Requirements Summary

Detailed in `docs/07-non-functional-requirements.md`. Key categories:

| Category | Key Requirements |
|----------|------------------|
| Performance | Upload <1s, Parse <10s, Retrieval p95<200ms, Total E2E <2s (Mock) |
| Scalability | 100 docs, 50k chunks, sequential ingestion, 5 concurrent queries |
| Reliability | Explicit states, no silent drops, bounded retries, deterministic re-ingestion |
| Availability | Startup <60s, restart <10s, data persistence, Mock mode fallback |
| Security | No secrets in Git, loopback binding, upload validation, citation validation |
| Maintainability | Independent modules, provider interfaces, Pydantic Settings, strict types |
| Usability | Setup <5min, clear errors, citation inspection, config diff, a11y basics |
| Portability | Docker on Linux/macOS/Windows, pinned Python 3.11+/Node 20 LTS |
| Data Integrity | SHA-256 hashes, dimension validation, index versioning, config hashing |
| Observability | Structured JSON logs, correlation IDs, stage latency, error categories |

---

## Constraints & Assumptions

### Technical Constraints
- **Local-first:** Docker Compose required; no cloud dependencies for MVP demo
- **Mock mode mandatory:** All CI and required demos work without paid APIs
- **Single-user:** No authentication/authorization in MVP
- **English-only:** Documents and queries in English for MVP
- **Text-only:** PDF, TXT, Markdown only; no archives, images, audio, video

### Resource Constraints (Defaults)
- Max upload: 20 MiB | Max PDF pages: 200 | Max extracted text: 1M chars
- Chunk size: 1200 chars | Overlap: 150 chars | Top-k: 5 (max 20)
- Context budget: 4000 chars | Generation output: 1024 tokens

### Assumptions
- Reviewer has Docker Desktop and 4+ GB RAM
- Synthetic fixtures sufficient for demonstration (CC0 licensed)
- Mock providers exercise full pipeline contracts
- Optional local models (Ollama) run natively on host, not in containers

---

## Success Metrics (from docs/03-success-metrics.md)

### Must-Have (Gate Criteria)
- **Gate A (Setup):** Docker Compose starts clean, services healthy, Mock mode works
- **Gate B (Ingestion):** All 3 formats accepted, invalid rejected, metadata preserved
- **Gate C (RAG Answer):** Scoped queries, citations resolve, abstention works, injection blocked
- **Gate D (Evaluation):** Immutable datasets, deterministic metrics, failed samples visible, configs comparable
- **Gate E (Quality):** Tests pass, type checks pass, CI green, secret scan clean, README verified

### Measured Baselines (Post-Implementation)
All "Measured" values remain TBD until actual implementation runs produce them. No fabricated numbers.

---

## Release Criteria

**Ready for Portfolio Demo** when:
- All Gates A-E PASS
- No Critical audit findings
- README commands verified
- Real screenshots from actual implementation

**Not Production Ready** — explicitly documented. Production deployment requires auth, TLS, rate limiting, multi-tenancy, penetration testing, etc.

---

## Dependencies Between Major Components

```
Document Upload (DOC)
    ↓
Parsing & Metadata (DOC)
    ↓
Chunking (CHK)
    ↓
Embedding (EMB) ──→ Vector Indexing (IDX)
    ↓                    ↓
Retrieval (RET) ←────────┘
    ↓
Context Construction
    ↓
Generation (GEN)
    ↓
Citation Validation (CIT)
    ↓
Answer Response
    ↓
Evaluation Dataset (EVAL) ──→ Deterministic Metrics (EVAL)
    ↓                              ↓
Experiment Runner (EXP) ←──────────┘
    ↓
Comparison & Reporting (EXP)
    ↓
Frontend Integration (UI)
```

**Critical Path:** Upload → Parse → Chunk → Embed → Index → Retrieve → Generate → Validate → Answer → Evaluate → Compare

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Mock mode too trivial | Medium | High | Design Mock to exercise full pipeline contracts; document limitations |
| Qdrant/PostgreSQL version incompatibility | Low | Medium | Pin explicit compatible image tags; test startup order |
| Embedding dimension mismatch | Medium | High | Validate dimension at ingestion and query; version index by embedding config |
| LLM judge bias invalidates comparison | High | Medium | Never present judge scores as ground truth; separate from deterministic metrics |
| Scope creep beyond MVP | High | High | Strict P0/P1/P2 prioritization; ADR required for architecture changes |
| Fabricated metrics in portfolio | Low | Critical | Strict policy: only real implementation outputs; label unimplemented as "planned" |

---

## External Compatibility (Recorded)

| Dependency | Version | Checked | Notes |
|------------|---------|---------|-------|
| Python | 3.11+ | 2026-10-22 | Pinned in Dockerfile |
| FastAPI | 0.110.x | 2026-10-22 | Compatible with Pydantic 2 |
| Pydantic | 2.7+ | 2026-10-22 | v2 required |
| PostgreSQL | 16 | 2026-10-22 | Alpine image |
| Qdrant | 1.10.1 | 2026-10-22 | gRPC client |
| Node.js | 20 LTS | 2026-10-22 | Pinned in Dockerfile |
| Next.js | 14.2.x | 2026-10-22 | App Router |
| Ollama | Latest | 2026-10-22 | Optional, host-native |