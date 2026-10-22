# RAGBench — Project Understanding

**Version:** 1.0  
**Date:** 2026-10-22  
**Status:** Initialization baseline

---

## 1. Product Mission

RAGBench is a local-first Retrieval-Augmented Generation (RAG) application and evaluation lab. It enables users to:

- Ingest a controlled collection of documents (PDF, TXT, Markdown)
- Ask questions grounded in those documents
- Inspect source citations that resolve to actual stored chunks and source pages
- Construct versioned evaluation datasets with explicit ground truth
- Run reproducible experiments comparing retrieval and generation configurations
- Honestly report limitations and measurement boundaries

The product demonstrates both application engineering (document ingestion, metadata persistence, API design, provider abstractions, UI, containerization, security) and evaluation engineering (fixed datasets, explicit ground truth, independent retrieval and generation metrics, reproducible experiment configurations).

---

## 2. Target Users and Primary Use Cases

| Persona | Primary Use Cases |
|---------|-------------------|
| AI/LLM Engineering Hiring Manager | Review repository for evidence of RAG implementation, evaluation rigor, reliability, security, reproducibility |
| Backend/Platform Engineer | Understand modular pipeline architecture, provider abstractions, data model, CI/CD |
| Applied ML Engineer | Run evaluation datasets, compare chunking/embedding/retrieval/generation configurations |
| Technical Reviewer | Clone, run local demo via Docker Compose, execute tests, understand architecture without paid APIs |

**Primary Demo Flow:**
1. Start application locally with Docker Compose
2. Use deterministic Mock mode (no paid API key or model download required)
3. Upload small sample corpus (synthetic or openly licensed documents)
4. Inspect ingestion status, parsed pages, chunks, index metadata
5. Ask answerable question → receive structured answer with citations resolving to stored chunks
6. Ask unanswerable question → system abstains or states evidence is insufficient
7. Run versioned evaluation dataset
8. Compare at least two configurations using same dataset and corpus/index
9. Export/inspect reproducible metrics report

---

## 3. Functional Requirements (Consolidated from SPEC)

### Document Ingestion
- **DOC-001 (P0):** Accept PDF, TXT, Markdown only in MVP
- **DOC-002 (P0):** Configurable limits for bytes, pages, text size, processing time
- **DOC-003 (P0):** Preserve document ID/version, file metadata, content hash, page metadata
- **DOC-004 (P0):** Explicit ingestion states and safe error reasons
- **DOC-005 (P0):** Prevent path traversal and untrusted filename use

### Chunking
- **CHK-001 (P0):** Configurable chunk size and overlap
- **CHK-002 (P0):** Preserve chunk-to-document/version/source linkage

### Embeddings
- **EMB-001 (P0):** Provider interface for embedding generation
- **EMB-002 (P0):** Validate embedding dimension and model/index compatibility

### Vector Indexing
- **IDX-001 (P0):** Index chunks in Qdrant using stable point IDs
- **IDX-002 (P0):** Re-index cleanly when embedding model or chunking config changes

### Retrieval
- **RET-001 (P0):** Retrieve top-k chunks within explicit corpus/document scope
- **RET-002 (P0):** Keep similarity score distinct from calibrated relevance probability

### Generation
- **GEN-001 (P0):** Generate answer from retrieved context through provider interface
- **GEN-002 (P0):** Handle insufficient evidence explicitly

### Citations
- **CITE-001 (P0):** Validate all cited chunk IDs against actual retrieved/stored chunks
- **CITE-002 (P0):** Show source title, page (when available), and supporting excerpt

### UI
- **UI-001 (P0):** Upload, query, inspect citation, view evaluation from UI

### Evaluation
- **EVAL-001 (P0):** Store versioned evaluation datasets
- **EVAL-002 (P0):** Compute retrieval metrics from explicit relevance ground truth
- **EVAL-003 (P0):** Store all configuration needed to explain experiment results
- **EVAL-004 (P1):** Support optional LLM-judge evaluation behind separate interface

### Experiments
- **EXP-001 (P0):** Compare two configurations against same dataset version
- **EXP-002 (P0):** Preserve failed samples and report their count

### Operations
- **OPS-001 (P0):** Local deterministic Mock mode works without paid API keys
- **OPS-002 (P0):** Docker Compose setup, health checks, persistent volumes work

