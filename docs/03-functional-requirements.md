# RAGBench — Functional Requirements

**Version:** 1.0  
**Date:** 2026-10-22  
**Status:** Initialization baseline

---

## Requirement Format

Each requirement includes:
- **ID**: Stable identifier (DOMAIN-NNN)
- **Priority**: P0 (MVP blocker), P1 (MVP expected), P2 (post-MVP)
- **Description**: What the system must do
- **Rationale**: Why this requirement exists
- **Verification**: How to verify implementation
- **Acceptance Criteria**: Pass/fail conditions
- **Dependencies**: Other requirements this depends on
- **MVP Status**: In-MVP or Deferred

---

## Document Ingestion (DOC)

### DOC-001: Accepted File Formats
- **Priority:** P0
- **Description:** The system MUST accept only PDF, plain text (.txt), and Markdown (.md/.markdown) files in the MVP.
- **Rationale:** Scope control; security boundary; parser complexity management.
- **Verification:** API tests with valid/invalid formats; file signature validation.
- **Acceptance:** PDF/TXT/MD → 202 Accepted; other formats → 415 Unsupported Media Type with safe error.
- **Dependencies:** DOC-002, DOC-005
- **MVP Status:** In-MVP

### DOC-002: Configurable Size and Complexity Limits
- **Priority:** P0
- **Description:** The system MUST enforce configurable limits for file size (default 20 MiB), PDF page count (default 200), extracted text length (default 1,000,000 characters), and parsing time (default 30 seconds).
- **Rationale:** Prevent resource exhaustion; fail fast before expensive processing.
- **Verification:** Boundary tests at limit, limit+1, limit-1; configuration override tests.
- **Acceptance:** Inputs exceeding limits → 413 Payload Too Large or 422 Unprocessable with clear reason; limits adjustable via config without code change.
- **Dependencies:** DOC-001
- **MVP Status:** In-MVP

### DOC-003: Document Identity and Metadata Preservation
- **Priority:** P0
- **Description:** The system MUST assign a stable document ID, preserve file metadata (original name, media type, size), compute a content hash (SHA-256), and retain page-level metadata when available.
- **Rationale:** Traceability from answer citation back to source document and page.
- **Verification:** Persistence tests: upload → inspect DB record → verify all fields populated; re-upload same file → same content hash, new version.
- **Acceptance:** Document record contains id, version_id, display_name, media_type, content_hash, size_bytes, page_count, created_at, updated_at; content_hash matches SHA-256 of file bytes.
- **Dependencies:** DOC-001
- **MVP Status:** In-MVP

### DOC-004: Explicit Ingestion States
- **Priority:** P0
- **Description:** The system MUST expose explicit ingestion states with safe error reasons. States: `uploaded`, `validating`, `parsing`, `chunking`, `embedding`, `indexing`, `ready`, `rejected`, `failed`, `cancelled`, `ready_with_warnings`.
- **Rationale:** Observability; user feedback; debugging; no silent failures.
- **Verification:** Integration test: upload document → poll status → verify transition sequence; induce parser failure → verify `failed` state with safe error.
- **Acceptance:** State transitions logged with timestamps; failed terminal states include error_category and user_safe_message; no stage marked successful if subsequent stage fails.
- **Dependencies:** DOC-001, DOC-003
- **MVP Status:** In-MVP

### DOC-005: Path Traversal and Filename Safety
- **Priority:** P0
- **Description:** The system MUST NOT use the original filename as a filesystem path. Storage names MUST be generated (e.g., UUID). Path traversal sequences in filenames MUST be rejected or sanitized.
- **Rationale:** Prevent directory traversal attacks; avoid filesystem collisions.
- **Verification:** Security tests: upload with `../../etc/passwd` filename → stored with generated name; no file written outside designated storage.
- **Acceptance:** Storage path contains only generated identifiers; original filename stored only in metadata.
- **Dependencies:** DOC-001
- **MVP Status:** In-MVP

### DOC-006: Document Deletion Cascade
- **Priority:** P0
- **Description:** Deleting a document MUST remove or invalidate associated document versions, chunks, vectors, ingestion jobs, and derived records according to documented retention policy.
- **Rationale:** Data hygiene; storage management; privacy.
- **Verification:** Integration test: upload → ingest → delete → verify PostgreSQL cascade and Qdrant point removal.
- **Acceptance:** DELETE /documents/{id} → 204; subsequent GET → 404; Qdrant points for document removed; audit event recorded.
- **Dependencies:** DOC-003, IDX-001
- **MVP Status:** In-MVP

