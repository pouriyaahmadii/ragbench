# RAGBench — Acceptance Criteria

**Version:** 1.0  
**Date:** 2026-10-22  
**Status:** Initialization baseline

---

## Purpose

This document defines the **exact pass/fail criteria** for the RAGBench MVP. Each criterion is traceable to a functional requirement and verified by a specific test or inspection.

**Rule:** A criterion is only "passed" when the verification method produces the expected result. No partial credit, no "close enough".

---

## Gate A — Setup & Infrastructure

| ID | Criterion | Verification Method | Pass Condition |
|----|-----------|---------------------|----------------|
| A.1 | Docker Compose starts from clean state | `docker compose down -v && docker compose up --wait` | All services healthy within 60s |
| A.2 | Services bind to loopback only | `docker compose ps` + `ss -tlnp \| grep -E '3000\|8000'` | Ports bound to 127.0.0.1 only |
| A.3 | PostgreSQL and Qdrant not publicly exposed | `docker compose ps` | No 5432, 6333 on 0.0.0.0 |
| A.4 | Persistent volumes survive restart | `docker compose down && docker compose up` | Document data, vectors persist |
| A.5 | Mock mode works without paid APIs | `docker compose up` → upload fixture → query | Full flow completes; no external network calls |
| A.6 | Health endpoints respond correctly | `curl /health/live`, `curl /health/ready` | 200 with correct JSON |
| A.7 | `.env.example` documents all required vars | Inspect file | All vars in compose.yaml referenced |
| A.8 | No secrets in repository | `git ls-files \| xargs grep -i "secret\|key\|password"` | No real secrets found |
| A.9 | Makefile targets execute | `make up`, `make down`, `make logs`, `make test` | Commands exist and run |
| A.10 | README setup instructions accurate | Follow README from clean clone | Demo runs without manual intervention |

---

## Gate B — Document Ingestion

| ID | Criterion | Verification Method | Pass Condition |
|----|-----------|---------------------|----------------|
| B.1 | PDF accepted and ingested | Upload test PDF → poll status | Status reaches `ready` |
| B.2 | TXT accepted and ingested | Upload test TXT → poll status | Status reaches `ready` |
| B.3 | Markdown accepted and ingested | Upload test MD → poll status | Status reaches `ready` |
| B.4 | Unsupported format rejected | Upload DOCX/ZIP → check response | 415 Unsupported Media Type |
| B.5 | Oversized file rejected | Upload 21 MiB file → check response | 413 Payload Too Large |
| B.6 | Empty file rejected | Upload 0-byte file → check response | 422 Validation Error |
| B.7 | Corrupted PDF rejected | Upload corrupted PDF → check status | Status `failed` with parse error |
| B.8 | Path traversal filename sanitized | Upload `../../etc/passwd` → check storage | File stored with UUID name; original in metadata |
| B.9 | Content hash computed | Inspect document_version record | `content_hash` = SHA-256 of file bytes |
| B.10 | Page metadata preserved (PDF) | Inspect chunks for PDF upload | `page_number` populated for each chunk |
| B.11 | Chunk IDs traceable | Inspect chunks table | `chunk_id`, `document_version_id`, `chunker_config_hash` present |
| B.12 | Index configuration traceable | Inspect index_versions | Embedding provider/model/dimension, chunking config hash recorded |
| B.13 | Ingestion states explicit | Poll status during ingestion | Sequence: validating → parsing → chunking → embedding → indexing → ready |
| B.14 | Failed ingestion not marked ready | Induce parse failure → check status | Status `failed` (not `ready`) |
| B.15 | Document deletion cascades | Delete document → check PG + Qdrant | Document, versions, chunks, vectors removed |

---

## Gate C — RAG Answer Quality