### Security
- **SEC-001 (P0):** Secrets, real uploads, database/vector volumes excluded from Git
- **SEC-002 (P0):** Untrusted document instructions never treated as trusted system instructions

---

## 4. Non-Functional Requirements (Consolidated from SPEC)

| Control | Initial Default Target | Notes |
|---------|------------------------|-------|
| Max upload size | 20 MiB | Configurable; reject before expensive processing |
| Max PDF pages | 200 | Configurable; reject or fail with clear reason |
| Max extracted text | 1,000,000 characters per document | Configurable |
| Max chunk size | 1,200 characters | Baseline strategy; model/token-aware chunking may be added |
| Chunk overlap | 150 characters | Must be less than chunk size |
| Default retrieval top-k | 5 | Configurable per experiment |
| Max retrieval top-k | 20 | Configurable hard bound for MVP |
| Max answer context | Configurable character/token budget | Must not be unbounded |
| Max generation output | Configurable token budget | Enforced when provider supports it |
| Mock E2E runtime | Target under 10 seconds for tiny fixture corpus | Measured locally |
| Required external credentials | Zero | Mock path must function without them |

### Reliability
- Failed parse MUST NOT appear as successful ingestion
- Indexing complete only when vector index is usable
- Partial results and missing samples MUST be reported, not silently discarded
- Retries MUST be bounded and only applied to suitable transient failures
- Re-ingestion of same document version/config MUST be deterministic or explicitly versioned
- Deleting a document MUST remove/invalidate associated vectors and derived records

### Performance Reporting
Every benchmark report MUST identify: hardware, OS, software versions, corpus size, dataset size, relevant configuration, warm/cold status, actual result. No unqualified latency or quality numbers.

---

## 5. Technology Stack (Proposed Baseline)

| Layer | Technology | Responsibility |
|-------|------------|----------------|
| Web UI | Next.js + TypeScript | Document library, chat, citations, evaluation, comparisons |
| API | FastAPI + Pydantic | Contracts, validation, orchestration, document and experiment APIs |
| Metadata Database | PostgreSQL | Documents, versions, datasets, samples, experiments, results |
| Vector Store | Qdrant | Vector points and retrieval payloads |
| Parsing | Narrowly selected PDF/TXT/Markdown parsers | Safe extraction and source metadata |
| Embeddings | Provider interface | Local, external, deterministic Mock implementations |
| Generation | Provider interface | Local, external, deterministic Mock implementations |
| Evaluation | Deterministic metric modules + optional Ragas adapter | Reproducible metric calculation |
| Background Jobs | In-process initially; Celery + Redis if justified | Ingestion and evaluation tasks |
| Packaging | Docker Compose | Repeatable local execution |
| Quality | pytest, frontend tests, Playwright | Unit, integration, contract, E2E checks |
| CI | GitHub Actions | Repeatable checks with no paid credentials |

---

## 6. System Architecture and Component Responsibilities

### Primary Data Flow
```
Upload → Validation → Parse → Normalize → Chunk → Embed → Index → Retrieve → Build Context → Generate → Validate Citations → Persist Answer
```

### Evaluation Flow
```
Versioned Dataset + Corpus/Index + Pipeline Config → Run Samples → Collect Retrieval and Answer Results → Calculate Metrics → Persist Experiment → Compare Runs
```

### Component Boundaries

| Component | Responsibility | Key Interfaces |
|-----------|----------------|----------------|
| Ingestion | File validation, parsing, text extraction, metadata preservation | Parser interface, Document repository |
| Chunking | Text normalization, chunking strategies, metadata preservation | Chunker interface, Chunk repository |
| Embeddings | Provider abstraction, batch processing, dimension validation | EmbeddingProvider interface |
| Vector Store | Qdrant collection management, upsert, query, deletion | VectorStore interface |
| Retrieval | Dense retrieval, top-k, metadata filtering | RetrievalService |
| Generation | Provider abstraction, prompt construction, output parsing | ChatGenerationProvider interface |
| Citations | Validation against retrieved/stored chunks, source resolution | CitationValidator |
| Evaluation | Dataset management, deterministic metrics, experiment orchestration | EvaluationService, MetricCalculator |
| Experiments | Configuration versioning, run execution, comparison | ExperimentRunner |
| API | FastAPI routes, request/response validation, orchestration | Pydantic schemas |
| Frontend | Next.js UI, state management, API integration | TypeScript interfaces |