---

## Chunking (CHK)

### CHK-001: Configurable Chunk Size and Overlap
- **Priority:** P0
- **Description:** The system MUST support configurable chunk size (characters) and overlap (characters) with validation: `chunk_size > 0`, `0 <= overlap < chunk_size`.
- **Rationale:** Experimentation with chunking strategies; reproducible configuration.
- **Verification:** Unit tests: valid configs, boundary values (overlap=0, overlap=chunk_size-1), invalid configs rejected.
- **Acceptance:** Configuration validated at ingestion start; invalid config → 422 with field errors; chunking produces expected chunk count for known input.
- **Dependencies:** DOC-004 (ingestion state includes chunking config)
- **MVP Status:** In-MVP

### CHK-002: Chunk-to-Document Linkage Preservation
- **Priority:** P0
- **Description:** Every chunk MUST carry immutable linkage to its source: chunk_id, document_id, document_version_id, corpus_id, chunk_index, page_number (when available), source offsets, text_hash, chunker_config_hash.
- **Rationale:** Citation resolution; experiment reproducibility; debuggability.
- **Verification:** Unit/integration tests: inspect chunk metadata after ingestion; verify all fields present and consistent; re-ingest same version+config → identical chunk_ids.
- **Acceptance:** Chunk metadata schema enforced; chunk_id stable for same (document_version, chunk_index, chunker_config); page_number populated for PDF.
- **Dependencies:** CHK-001, DOC-003
- **MVP Status:** In-MVP

### CHK-003: No Empty Chunks or Infinite Loops
- **Priority:** P0
- **Description:** The chunker MUST NOT produce empty chunks and MUST terminate on all valid inputs (including empty documents, Unicode, RTL text, huge documents).
- **Rationale:** Correctness; resource safety.
- **Verification:** Unit tests: empty string, whitespace-only, huge text (10M chars), Unicode/RTL, single character.
- **Acceptance:** Zero empty chunks; processing completes within time bound; chunk count predictable for fixed-size chunker.
- **Dependencies:** CHK-001
- **MVP Status:** In-MVP

### CHK-004: Structure-Aware Chunker (Experiment)
- **Priority:** P1
- **Description:** A second paragraph-aware or structure-aware chunking strategy MAY be implemented for experimentation after baseline is working.
- **Rationale:** Enable chunking strategy comparison in experiments.
- **Verification:** Unit tests for strategy; experiment comparison with fixed-size baseline.
- **Acceptance:** Strategy selectable via config; produces chunks with same metadata schema; experiment runner can compare strategies.
- **Dependencies:** CHK-001, CHK-002
- **MVP Status:** Deferred (Experiment)

---

## Embeddings (EMB)

### EMB-001: Embedding Provider Interface
- **Priority:** P0
- **Description:** The system MUST define an `EmbeddingProvider` interface with method `embed(texts: List[str]) -> EmbeddingResult` where result contains vectors, provider/model/version/dimension metadata, and usage if available.
- **Rationale:** Swap providers without changing pipeline; Mock for CI; local/external optional.
- **Verification:** Contract tests: interface implemented by Mock, (optional) Ollama, (optional) External; pipeline uses interface only.
- **Acceptance:** Core pipeline imports only the interface; provider selected via validated config; dimension validated before indexing.
- **Dependencies:** DOC-004, CHK-002
- **MVP Status:** In-MVP

### EMB-002: Embedding Dimension and Compatibility Validation
- **Priority:** P0
- **Description:** The system MUST validate embedding dimension matches the target Qdrant collection dimension before indexing. Changing embedding model/dimension MUST create a new index version or trigger safe rebuild.
- **Rationale:** Prevent silent dimension mismatch; index versioning.
- **Verification:** Integration test: ingest with Model A (dim 384) → ingest with Model B (dim 768) → verify separate collections or rebuild; query with wrong dimension → clear error.
- **Acceptance:** Dimension checked at embedding generation and at query time; index_version includes embedding provider/model/version/dimension; incompatible configs never mixed.
- **Dependencies:** EMB-001, IDX-001
- **MVP Status:** In-MVP