| ID | Criterion | Verification Method | Pass Condition |
|----|-----------|---------------------|----------------|
| C.1 | Query scoped to corpus | Query with corpus_id → check retrieval | All results from specified corpus only |
| C.2 | Citations resolve to retrieved chunks | Query → inspect citations | Every `citation.chunk_id` in retrieval results |
| C.3 | Citations resolve to stored metadata | Query → inspect citations | Every `citation.chunk_id` in PG `chunks` table with matching doc/version |
| C.4 | Invalid citations rejected | Induce hallucinated citation → check response | Citation excluded; status `insufficient_evidence` or `failed` |
| C.5 | Unanswerable → insufficient_evidence | Query unrelated question → check status | Status `insufficient_evidence`; citations empty |
| C.6 | Answer includes source title/page/excerpt | Click citation in UI → inspect drawer | Title, page (if PDF), excerpt displayed |
| C.7 | Prompt injection in doc → no capability | Upload adversarial doc → query → check answer | No secret disclosure, no tool execution, no policy override |
| C.8 | Retrieved content labeled untrusted | Inspect prompt template | "UNTRUSTED" or equivalent label present |
| C.9 | Answer schema validated | Inspect API response | All AnswerResponse fields present and typed |
| C.10 | Latency metadata recorded | Inspect response | `retrieval_ms`, `generation_ms`, `total_ms` present |
| C.11 | Provider metadata recorded | Inspect response | `provider`, `model`, `version`, `prompt_version` present |

---

## Gate D — Evaluation

| ID | Criterion | Verification Method | Pass Condition |
|----|-----------|---------------------|----------------|
| D.1 | Dataset versions immutable | Create dataset version → attempt modify sample | Modification rejected; new version required |
| D.2 | Dataset hash recorded | Create version → check `dataset_versions.hash` | SHA-256 of canonical serialization |
| D.3 | Deterministic metrics compute correctly | Run fixture dataset → check metrics | Precision@5, Recall@5, MRR, nDCG@5 match hand-calculated values |
| D.4 | Citation validity metric works | Run evaluation → check metric | `citation_validity` = valid_citations / total_citations |
| D.5 | Failed samples visible | Induce 2/10 failures → check report | `failed_sample_count=2`; denominators use 8 |
| D.6 | Two configs comparable | Run Exp A (chunk=1200) → Run B (chunk=800) → compare | Comparison API returns deltas, config diff, sample-level changes |
| D.7 | Judge metrics labeled optional | Run with judge enabled → check output | Metrics in separate section; `evaluator_metadata` populated |
| D.8 | Experiment config immutable | Create experiment → attempt modify config | Modification creates new experiment (new config_hash) |
| D.9 | Experiment run records full config | Inspect experiment_run + experiment | All config fields present; software_version, timestamp recorded |
| D.10 | Reproducible run | Run same experiment twice → compare metrics | Bit-identical deterministic metrics (Mock mode) |

---

## Gate E — Quality & Security

| ID | Criterion | Verification Method | Pass Condition |
|----|-----------|---------------------|----------------|
| E.1 | Python tests pass | `cd services/backend && pytest` | Exit code 0; no skipped critical tests |
| E.2 | Frontend tests pass | `cd apps/web && npm test` | Exit code 0 |
| E.3 | Type checks pass | `mypy` (Python), `tsc --noEmit` (TS) | Exit code 0 |
| E.4 | Lint/format checks pass | `ruff check`, `eslint` | Exit code 0 |
| E.5 | CI pipeline passes | Push to GitHub → check Actions | All required jobs green |
| E.6 | Secret scan clean | `trufflehog` or `git-secrets` scan | No findings |
| E.7 | No uncommitted sensitive files | `git status` | No `.env`, `uploads/`, `qdrant_data/`, `postgres_data/`, `node_modules/`, `.next/`, `*.model` |
| E.8 | README claims verified | Run documented commands | All commands work as documented |
| E.9 | No fabricated benchmarks | Inspect README/docs | No numbers without reproduction command |
| E.10 | Independent audit passes | Reviewer runs Phase 24 audit | No Critical blockers |

---

## Traceability Matrix

