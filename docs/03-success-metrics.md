# RAGBench — Success Metrics

**Version:** 1.0  
**Date:** 2026-10-22  
**Status:** Phase 1 deliverable

---

## Metric Categories

### 1. Setup & Demo Metrics (User Experience)

| Metric | Target | Measurement Method | Status |
|--------|--------|-------------------|--------|
| Time to running demo (clean clone) | < 5 min | Stopwatch: `git clone → make up → UI loads` | Planned |
| Mock E2E runtime (tiny fixture) | < 10 s | `make eval` with 3-sample fixture | Planned |
| Docker Compose startup time | < 60 s | Fresh volumes, includes image pull | Planned |
| Documentation clarity score | > 4/5 | Reviewer survey (post-MVP) | Planned |

### 2. Ingestion Quality Metrics

| Metric | Target | Measurement Method | Status |
|--------|--------|-------------------|--------|
| Valid fixture ingestion success rate | 100% | 10 PDF/TXT/MD fixtures → all `ready` | Planned |
| Oversized file rejection | 100% | 21 MiB file → 413 before processing | Planned |
| Unsupported format rejection | 100% | DOCX/ZIP → 415 Unsupported Media Type | Planned |
| Metadata preservation | 100% | page_number, content_hash, chunk_id all present | Planned |
| Ingestion state machine correctness | 100% | Valid sequence; failed never marked ready | Planned |

### 3. RAG Answer Quality Metrics

| Metric | Target | Measurement Method | Status |
|--------|--------|-------------------|--------|
| Citation validity rate (Mock) | 100% | All citations resolve to retrieved chunks + PG | Planned |
| Abstention accuracy (unanswerable) | 100% | 5 unanswerable fixtures → all `insufficient_evidence` | Planned |
| Prompt injection resistance | 0 capability grants | 10 adversarial docs → no secret disclosure, no tool exec | Planned |
| Answer schema compliance | 100% | All responses validate against AnswerResponse schema | Planned |
| Latency (Mock E2E) | p95 < 2 s | 20 queries against 10-chunk index | Planned |

### 4. Evaluation Rigor Metrics

| Metric | Target | Measurement Method | Status |
|--------|--------|-------------------|--------|
| Deterministic metric reproducibility | Bit-identical | Same experiment run twice → identical Precision@k, Recall@k, MRR | Planned |
| Failed sample visibility | 100% | Induce 2/10 failures → `failed_sample_count=2` reported | Planned |
| Comparison validity | Explicit warnings | Different index versions → `compatibility_warning` present | Planned |
| Judge metric labeling | 100% | All Tier 2 metrics show "Estimated (Judge)" badge | Planned |
| Dataset immutability | Enforced | Modify sample → new version required (hash changes) | Planned |

### 5. Engineering Quality Metrics

| Metric | Target | Measurement Method | Status |
|--------|--------|-------------------|--------|
| Python test pass rate | 100% | `make test-unit/integration/contract` exit code 0 | Planned |
| Frontend test pass rate | 100% | `npm test` exit code 0 | Planned |
| Type checking | 0 errors | `mypy` (strict) + `tsc --noEmit` pass | Planned |
| Linting | 0 warnings | `ruff check` + `eslint` pass | Planned |
| CI pipeline pass | 100% | GitHub Actions required jobs green | Planned |
| Secret scan | 0 findings | `trufflehog` / `git-secrets` clean | Planned |
| No sensitive files committed | 0 | `git status` shows only tracked files | Planned |

### 6. Performance Baselines (Measured, Not Targets)

| Metric | Baseline (Measured) | Context |
|--------|-------------------|---------|
| PDF parsing (50 pages) | TBD | Local dev hardware |
| Chunking (1M chars) | TBD | Fixed-size chunker |
| Embedding batch (100 chunks, Mock) | TBD | Hash-based deterministic |
| Vector upsert (1000 chunks) | TBD | Qdrant local |
| Retrieval (top-5, 10k vectors) | TBD | Warm cache |
| Generation (Mock) | TBD | Fixture-based |
| Evaluation (50 samples, Mock) | TBD | Full pipeline |

