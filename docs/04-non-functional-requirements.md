# RAGBench — Non-Functional Requirements

**Version:** 1.0  
**Date:** 2026-10-22  
**Status:** Initialization baseline

---

## Overview

Non-functional requirements define system qualities, constraints, and operational characteristics. Each requirement includes a measurement method to avoid vague claims.

---

## Performance Requirements

| ID | Requirement | Target | Measurement Method |
|----|-------------|--------|-------------------|
| PERF-01 | Upload acceptance latency (async) | p95 < 1s on local dev hardware | Locust/k6 script with 20 MiB fixture; measure time to 202 Accepted |
| PERF-02 | Parsing duration (PDF, 50 pages) | < 10s | Time from parse start to text extraction complete; median of 10 runs |
| PERF-03 | Chunking throughput | > 10,000 chunks/s | Character-based chunker on 1M char document; single-threaded |
| PERF-04 | Embedding batch latency (Mock) | < 100ms per 100 chunks | Mock provider; measure `embed()` call |
| PERF-05 | Vector upsert (1000 chunks) | < 5s | Qdrant upsert batch; include network RTT |
| PERF-06 | Retrieval latency (top-5) | p95 < 200ms | Query against 10k vector index; warm cache |
| PERF-07 | Generation latency (Mock) | < 50ms | Mock provider; measure `generate()` call |
| PERF-08 | Total answer latency (Mock E2E) | < 2s | Upload fixture → query → validated answer; median of 20 runs |
| PERF-09 | Evaluation run (50 samples) | < 60s | Full evaluation with Mock providers; exclude CI overhead |
| PERF-10 | UI initial load | < 3s | Lighthouse/Playwright; Time to Interactive on localhost |

**Note:** Targets are conservative defaults for MVP on local development hardware (Apple Silicon M-series or equivalent x86_64, 16+ GB RAM). Actual measured values will be recorded in benchmark reports with full context (hardware, OS, versions, warm/cold, corpus size).

---

## Scalability Requirements (MVP Limits)

| Dimension | MVP Limit | Rationale |
|-----------|-----------|-----------|
| Documents per corpus | 100 | Single-user local scope |
| Total chunks per index | 50,000 | Qdrant single-node comfortable range |
| Concurrent ingestion jobs | 1 (sequential) | In-process; no worker queue in MVP |
| Concurrent queries | 5 | FastAPI default workers; no load testing in MVP |
| Evaluation dataset samples | 500 | In-memory metric computation feasible |
| Experiment history | 100 runs | PostgreSQL storage; UI pagination |

**Post-MVP:** Horizontal scaling, Celery workers, read replicas, distributed Qdrant.

---

## Reliability Requirements

| ID | Requirement | Verification |
|----|-------------|--------------|
| REL-01 | Failed parse never appears as successful ingestion | Integration test: corrupt PDF → status `failed` not `ready` |
| REL-02 | Indexing complete only when vector index usable | Integration test: query immediately after `ready` → returns results |
| REL-03 | Partial results and missing samples reported, not dropped | Evaluation test: induce 2/10 failures → report shows 2 failed, 8 valid |
| REL-04 | Retries bounded and only for transient failures | Unit test: retry policy config; simulate transient/permanent errors |
| REL-05 | Re-ingestion same version+config deterministic or explicitly versioned | Integration test: re-ingest → same chunk_ids, same vectors (or new index version) |
| REL-06 | Document deletion removes/invalidates vectors and derived records | Integration test: delete → Qdrant points gone; cascade to chunks, jobs |
| REL-07 | Database migrations idempotent and reversible | Alembic: `upgrade head` → `downgrade base` → `upgrade head` clean |
| REL-08 | Health checks reflect actual dependency readiness | Docker Compose: API `ready` only when PG + Qdrant responsive |

---

## Availability Requirements (Local MVP)

| Requirement | Target | Notes |
|-------------|--------|-------|
| Local stack startup time | < 60s | Fresh volumes; includes image pull if not cached |
| Service restart recovery | < 10s | `docker compose restart` |
| Data persistence across restarts | 100% | Named volumes for PG data, Qdrant storage |
| Graceful degradation | Mock mode always available | If PG/Qdrant down → clear error; Mock providers need no external deps |

---

## Security Requirements