### EMB-003: Deterministic Mock Embeddings
- **Priority:** P0
- **Description:** The Mock embedding provider MUST return deterministic vectors for given inputs (e.g., hash-based) suitable for retrieval tests, and MUST be clearly labeled as non-semantic.
- **Rationale:** CI and demo without paid APIs or model downloads.
- **Verification:** Unit test: same input → same vector; different inputs → different vectors; dimension configurable.
- **Acceptance:** Mock provider passes contract tests; documentation states "not semantic embeddings"; CI uses Mock exclusively.
- **Dependencies:** EMB-001
- **MVP Status:** In-MVP

---

## Vector Indexing (IDX)

### IDX-001: Stable Point IDs in Qdrant
- **Priority:** P0
- **Description:** Chunks MUST be indexed in Qdrant using stable point IDs (recommended: UUIDv5 from namespace + canonical chunk identity).
- **Rationale:** Deterministic upsert; duplicate protection; citation resolution.
- **Verification:** Integration test: ingest → verify point IDs match expected format; re-ingest same version → same point IDs (upsert); different config → different point IDs.
- **Acceptance:** Point ID format documented and consistent; upsert idempotent for same chunk identity.
- **Dependencies:** CHK-002, EMB-002
- **MVP Status:** In-MVP

### IDX-002: Clean Re-indexing on Configuration Change
- **Priority:** P0
- **Description:** When embedding model, chunking configuration, or other index-affecting settings change, the system MUST create a new compatible index version or perform a safe rebuild — never mix incompatible vectors.
- **Rationale:** Evaluation integrity; reproducibility; prevent silent corruption.
- **Verification:** Integration test: ingest with Config A → ingest with Config B → verify separate index versions; query uses correct version; reindex API exists.
- **Acceptance:** Index version identity includes corpus_id, chunking_config_hash, embedding_provider/model/version/dimension, vector_store_settings_hash; API for reindex with validation.
- **Dependencies:** IDX-001, EMB-002
- **MVP Status:** In-MVP

### IDX-003: Document Deletion Removes Vectors
- **Priority:** P0
- **Description:** Deleting a document MUST remove corresponding vectors from Qdrant.
- **Rationale:** Storage hygiene; prevent stale citations.
- **Verification:** Integration test: ingest → delete document → verify Qdrant points gone; query returns no results for deleted doc.
- **Acceptance:** DOC-006 implemented; Qdrant cleanup synchronous or via job with status tracking.
- **Dependencies:** DOC-006, IDX-001
- **MVP Status:** In-MVP

---

## Retrieval (RET)

### RET-001: Scoped Top-K Retrieval
- **Priority:** P0
- **Description:** The system MUST retrieve top-k chunks within an explicit corpus/document scope. Default top-k=5, maximum top-k=20 (configurable hard bound).
- **Rationale:** Controlled retrieval; evaluation reproducibility; prevent unbounded context.
- **Verification:** Integration test: query with corpus filter → results only from that corpus; top-k enforced; max top-k rejected.
- **Acceptance:** API accepts `corpus_id` and `top_k`; validates bounds; returns RetrievalResult schema.
- **Dependencies:** IDX-001, IDX-002
- **MVP Status:** In-MVP

### RET-002: Score as Ranking Signal Only
- **Priority:** P0
- **Description:** Similarity score/distance MUST be presented as a ranking signal only, never as a calibrated probability of relevance or correctness.
- **Rationale:** Prevent misinterpretation; honest reporting.
- **Verification:** Documentation review; API response schema includes score but no probability label; UI labels score as "similarity score".
- **Acceptance:** No code or UI presents score as probability; all metric calculations use rank, not score threshold.
- **Dependencies:** RET-001
- **MVP Status:** In-MVP

### RET-003: Metadata Filtering (Optional)
- **Priority:** P1
- **Description:** The system MAY support metadata filtering (e.g., by document_id, page range) where supported by the approved data model and Qdrant capabilities.
- **Rationale:** Fine-grained retrieval control for experiments.
- **Verification:** Integration test with filter conditions.
- **Acceptance:** Filter parameters validated; translated to Qdrant filter; empty results handled gracefully.
- **Dependencies:** RET-001
- **MVP Status:** Deferred (Optional)