---

## 7. Data Model (Consolidated from SPEC)

### Core Entities

- **documents**: Logical document identity, display name, media type, status, content hash, size, timestamps
- **document_versions**: Immutable source version, parser metadata, content hash, storage reference, page count, ingestion status
- **ingestion_jobs**: Attempt, state, start/end timestamps, failure category, safe error detail
- **chunks**: Chunk identity, document version, chunk index, text/reference, page/offset metadata, chunker config hash, text hash
- **index_versions**: Corpus/version, embedding provider/model/version/dimension, vector collection, chunking configuration, status
- **datasets**: Logical dataset identity and current metadata
- **dataset_versions**: Immutable dataset version, schema version, hash, provenance, created timestamp
- **dataset_samples**: Question, answerability label, references, relevant chunks/documents, tags
- **experiments**: Immutable configuration manifest and hash
- **evaluation_runs**: Dataset/index/experiment linkage, status, timing, software version
- **sample_results**: Query-level retrieval/generation output metadata, metrics, status, safe error
- **metric_results**: Metric name/version, value, denominator, evaluator metadata, sample count
- **audit_events**: Relevant state transitions and deletion operations

### Vector Payloads (Qdrant)
Carry only metadata required for retrieval and citation resolution: chunk_id, document_id, document_version_id, page_number, source_title, text_excerpt. Source metadata validated against PostgreSQL before citation rendering.

---

## 8. RAG Pipeline Stages (Detailed)

### Stage 1: Document Upload & Input Validation
- **Purpose:** Accept file, validate format/size, generate safe identifiers
- **Inputs:** HTTP multipart upload (PDF, TXT, Markdown)
- **Outputs:** Document record with generated ID, storage reference, content hash, validation status
- **Validation:** File size ≤ 20 MiB, MIME type in allowed set, file signature matches extension, no path traversal
- **Failure Modes:** Oversized, unsupported format, empty, malformed, encrypted
- **Observability:** Upload latency, validation result, file metadata

### Stage 2: Text Extraction & Metadata Preservation
- **Purpose:** Extract text content and structural metadata
- **Inputs:** Validated file reference
- **Outputs:** Extracted text per page/segment, page count, document metadata
- **Validation:** Page count ≤ 200, extracted text ≤ 1M chars, parser timeout
- **Failure Modes:** Parser crash, timeout, corrupted PDF, unsupported encoding
- **Observability:** Parser duration, page count, character count, warnings

### Stage 3: Text Normalization
- **Purpose:** Normalize line endings, whitespace while preserving meaningful structure
- **Inputs:** Raw extracted text with page/segment boundaries
- **Outputs:** Normalized text with preserved paragraph/page boundaries
- **Validation:** No data loss beyond normalization rules
- **Failure Modes:** Unicode normalization issues, excessive memory

### Stage 4: Configurable Chunking
- **Purpose:** Split text into chunks with overlap, preserve provenance
- **Inputs:** Normalized text, chunking configuration (size, overlap, strategy)
- **Outputs:** Ordered chunks with metadata (chunk_id, document_id, version_id, chunk_index, page_number, offsets, text_hash, chunker_config_hash)
- **Validation:** chunk_size > 0, 0 ≤ overlap < chunk_size, no empty chunks, stable ordering
- **Failure Modes:** Infinite loop, empty chunks, memory exhaustion on huge documents
- **Observability:** Chunk count, chunk size distribution, processing time

### Stage 5: Embedding Generation
- **Purpose:** Generate vector embeddings for chunks via provider interface
- **Inputs:** Chunk texts, embedding provider configuration
- **Outputs:** Vectors with metadata (provider, model, version, dimension)
- **Validation:** Response length matches input, dimensions match expected, finite values
- **Failure Modes:** Provider timeout, rate limit, dimension mismatch, invalid response
- **Observability:** Batch count, embedding latency, token usage (if available)

### Stage 6: Vector Indexing
- **Purpose:** Upsert vectors to Qdrant with stable point IDs and payload metadata
- **Inputs:** Vectors, chunk metadata, index version configuration
- **Outputs:** Indexed points, index version record
- **Validation:** Dimension matches collection, point IDs stable, upsert confirmed
- **Failure Modes:** Qdrant unavailable, dimension mismatch, duplicate point IDs
- **Observability:** Upsert latency, point count, index version