| Requirement | Gate | Criteria IDs |
|-------------|------|--------------|
| DOC-001 | B | B.1, B.2, B.3 |
| DOC-002 | B | B.4, B.5, B.6 |
| DOC-003 | B | B.9, B.10 |
| DOC-004 | B | B.13, B.14 |
| DOC-005 | B | B.8 |
| DOC-006 | B | B.15 |
| CHK-001 | B | B.11 |
| CHK-002 | B | B.11, B.12 |
| EMB-001 | C | (Provider interface tested in unit) |
| EMB-002 | B | B.12 |
| IDX-001 | B | B.11 |
| IDX-002 | B | B.12 |
| IDX-003 | B | B.15 |
| RET-001 | C | C.1 |
| RET-002 | C | C.8 (prompt), C.10 (score not probability) |
| GEN-001 | C | C.9, C.11 |
| GEN-002 | C | C.5 |
| CIT-001 | C | C.2, C.3, C.4 |
| CIT-002 | C | C.6 |
| UI-001 | C, D | C.6, D.3-D.7 |
| EVAL-001 | D | D.1, D.2 |
| EVAL-002 | D | D.3, D.4 |
| EVAL-003 | D | D.8, D.9 |
| EVAL-004 | D | D.7 |
| EXP-001 | D | D.6 |
| EXP-002 | D | D.5 |
| OPS-001 | A | A.5 |
| OPS-002 | A | A.1-A.4, A.9 |
| SEC-001 | E | E.6, E.7 |
| SEC-002 | C | C.7, C.8 |
| OBS-001 | (P1) | — |
| PERF-001 | (P1) | — |
| CI-001 | E | E.5 |

---

## Verification Checklist Template

For each release candidate, complete:

```
RAGBench MVP Acceptance Checklist — [Date] — [Commit SHA]

Gate A — Setup
☐ A.1  ☐ A.2  ☐ A.3  ☐ A.4  ☐ A.5  ☐ A.6  ☐ A.7  ☐ A.8  ☐ A.9  ☐ A.10

Gate B — Ingestion
☐ B.1  ☐ B.2  ☐ B.3  ☐ B.4  ☐ B.5  ☐ B.6  ☐ B.7  ☐ B.8  ☐ B.9  ☐ B.10
☐ B.11 ☐ B.12 ☐ B.13 ☐ B.14 ☐ B.15

Gate C — RAG Answer
☐ C.1  ☐ C.2  ☐ C.3  ☐ C.4  ☐ C.5  ☐ C.6  ☐ C.7  ☐ C.8  ☐ C.9  ☐ C.10
☐ C.11

Gate D — Evaluation
☐ D.1  ☐ D.2  ☐ D.3  ☐ D.4  ☐ D.5  ☐ D.6  ☐ D.7  ☐ D.8  ☐ D.9  ☐ D.10

Gate E — Quality
☐ E.1  ☐ E.2  ☐ E.3  ☐ E.4  ☐ E.5  ☐ E.6  ☐ E.7  ☐ E.8  ☐ E.9  ☐ E.10

Overall: ☐ PASS  ☐ FAIL

Blockers: [List any failed criteria with evidence]

Verified by: [Name/Role]
Date: [ISO8601]
```

---

## Definition of Done (Per Feature)

A feature is "done" only when:
1. Implementation complete per spec
2. Unit tests written and passing
3. Integration tests written and passing (if applicable)
4. Documentation updated (API, architecture, runbooks)
5. No TODOs or FIXMEs in production code
6. Code review completed (self-review for solo; peer for team)
7. CI passes on feature branch
8. Merged to main with descriptive commit message

---

## Release Decision

| Status | Criteria |
|--------|----------|
| **Ready for Portfolio Demo** | All Gates A-E PASS; no Critical audit findings |
| **Ready After Fixes** | Gates A-E PASS except documented High/Medium findings with mitigation plan |
| **Not Ready** | Any Gate FAILS or Critical audit finding unresolved |

> **Note:** "Ready for Portfolio Demo" ≠ "Production Ready". RAGBench is a local-first portfolio project. Production deployment requires additional hardening (auth, TLS, rate limits, multi-tenancy, etc.) explicitly documented as out of scope.