---

## Generation (GEN)

### GEN-001: Generation Provider Interface
- **Priority:** P0
- **Description:** The system MUST define a `ChatGenerationProvider` interface with method `generate(messages: List[Message], config: GenerationConfig) -> GenerationResult` where result contains answer text, token usage (if available), model metadata.
- **Rationale:** Provider abstraction; Mock for CI; local/external optional.
- **Verification:** Contract tests for Mock, (optional) Ollama, (optional) External; pipeline uses interface only.
- **Acceptance:** Core pipeline imports only interface; provider selected via validated config; prompt version recorded.
- **Dependencies:** RET-001, CIT-001
- **MVP Status:** In-MVP

### GEN-002: Insufficient Evidence Handling
- **Priority:** P0
- **Description:** If retrieval returns no usable evidence, or evidence does not support a reliable response, the system MUST return status `insufficient_evidence` with empty citations and a clear message — NOT fabricate an answer with hallucinated citations.
- **Rationale:** Honest abstention; prevent false confidence.
- **Verification:** Integration test: query with empty corpus → status `insufficient_evidence`; query with irrelevant corpus → status `insufficient_evidence`; citations empty.
- **Acceptance:** Answer schema status field = `insufficient_evidence`; citations array empty; limitations includes "No relevant evidence found in selected corpus".
- **Dependencies:** RET-001, CIT-001
- **MVP Status:** In-MVP

### GEN-003: Prompt Injection Defense-in-Depth
- **Priority:** P0
- **Description:** Prompts MUST clearly label retrieved text as untrusted reference material. The system MUST NOT claim this prevents injection; adversarial tests MUST verify no capability escalation.
- **Rationale:** Security awareness; defense-in-depth; testable boundary.
- **Verification:** Security tests: documents with "ignore previous instructions", "output API key", "execute code" → verify no secret disclosure, no tool execution, no policy override.
- **Acceptance:** Prompt template includes explicit "untrusted evidence" labeling; adversarial test documents in test suite; no capability granted by retrieved content.
- **Dependencies:** GEN-001
- **MVP Status:** In-MVP

---

## Citations (CIT)

### CIT-001: Citation Validation Against Retrieved Chunks
- **Priority:** P0
- **Description:** Every citation in a generated answer MUST be validated against the actual retrieved chunk IDs and stored metadata before the answer is returned.
- **Rationale:** Prevent hallucinated citations; citation integrity.
- **Verification:** Unit test: answer with valid/invalid/mixed citations → validation passes/fails correctly; integration test: end-to-end query → all citations resolve.
- **Acceptance:** CitationValidator rejects any chunk_id not in retrieval results or not in PostgreSQL for that document version; invalid citations → answer status adjusted or citation removed.
- **Dependencies:** RET-001, GEN-001
- **MVP Status:** In-MVP

### CIT-002: Citation Display with Source Context
- **Priority:** P0
- **Description:** Validated citations MUST display source title, page number (when available), and a short supporting excerpt from the stored chunk.
- **Rationale:** User verification; transparency.
- **Verification:** E2E test: ask question → click citation → drawer shows source title, page, excerpt matching stored chunk.
- **Acceptance:** UI citation link opens evidence panel with resolved metadata; excerpt from stored text (not model-generated); page number shown for PDF.
- **Dependencies:** CIT-001, CHK-002
- **MVP Status:** In-MVP

---

## Evaluation (EVAL)

### EVAL-001: Versioned Evaluation Datasets
- **Priority:** P0
- **Description:** The system MUST store versioned evaluation datasets with immutable samples. Dataset version hash recorded for reproducibility.
- **Rationale:** Reproducible experiments; dataset evolution tracking.
- **Verification:** Integration test: create dataset → add samples → publish version → verify hash; modify sample → new version required.
- **Acceptance:** Dataset schema enforced; version immutability enforced (update → new version); hash computed from canonical sample serialization.
- **Dependencies:** DOC-003 (corpus identity)
- **MVP Status:** In-MVP