### Stage 7: Query Normalization & Retrieval
- **Purpose:** Retrieve top-k relevant chunks for a query
- **Inputs:** User question, corpus/document scope, retrieval configuration (top-k, filters)
- **Outputs:** Ranked RetrievalResult objects (rank, score, chunk_id, document_id, version_id, page, metadata, text)
- **Validation:** top-k within bounds, dimension compatibility, scope valid
- **Failure Modes:** Empty collection, Qdrant error, dimension mismatch
- **Observability:** Retrieval latency, result count, score distribution

### Stage 8: Context Construction
- **Purpose:** Build bounded context for generation from retrieved chunks
- **Inputs:** RetrievalResults, context budget configuration
- **Outputs:** Context string with embedded chunk metadata, context metadata
- **Validation:** Context size within budget, deduplication applied, metadata preserved
- **Failure Modes:** Context overflow, no retrieved chunks

### Stage 9: Answer Generation
- **Purpose:** Generate grounded answer via provider interface
- **Inputs:** Question, constructed context, generation configuration, prompt template version
- **Outputs:** Raw generation response
- **Validation:** Provider response schema, timeout, output token budget
- **Failure Modes:** Provider timeout, rate limit, malformed response, content policy

### Stage 10: Citation Validation
- **Purpose:** Verify all citations resolve to actual retrieved/stored chunks
- **Inputs:** Generated answer with citations, retrieval results, stored chunk metadata
- **Outputs:** Validated answer with resolved citations, invalid citation flags
- **Validation:** Every cited chunk_id exists in retrieval results and PostgreSQL, page/document metadata matches
- **Failure Modes:** Hallucinated citations, mismatched metadata, provider didn't include citations

### Stage 11: Final Response Assembly
- **Purpose:** Produce final schema-validated answer
- **Inputs:** Validated answer, citations, limitations, provider metadata, timing
- **Outputs:** AnswerResponse (answer_id, question, answer_text, status, citations[], limitations[], provider_metadata, latency_metadata)
- **Status Values:** `answered`, `insufficient_evidence`, `failed`

---

## 9. Evaluation Methodology and Datasets

### Dataset Format (from SPEC §11)
Each sample includes:
- `sample_id`: stable unique identifier
- `question`: query to test
- `corpus_id`: corpus definition
- `relevant_document_ids`: known relevant documents (optional)
- `relevant_chunk_ids`: known relevant chunks for specific versioned index (optional)
- `relevance_grades`: graded relevance for nDCG (optional)
- `reference_answer`: gold/reference answer (optional)
- `expected_citation_ids`: expected source IDs (optional)
- `answerable`: boolean or explicit answerability label
- `tags`: topics/difficulty/failure category
- `provenance`: source/licensing/dataset origin
- `dataset_version`

### Dataset Immutability
Published dataset versions used by experiments MUST be immutable. Changed sample set → new dataset version. Every run records exact dataset hash/version.

---

## 10. Metrics Specification (Consolidated from SPEC §12)

### Deterministic Retrieval Metrics
Let `R_q` = relevant chunks for query `q`, `TopK_q` = ranked retrieved chunks at cutoff `k`.

- **Precision@k:** `|TopK_q ∩ R_q| / k` (divide by k even if fewer results returned; also report result count)
- **Recall@k:** `|TopK_q ∩ R_q| / |R_q|` (undefined/missing if no relevant items; report sample separately)
- **Reciprocal Rank / MRR:** `1 / rank` of first relevant result, or 0 if none; MRR = mean across valid samples
- **nDCG@k:** Graded relevance when available (gain `2^rel - 1`, discount `log2(rank + 1)`); document binary convention if only binary
- **Citation Validity:** Count whether every citation ID resolves to retrieved chunk in appropriate scope; report invalid count and validity rate

### Answer Quality Metrics (Optional, Judge-Based)
- Exact match (where appropriate)
- Token F1 (suitable short-answer datasets)
- Answerability/abstention precision and recall
- Claim-to-evidence support (human-reviewed or labeled evaluator)
- Faithfulness/groundedness (Ragas or equivalent)
- Context precision/recall (when reference information exists)

**Requirement:** LLM-judge scores are estimates with bias. Each result MUST include judge provider/model/version, metric version, prompt version, run timestamp, failure state. Never present as ground truth.