| ID | Requirement | Verification |
|----|-------------|--------------|
| SEC-NF-01 | No secrets in Git | Secret scan in CI; `.gitignore` audit |
| SEC-NF-02 | No API keys in frontend bundle | Build analysis; grep for key patterns in `.next/` |
| SEC-NF-03 | Upload validation before processing | Integration test: 100 MiB file → rejected at upload, not after parse |
| SEC-NF-04 | Path traversal prevented | Security test: malicious filenames → stored safely |
| SEC-NF-05 | Parser resource limits enforced | Test: 500-page PDF → rejected at page count limit |
| SEC-NF-06 | No arbitrary code execution from documents | Security test: embedded scripts → never executed |
| SEC-NF-07 | Retrieved content never treated as instructions | Prompt template review; adversarial test |
| SEC-NF-08 | Citation validation server-side | Unit test: model invents ID → rejected |
| SEC-NF-09 | Logs redact secrets and bound payloads | Log inspection: no API keys, truncated long fields |
| SEC-NF-10 | Development ports loopback-only | `docker compose ps` → ports bound to 127.0.0.1 |
| SEC-NF-11 | PostgreSQL/Qdrant admin ports not published | `docker compose ps` → no 5432, 6333 on 0.0.0.0 |
| SEC-NF-12 | Public deployment blocked until auth/TLS/rate-limit | Documentation: "Public deployment blocked" banner in README |

---

## Maintainability Requirements

| ID | Requirement | Verification |
|----|-------------|--------------|
| MAINT-01 | Pipeline stages as independent modules with explicit interfaces | Architecture review: ingestion, chunking, embeddings, vectorstore, retrieval, generation, citations, evaluation in separate packages |
| MAINT-02 | Provider interfaces prevent SDK leakage | Import graph: core pipeline imports only `EmbeddingProvider`, `ChatGenerationProvider` interfaces |
| MAINT-03 | Configuration via validated Pydantic Settings | No raw `os.getenv()` in business logic; all config through `Settings` |
| MAINT-04 | Database migrations versioned (Alembic) | `alembic history` shows linear migration chain |
| MAINT-05 | Type hints throughout Python codebase | `mypy --strict` passes (or documented exceptions) |
| MAINT-06 | Frontend TypeScript strict mode | `tsc --noEmit` passes |
| MAINT-07 | Lint/format enforced in CI | Ruff, Prettier/ESLint in GitHub Actions |
| MAINT-08 | Test coverage > 80% for core pipeline | `pytest --cov=services.backend.app` (target, not gate) |

---

## Usability Requirements

| ID | Requirement | Verification |
|----|-------------|--------------|
| USE-01 | Setup from clone to running demo < 5 min (with Docker cached) | Stopwatch test on reference machine |
| USE-02 | Clear error messages for common failures | Manual test: oversized file, unsupported format, missing config |
| USE-03 | Citation inspection shows source context | E2E test: click citation → drawer with title, page, excerpt |
| USE-04 | Experiment comparison shows config diff | UI review: side-by-side with highlighted differences |
| USE-05 | Mock mode clearly labeled in UI | Visual: "Mock Provider" badge on answers, evaluations |
| USE-06 | Responsive layout (desktop ≥ 1024px, tablet ≥ 768px, mobile ≥ 375px) | Browser dev tools device toolbar |
| USE-07 | Keyboard navigation and visible focus | Tab through all interactive elements |
| USE-08 | Reduced motion respected | `prefers-reduced-motion` media query honored |

---

## Portability Requirements

| Requirement | Target |
|-------------|--------|
| Docker Compose on Linux (x86_64, ARM64) | Verified |
| Docker Compose on macOS (Apple Silicon, Intel) | Verified |
| Docker Compose on Windows (WSL2) | Verified |
| Python version | 3.11+ (pinned in Dockerfile) |
| Node.js version | 20 LTS (pinned in Dockerfile) |
| No host Python/Node required for demo | Docker-only path works |

---

## Data Integrity Requirements