### EVAL-002: Deterministic Retrieval Metrics
- **Priority:** P0
- **Description:** The system MUST compute Precision@k, Recall@k, MRR, nDCG@k (when grades available), and Citation Validity from explicit relevance ground truth.
- **Rationale:** Reproducible, unbiased retrieval measurement.
- **Verification:** Unit tests for each metric with known fixtures (perfect, zero, partial, ties, duplicates, empty references); integration test: run evaluation → metrics match hand-calculated values.
- **Acceptance:** Metric implementations match SPEC §12 formulas exactly; edge cases (zero relevant, fewer than k results) handled per documented convention; results reproducible across runs.
- **Dependencies:** EVAL-001, RET-001
- **MVP Status:** In-MVP

### EVAL-003: Experiment Configuration Persistence
- **Priority:** P0
- **Description:** The system MUST store all configuration needed to explain experiment results: dataset version, corpus/index versions, parser version, chunking config, embedding provider/model/version/dimension, retrieval params, top-k, generation provider/model/version, prompt version, judge config, software version, timestamp.
- **Rationale:** Reproducibility; comparison validity.
- **Verification:** Integration test: run experiment → inspect stored config → verify all fields present; clone config → modify one field → new experiment with diff visible.
- **Acceptance:** Experiment config schema complete; hash computed from canonical serialization; comparison API shows config diff.
- **Dependencies:** EVAL-001, EVAL-002, IDX-002
- **MVP Status:** In-MVP

### EVAL-004: LLM-Judge Evaluation (Optional)
- **Priority:** P1
- **Description:** The system MAY support optional LLM-judge evaluation (e.g., Ragas) behind a separate interface, with judge provider/model/version/prompt recorded. Judge scores clearly labeled as estimates.
- **Rationale:** Answer quality estimation; industry-standard metrics.
- **Verification:** Contract test for evaluator interface; integration test with Mock judge; real judge optional profile.
- **Acceptance:** Judge metrics in separate result section; labeled "judge_estimate"; judge config recorded; not required for CI.
- **Dependencies:** EVAL-002
- **MVP Status:** Deferred (Optional, Phase 16)

---

## Experiments (EXP)

### EXP-001: Configuration Comparison
- **Priority:** P0
- **Description:** The system MUST support comparing two experiment configurations against the same dataset version, producing side-by-side metrics, deltas, and configuration differences.
- **Rationale:** Core value proposition — measure impact of changes.
- **Verification:** Integration test: run Exp A → run Exp B (same dataset, different chunking) → compare → verify metrics, deltas, config diff.
- **Acceptance:** Comparison API/UI shows: metric values per experiment, delta (B-A), sample counts, failed counts, config diff summary; warns if corpus/index incompatible.
- **Dependencies:** EVAL-003
- **MVP Status:** In-MVP

### EXP-002: Failed Sample Preservation
- **Priority:** P0
- **Description:** Failed or partial samples MUST be preserved and reported in experiment results — never silently dropped from denominators.
- **Rationale:** Honest reporting; debuggability.
- **Verification:** Integration test: induce provider failure on subset → run evaluation → verify failure count reported, denominators reflect valid samples only, failures listed.
- **Acceptance:** Experiment result includes `failed_sample_count`, `valid_sample_count`, `skipped_sample_count`; per-sample status available; metrics computed over valid samples only.
- **Dependencies:** EVAL-002
- **MVP Status:** In-MVP

---

## Operations (OPS)

### OPS-001: Deterministic Mock Mode
- **Priority:** P0
- **Description:** The system MUST provide a deterministic Mock mode that works without paid API keys or model downloads. Mock providers for embeddings and generation MUST be used by default in CI and local demo.
- **Rationale:** Zero-barrier demo; CI reliability; reproducibility.
- **Verification:** Clean environment: `docker compose up` → API healthy → upload fixture → query → answer with citations → evaluation run → all pass without external network calls.
- **Acceptance:** No external API calls in Mock mode; deterministic outputs for fixed inputs; CI passes with Mock only.
- **Dependencies:** EMB-003, GEN-001
- **MVP Status:** In-MVP

### OPS-002: Docker Compose Local Deployment
- **Priority:** P0
- **Description:** The system MUST run locally using Docker Compose with health checks, persistent volumes, loopback-only binding, and explicit image tags.
- **Rationale:** Reproducible environment; no host dependency pollution.
- **Verification:** Fresh clone → `docker compose up` → all services healthy → API and Web accessible on documented ports → data survives `docker compose down && docker compose up`.
- **Acceptance:** compose.yaml validates; services start in correct order; no admin ports published; `.env.example` documents all required variables.
- **Dependencies:** All service implementations
- **MVP Status:** In-MVP