### Performance/Resource Metrics
- Parsing/ingestion duration
- Embedding duration and vector count
- Vector upsert and retrieval latency
- Generation latency
- Total request latency
- Token usage and estimated cost (when provider returns usage)
- Failed/partial sample count
- **Requirement:** Report cold/warm status, hardware/software/configuration context

---

## 11. Security and Privacy Requirements (Consolidated from SPEC §16)

### Local-First Boundary
- Bind development services to loopback by default
- Do not publish PostgreSQL or Qdrant admin interfaces
- Secrets in ignored local env files or secret manager
- `.env.example` with placeholders only
- Do not commit: uploaded documents, embeddings/vector storage, database volumes, model weights, private evaluation data
- Public deployment blocked until: authentication, authorization, TLS, rate limiting, secure secrets, deployment hardening verified

### Upload Security
- Accept only PDF, TXT, Markdown in MVP
- Validate file size and format; never trust extension alone
- Use safe generated storage names
- Limit parser time, pages, text size, temporary storage
- Clean up partial files on error
- No archive acceptance in MVP

### RAG-Specific Threat Model
- Uploaded/retrieved content = untrusted data, not instructions
- No arbitrary filesystem, shell, database, network capabilities for model
- Validate model output with schemas, resolve citations server-side
- No claim that prompt wording alone prevents injection
- Adversarial test documents with instructions to reveal secrets/ignore policies → verify no authorized behavior change

### Logging and Retention
- Never log API keys or authorization headers
- Bound log payloads, redact sensitive fields
- Do not log full document contents by default
- Document deletion semantics for: source file, parsed text, chunks, vectors, derived results, retained audit metadata

---

## 12. Local Development and Deployment Requirements

### Docker Compose (MVP)
- PostgreSQL with persistent volume
- Qdrant with persistent volume
- API service (FastAPI)
- Web service (Next.js)
- Optional: Redis + Celery worker (only if justified by approved architecture)
- All developer-facing ports bound to loopback
- Database/vector store ports NOT published
- Health checks for dependencies
- Explicit image tags (no `latest`)
- Non-destructive start/stop commands

### Mock Mode
- Deterministic embedding provider (fixed vectors for test inputs)
- Deterministic generation provider (fixed answers for test inputs)
- Works without paid credentials or model downloads
- Required for CI and local demo

### Optional Local Models
- Ollama on macOS (native, not in Docker) as optional endpoint
- Application containers may call configured local Ollama endpoint
- Keep optional; not required for MVP demo

---

## 13. Testing and Acceptance Criteria (Consolidated from SPEC §17-18)

### Test Layers
- **Unit:** Chunking boundaries, metadata preservation, vector dimension validation, metric formulas, configuration hashing, citation validation, abstention logic, dataset validation
- **Integration:** Parser→chunks, chunks→embeddings, Qdrant upsert/query/delete, database migrations, ingestion status, document deletion, query processing, evaluation persistence
- **E2E (Playwright):** Upload fixture → wait for indexing → ask answerable question → inspect citation → ask unanswerable question → execute small evaluation → inspect comparison report
- **Security Regression:** Oversized input, malformed PDF, path traversal filenames, empty documents, prompt injection, invalid citation IDs, model output HTML, missing secrets, cross-scope access, accidental secret logging
- **Evaluation:** Perfect retrieval, no relevant results, partial retrieval, duplicate results, ties, empty references, missing sample results, metric denominator handling

### CI Rules
- Required CI uses deterministic fixtures and Mock providers
- Real API evaluation optional, separate workflow
- Test failures remain visible; never weaken assertions for green build
- Dependency audit and secret scanning

### Acceptance Gates (P0 Requirements)

| Gate | Criteria |
|------|----------|
| **A — Setup** | Docker Compose startup succeeds from clean state; services healthy; basic path works without paid APIs; ports/persistence match docs |
| **B — Ingestion** | PDF/TXT/Markdown fixtures accepted; unsupported/invalid/oversized fail safely; source/page metadata survives; chunk IDs and index config traceable |
| **C — RAG Answer** | Query constrained to chosen scope; citations resolve to actual chunks; invalid citations rejected/flagged; unanswerable → clear insufficient-evidence; prompt injection in retrieved text grants no capabilities |
| **D — Evaluation** | Dataset versions and ground truth stored; deterministic retrieval metrics work on test fixtures; sample failures visible; two configurations comparable on same dataset; LLM-judge metrics labeled optional |
| **E — Quality** | Python/frontend tests and CI pass; Docker/dependency config validates; secret scan clean; README setup/benchmarks verified; independent audit finds no Critical blockers |