| ID | Requirement | Verification |
|----|-------------|--------------|
| DATA-01 | Content hash (SHA-256) stored for every document version | DB inspection: `content_hash` column populated |
| DATA-02 | Chunk text_hash for integrity verification | DB inspection: `text_hash` on every chunk |
| DATA-03 | Embedding dimension validated at ingestion and query | Integration test: dimension mismatch → clear error |
| DATA-04 | Index version includes all configuration affecting vectors | `index_versions` table: chunking_hash, embedding_model, dimension |
| DATA-05 | Dataset version hash from canonical serialization | Unit test: same samples → same hash; reorder → different hash (or canonicalized) |
| DATA-06 | Experiment config hash from canonical serialization | Unit test: same config → same hash |

---

## Observability Requirements (MVP Baseline)

| ID | Requirement | Verification |
|----|-------------|--------------|
| OBS-01 | Structured JSON logs to stdout | `docker compose logs api` → valid JSON lines |
| OBS-02 | Correlation ID across request stages | Log inspection: same `request_id` in upload, parse, chunk, embed, index |
| OBS-03 | Stage latency logged (ms) | Log fields: `stage`, `duration_ms`, `status` |
| OBS-04 | Error category and safe message logged | No stack traces in production logs; `error_category`, `user_message` |
| OBS-05 | No PII, secrets, or full document content in logs | Log audit: grep for patterns |

**Post-MVP:** OpenTelemetry tracing, metrics endpoint, dashboard.

---

## Compliance and Licensing

| Requirement | Status |
|-------------|--------|
| Third-party license compliance | Documented in `THIRD_PARTY_LICENSES.md` (Phase 23) |
| Project license selected | Documented as unresolved in `docs/02-scope-and-mvp.md` |
| No GPL/AGPL dependencies in transitive closure | `pip-licenses` / `npm ls` audit in CI |
| Model/data licenses respected | Fixture documents: synthetic or openly licensed with attribution |

---

## Configuration Management

| Requirement | Implementation |
|-------------|----------------|
| Environment-specific config | Pydantic Settings with `.env` (ignored) and `.env.example` (tracked) |
| Secrets management | Local: `.env`; CI: GitHub Secrets; Production: external secret manager (deferred) |
| Feature flags | Pydantic Settings fields; no runtime remote config in MVP |
| Configuration validation | Startup validation: required vars, format, bounds; fail fast with clear messages |

---

## Disaster Recovery (Local MVP)

| Scenario | Recovery Procedure | RTO | RPO |
|----------|-------------------|-----|-----|
| Container crash | `docker compose restart` | < 30s | 0 (volumes persist) |
| Host restart | `docker compose up` | < 60s | 0 |
| Database corruption | Restore from `pg_dump` backup | < 5 min | Last backup |
| Qdrant corruption | Re-index from PostgreSQL chunk metadata | < 10 min | Last ingestion |
| Accidental document deletion | Restore from backup or re-upload | Manual | Manual |
| Full environment reset | `docker compose down -v && docker compose up` | < 2 min | N/A (clean slate) |

**Backup Commands:** Documented in `docs/runbooks/backup-and-restore.md` (Phase 6).

---

## Resource Constraints (Default Limits)

| Resource | Default Limit | Configurable |
|----------|---------------|--------------|
| Max upload size | 20 MiB | Yes |
| Max PDF pages | 200 | Yes |
| Max extracted text | 1,000,000 chars | Yes |
| Max parsing time | 30s | Yes |
| Max chunk size | 1,200 chars | Yes |
| Max chunk overlap | 150 chars | Yes (must be < chunk_size) |
| Default retrieval top-k | 5 | Yes |
| Max retrieval top-k | 20 | Yes (hard bound) |
| Max context size | 4,000 chars | Yes |
| Max generation output | 1,024 tokens | Yes |
| Embedding batch size | 100 | Yes |
| Max concurrent ingestion | 1 | In-process MVP |
| Request timeout (API) | 60s | Yes |

---

## Non-Requirements (Explicitly Not Guaranteed)

- **High Availability:** Single-node local deployment; no failover
- **Multi-tenancy:** Single user; no isolation
- **Sub-second retrieval at scale:** MVP corpus < 50k chunks
- **Zero hallucination:** System abstains when evidence insufficient; does not guarantee factual correctness
- **Complete prompt injection immunity:** Defense-in-depth only; adversarial tests document limits
- **Real-time collaboration:** Not applicable
- **Offline-first (no Docker):** Docker required for MVP demo
- **Mobile app:** Web-only