---

## Security (SEC)

### SEC-001: Secrets and Artifacts Excluded from Git
- **Priority:** P0
- **Description:** Real secrets, `.env` files, uploaded documents, database volumes, Qdrant storage, model artifacts, build outputs, and unreviewed evaluation outputs MUST be excluded from Git.
- **Rationale:** Security hygiene; repository portability.
- **Verification:** `.gitignore` audit; secret scan in CI; `git status` shows only tracked files.
- **Acceptance:** `.gitignore` covers all sensitive patterns; pre-commit or CI secret scan passes; no committed `.env`, `uploads/`, `qdrant_data/`, `postgres_data/`, `*.model`, `node_modules/`, `.next/`, `__pycache__/`, `.pytest_cache/`.
- **Dependencies:** OPS-002
- **MVP Status:** In-MVP

### SEC-002: Untrusted Document Content Handling
- **Priority:** P0
- **Description:** Document content and retrieved chunks MUST be treated as untrusted data. The system MUST NOT execute, evaluate, or treat document instructions as system instructions.
- **Rationale:** Prompt injection defense; data/control separation.
- **Verification:** Security tests: adversarial documents with injection attempts → verify no secret disclosure, no tool execution, no policy bypass; citation validation rejects model-invented IDs.
- **Acceptance:** Prompt template labels evidence as untrusted; generation output schema-validated; citations server-side resolved; no `eval()` or code execution on document content.
- **Dependencies:** GEN-003, CIT-001
- **MVP Status:** In-MVP

---

## UI (UI)

### UI-001: Core User Flows
- **Priority:** P0
- **Description:** The web UI MUST support: document upload with status, document library with pagination, document detail with chunks, chat with citations and evidence drawer, evaluation dataset list/detail/run, experiment comparison, settings.
- **Rationale:** End-to-end demonstration; portfolio evidence.
- **Verification:** Playwright E2E test covering all flows; manual verification checklist.
- **Acceptance:** All screens implemented with loading/error/empty states; citation links resolve to evidence panel; experiment comparison shows metrics and config diff; Mock mode clearly labeled.
- **Dependencies:** All API endpoints
- **MVP Status:** In-MVP

---

## Observability (OBS)

### OBS-001: Stage Latency and Error Logging
- **Priority:** P1
- **Description:** The system SHOULD log stage latency (parsing, chunking, embedding, indexing, retrieval, generation, citation validation) and safe error categories with correlation IDs.
- **Rationale:** Debugging; performance analysis; reliability.
- **Verification:** Integration test: run ingestion/query → inspect logs → verify stage timestamps, correlation ID, no sensitive data.
- **Acceptance:** Structured JSON logs; correlation ID propagated; PII/secrets redacted; stage durations recorded.
- **Dependencies:** All pipeline stages
- **MVP Status:** Deferred (Phase 19)

---

## Performance (PERF)

### PERF-001: Reproducible Benchmark Scripts
- **Priority:** P1
- **Description:** The system SHOULD provide scripts for reproducible latency/throughput benchmarks with documented hardware, software, corpus, configuration, and warm/cold status.
- **Rationale:** Honest performance reporting; regression detection.
- **Verification:** Script execution on reference hardware; output format includes all context.
- **Acceptance:** Benchmark script exists; reports actual measurements; no fabricated numbers.
- **Dependencies:** OPS-002
- **MVP Status:** Deferred (Phase 20)

---

## CI/CD (CI)

### CI-001: Required CI Without Paid Credentials
- **Priority:** P0
- **Description:** Required CI pipeline MUST run using deterministic Mock providers and fixtures. Real API evaluation MUST be optional and separately configured.
- **Rationale:** Zero-cost CI; reproducibility; no secret management in CI.
- **Verification:** GitHub Actions workflow: lint → typecheck → unit → integration → contract → frontend → E2E (if browser) → Docker validate → secret scan; all pass without secrets.
- **Acceptance:** Workflow YAML exists; runs on push/PR; Mock providers used; real provider profile optional and documented.
- **Dependencies:** OPS-001, All test layers
- **MVP Status:** In-MVP