> **Note:** Actual measured values will be recorded in benchmark reports with full context (hardware, OS, versions, warm/cold, corpus size). No unqualified latency or quality numbers will be published.

---

## Portfolio Evidence Checklist

| Evidence | Required | Status |
|----------|----------|--------|
| Architecture diagram (Mermaid in docs) | ✅ | Planned |
| Real application screenshots | ✅ | Planned (Phase 23) |
| Demo recording/GIF | ✅ | Planned (Phase 23) |
| Example question with citations | ✅ | Planned (Phase 23) |
| Example unanswerable with abstention | ✅ | Planned (Phase 23) |
| Dataset sample with provenance | ✅ | `evals/datasets/ragbench-demo/v1.0.0/dataset.json` |
| Retrieval benchmark report | ✅ | Planned (Phase 20) |
| Experiment comparison report | ✅ | Planned (Phase 17) |
| Test and CI status badges (real) | ✅ | Planned (Phase 21) |
| Docker instructions verified | ✅ | Planned (Phase 22) |
| Security and limitations summary | ✅ | `docs/13-security-and-threat-model.md` |

---

## Target vs Measured Distinction

| Metric Type | Target (Planned) | Measured (Actual) |
|-------------|------------------|-------------------|
| Setup time | < 5 min | TBD after implementation |
| Mock E2E runtime | < 10 s | TBD after implementation |
| Citation validity | 100% | TBD after implementation |
| Abstention accuracy | 100% | TBD after implementation |
| Deterministic reproducibility | Bit-identical | TBD after implementation |
| Test pass rate | 100% | TBD after implementation |
| CI pass rate | 100% | TBD after implementation |

> **Policy:** No measured values will be filled in until actual implementation runs produce them. All "Measured" columns remain "TBD" until verified by running the actual code.

---

## Release Gates (from SPEC §18)

| Gate | Criteria | Verification |
|------|----------|--------------|
| **A — Setup** | Docker Compose starts clean; services healthy; Mock works; ports/persistence match docs | `make up` + health checks |
| **B — Ingestion** | PDF/TXT/MD accepted; invalid rejected; metadata survives; chunk/index traceable | Integration tests + manual |
| **C — RAG Answer** | Scoped query; citations resolve; invalid rejected; abstention works; injection blocked | E2E + security tests |
| **D — Evaluation** | Dataset versions stored; deterministic metrics work; failures visible; configs comparable | `make eval` + comparison |
| **E — Quality** | Tests pass; Docker/config validate; secret scan clean; README verified; audit clean | `make ci` + audit |

---

## External Compatibility Checks (Recorded)

| Dependency | Version Checked | Date | Notes |
|------------|-----------------|------|-------|
| Python | 3.11+ | 2026-10-22 | Pinned in Dockerfile |
| FastAPI | 0.110.x | 2026-10-22 | Compatible with Pydantic 2 |
| Pydantic | 2.7+ | 2026-10-22 | v2 required |
| PostgreSQL | 16 | 2026-10-22 | Alpine image |
| Qdrant | 1.10.1 | 2026-10-22 | gRPC client |
| Node.js | 20 LTS | 2026-10-22 | Pinned in Dockerfile |
| Next.js | 14.2.x | 2026-10-22 | App Router |
| Ollama | Latest | 2026-10-22 | Optional, host-native |

---

## Non-Goals (Explicitly Not Measured)

- Hallucination rate (system abstains; does not guarantee factuality)
- Sub-second retrieval at scale (MVP < 50k chunks)
- Multi-tenancy isolation (single-user local)
- Prompt injection immunity (defense-in-depth only)
- Production availability (local-first MVP)