---

## 14. Implementation Phases and Dependencies

From RAGBench_Antigravity_Roadmap.md (25 phases):

| Phase | Focus | Dependencies |
|-------|-------|--------------|
| 1 | Product Vision & MVP Boundaries | — |
| 2 | PRD, Requirements, Acceptance Criteria | Phase 1 |
| 3 | Architecture, Data Flow, ADRs | Phase 2 |
| 4 | Repository Scaffold & Markdown Map | Phase 3 |
| 5 | Dependency Compatibility & Developer Tooling | Phase 4 |
| 6 | Local Infrastructure (Docker Compose) | Phase 5 |
| 7 | PostgreSQL Models & Migrations | Phase 6 |
| 8 | Provider Interfaces & Mock Mode | Phase 7 |
| 9 | Secure Document Upload & Parsing | Phase 8 |
| 10 | Chunking & Embedding Pipeline | Phase 9 |
| 11 | Qdrant Indexing & Retrieval Baseline | Phase 10 |
| 12 | RAG Orchestration, Prompt, Citation Validation | Phase 11 |
| 13 | Frontend Design System & IA | Phase 6 (parallel) |
| 14 | Frontend/API Integration | Phases 12, 13 |
| 15 | Versioned Evaluation Dataset & Deterministic Metrics | Phase 12 |
| 16 | Answer Evaluation & Ragas Integration | Phase 15 |
| 17 | Experiment Runner & Configuration Comparison | Phase 16 |
| 18 | Security & Privacy Hardening | Phase 12+ |
| 19 | Reliability, Observability, Recovery | Phase 12+ |
| 20 | Performance & Benchmarking | Phase 19 |
| 21 | E2E Testing & CI | Phase 14+ |
| 22 | Final Docker Experience & Dev Commands | Phase 21 |
| 23 | README, Demo, Licensing, Portfolio | Phase 22 |
| 24 | Independent Final Engineering Audit | Phase 23 |
| 25 | Root-Cause Analysis & Safe Repair | As needed |

**Critical Path:** Phases 1→2→3→4→5→6→7→8→9→10→11→12→14→15→17→21→22→23→24
**Parallel Tracks:** Frontend (13, 14) can proceed after API contracts stable (12)

---

## 15. Key Unresolved Decisions (Requiring ADRs)

1. **Background Jobs:** Celery + Redis vs. in-process for MVP ingestion/evaluation (ADR-005)
2. **License:** Final license selection for original code (documented in README)
3. **Vector ID Strategy:** UUIDv5 vs. Qdrant-native ID format for point IDs
4. **Conversation History:** Whether conversation/message persistence is in MVP scope
5. **Hybrid Search/Reranking:** Explicitly deferred post-MVP; baseline is dense-only
6. **Ragas Version Compatibility:** Must verify current API before Phase 16 implementation
7. **Frontend State Management:** TanStack Query vs. SWR vs. custom (decide in Phase 13)
8. **OpenTelemetry:** Whether to include in MVP or defer (ADR in Phase 19)

---

## 16. Conflicts and Resolutions

| Conflict | Resolution |
|----------|------------|
| SPEC §5 repository structure shows `services/backend/` but roadmap Phase 4 shows `services/api/` | Use `services/backend/` as primary (more descriptive); `services/api/` was an earlier name |
| SPEC §5 shows `infra/qdrant/` but Phase 4 shows `infra/qdrant/` not listed | Include `infra/qdrant/` for Qdrant-specific configuration |
| Roadmap mentions `services/backend/app/workers/` but SPEC doesn't | Include `workers/` for potential Celery workers; only implement if ADR-005 justifies |
| SPEC mentions "conversation history" in data model but roadmap doesn't explicitly | Keep in data model as optional MVP scope; implement only if chat history required |

---

## 17. Validation Checklist for Initialization

- [x] Project specifications read and understood
- [x] Existing user files preserved (4 SPEC files in workspace root)
- [ ] Repository structure created (in progress)
- [ ] Foundational documentation created (in progress)
- [ ] RAG pipeline documented
- [ ] Evaluation methodology documented
- [ ] Technology decisions recorded
- [ ] No application functionality falsely represented as complete
- [ ] Unresolved decisions identified