# RAGBench — Product and Technical Specification

**Document version:** 1.0  
**Status:** Implementation baseline for an engineering portfolio MVP  
**Repository:** `ragbench`  
**Audience:** Antigravity coding agent, developer, technical reviewer, and hiring manager  
**Normative language:** MUST / MUST NOT indicate required behavior; SHOULD indicates a strong recommendation; MAY indicates an optional capability.

---

## 1. Product Summary

RAGBench is a local-first Retrieval-Augmented Generation (RAG) application and evaluation lab. It lets a user ingest a controlled collection of documents, ask questions grounded in those documents, inspect source citations, construct versioned evaluation datasets, run reproducible experiments, and compare retrieval and answer-generation configurations.

The product must demonstrate both sides of LLM engineering:

1. **Application engineering:** document ingestion, metadata persistence, API design, provider abstractions, useful UI, error handling, containerization, and security boundaries.
2. **Evaluation engineering:** fixed datasets, explicit ground truth, independent retrieval and generation metrics, reproducible experiment configurations, and honest reporting of limitations.

RAGBench is not simply a chat UI around a vector database. Its distinctive feature is that the quality and behavior of the RAG pipeline can be examined, measured, and compared.

### 1.1 Primary demo

1. Start the application locally with Docker Compose.
2. Use the clearly labeled deterministic Mock mode; no paid API key or model download is required.
3. Upload a small sample corpus consisting of synthetic or openly licensed documents.
4. Inspect ingestion status, parsed pages, chunks, and index metadata.
5. Ask a question that is answerable from the corpus.
6. Receive a structured answer with citations that resolve to actual stored chunks and source pages when available.
7. Ask a question that the corpus cannot answer and verify that the system abstains or states that evidence is insufficient.
8. Run a versioned evaluation dataset.
9. Compare at least two configurations using the same dataset and corpus/index definition.
10. Export or inspect a reproducible metrics report.

### 1.2 Target audience

- AI Engineer / LLM Engineer hiring managers
- Backend and platform engineers
- Applied ML engineers
- Technical reviewers interested in RAG reliability and evaluation

### 1.3 Core value proposition

RAGBench shows how to build a grounded document assistant and how to measure whether changes to chunking, embeddings, retrieval, prompts, or generation actually improve outcomes.

---

## 2. Goals and Non-Goals

### 2.1 MVP goals

- Support PDF, TXT, and Markdown ingestion.
- Preserve document identity, version, page metadata where available, and chunk provenance.
- Make chunking, embedding, retrieval, and generation configuration explicit and versioned.
- Provide a usable document library and chat experience.
- Return schema-validated answers with source-linked citations.
- Detect invalid citations and explicitly handle insufficient evidence.
- Store versioned evaluation datasets and fixed samples.
- Calculate deterministic retrieval metrics when ground truth exists.
- Optionally run model-based answer-quality evaluation behind a separate interface.
- Run experiments and compare configurations on consistent evaluation cases.
- Provide a deterministic Mock path for required local demo and CI.
- Offer optional local-model and external API adapters.
- Run locally using Docker Compose.
- Provide tests, CI, security controls, reproducible setup, and professional English documentation.

### 2.2 Non-goals for the MVP

- Public multi-tenant SaaS deployment.
- Unrestricted public URL crawling.
- Executing instructions or code found in uploaded documents.
- Guaranteeing that all generated answers are factually correct.
- Guaranteeing complete protection against prompt injection.
- Fine-tuning or training foundation models.
- Large-scale distributed indexing across multiple machines.
- Mandatory paid model, embedding, or evaluator APIs.
- Multimodal image/audio/video RAG.
- Complex agentic research workflows.
- Arbitrary document archive ingestion.
- Automatic publication or external actions based on generated answers.

These can be considered only after the MVP acceptance gates pass.

---

## 3. Personas and Main User Stories

### 3.1 Local user / researcher

- As a user, I can upload a supported document and see whether ingestion succeeded.
- As a user, I can inspect document metadata and extracted chunks.
- As a user, I can ask a question over a selected corpus.
- As a user, I can click a citation and inspect the supporting passage and source page.
- As a user, I can see when the corpus lacks sufficient evidence.
- As a user, I can delete a document and understand what related data is removed.

### 3.2 Evaluator

- As an evaluator, I can create and version a dataset of questions and relevant evidence.
- As an evaluator, I can run that dataset against a chosen corpus/index and pipeline configuration.
- As an evaluator, I can distinguish deterministic retrieval metrics from LLM-judge estimates.
- As an evaluator, I can compare runs and inspect which samples improved, regressed, failed, or were skipped.
- As an evaluator, I can reproduce a previous experiment from its stored configuration and dataset version, subject to provider/model availability.

### 3.3 Technical reviewer

- As a reviewer, I can clone the repository, follow the local setup, execute the Mock demo, run tests, and understand architecture and limitations without needing secret credentials.

---

## 4. Technology and Architecture Baseline

The final implementation must follow the approved architecture and record material changes as Architecture Decision Records (ADRs).

### 4.1 Proposed stack

| Layer | Preferred technology | Responsibility |
|---|---|---|
| Web UI | Next.js + TypeScript | Document library, chat, citations, evaluation, comparisons |
| API | FastAPI + Pydantic | Contracts, validation, orchestration, document and experiment APIs |
| Metadata database | PostgreSQL | Documents, versions, datasets, samples, experiments, results |
| Vector store | Qdrant | Vector points and retrieval payloads |
| Parsing | Narrowly selected PDF/TXT/Markdown parsers | Safe extraction and source metadata |
| Embeddings | Provider interface | Local, external, deterministic Mock implementations |
| Generation | Provider interface | Local, external, deterministic Mock implementations |
| Evaluation | Deterministic metric modules + optional Ragas adapter | Reproducible metric calculation |
| Background jobs | In-process initially or Celery + Redis if long-running workload justifies it | Ingestion and evaluation tasks |
| Packaging | Docker Compose | Repeatable local execution |
| Quality | pytest, frontend tests, Playwright | Unit, integration, contract, E2E checks |
| CI | GitHub Actions | Repeatable checks with no paid credentials |

### 4.2 Architecture rule

Business logic for parsing, chunking, embedding, indexing, retrieval, context building, citation validation, metric calculation, and experiment identity MUST remain visible in ordinary Python modules with explicit inputs and outputs. A framework MAY be used when it provides measurable value, but it MUST NOT make core evaluation behavior opaque.

### 4.3 Primary data flow

`Upload -> Validation -> Parse -> Normalize -> Chunk -> Embed -> Index -> Retrieve -> Build Context -> Generate -> Validate Citations -> Persist Answer`

Evaluation flow:

`Versioned Dataset + Corpus/Index + Pipeline Config -> Run Samples -> Collect Retrieval and Answer Results -> Calculate Metrics -> Persist Experiment -> Compare Runs`

### 4.4 Local-only security boundary

The MVP MUST bind web/API development ports to loopback by default. PostgreSQL and Qdrant admin ports MUST NOT be publicly exposed. Public or remote deployment MUST be considered blocked until authentication, authorization, TLS, rate limiting, secure secrets, and deployment hardening are implemented and verified.

---

## 5. Repository Structure Contract

The following is the intended structure. It may be refined only through a documented decision, not through uncontrolled file proliferation.

```text
ragbench/
├── apps/
│   └── web/
│       ├── app/
│       ├── components/
│       │   └── ui/
│       ├── features/
│       │   ├── documents/
│       │   ├── chat/
│       │   ├── evaluations/
│       │   └── experiments/
│       ├── hooks/
│       ├── lib/
│       ├── public/
│       └── tests/
│           └── e2e/
├── services/
│   └── backend/
│       ├── app/
│       │   ├── api/v1/routes/
│       │   ├── core/
│       │   ├── config/
│       │   ├── db/
│       │   ├── models/
│       │   ├── schemas/
│       │   ├── repositories/
│       │   ├── services/
│       │   ├── ingestion/
│       │   ├── chunking/
│       │   ├── embeddings/
│       │   ├── vectorstore/
│       │   ├── retrieval/
│       │   ├── generation/
│       │   ├── citations/
│       │   ├── evaluation/
│       │   ├── providers/
│       │   └── observability/
│       ├── migrations/
│       └── tests/
│           ├── unit/
│           ├── integration/
│           └── contract/
├── evals/
│   ├── datasets/
│   ├── cases/
│   ├── baselines/
│   └── reports/
├── data/
│   ├── samples/
│   ├── expected/
│   └── README.md
├── infra/
│   ├── docker/
│   ├── postgres/
│   └── monitoring/
├── scripts/
├── docs/
│   ├── adr/
│   ├── audits/
│   ├── diagrams/
│   └── runbooks/
├── .github/workflows/
├── compose.yaml
├── Makefile
├── .env.example
├── .gitignore
├── .dockerignore
├── .editorconfig
└── README.md
```

Do not create empty modules just to satisfy the tree. Create modules as their phase is implemented. Do not commit `.env`, uploads, Qdrant storage, PostgreSQL volume files, model artifacts, caches, build output, or unreviewed evaluation outputs.

---

## 6. Functional Requirements

Requirement priorities: P0 = release blocker for MVP; P1 = expected in MVP when feasible; P2 = later enhancement.

| ID | Priority | Requirement | Verification |
|---|---|---|---|
| DOC-001 | P0 | Accept PDF, TXT, and Markdown only in MVP | API and parser tests |
| DOC-002 | P0 | Enforce configurable limits for bytes, pages, text size, and processing time | Boundary tests |
| DOC-003 | P0 | Preserve document ID/version, file metadata, content hash, and page metadata when available | Persistence tests |
| DOC-004 | P0 | Expose explicit ingestion states and safe error reasons | API integration tests |
| DOC-005 | P0 | Prevent path traversal and untrusted filename use | Security tests |
| CHK-001 | P0 | Support configurable chunk size and overlap | Unit tests |
| CHK-002 | P0 | Preserve chunk-to-document/version/source linkage | Data-integrity tests |
| EMB-001 | P0 | Use provider interface for embedding generation | Contract tests |
| EMB-002 | P0 | Validate embedding dimension and model/index compatibility | Contract/integration tests |
| IDX-001 | P0 | Index chunks in Qdrant using stable point IDs | Integration tests |
| IDX-002 | P0 | Re-index cleanly when embedding model or chunking config changes | Reindex tests |
| RET-001 | P0 | Retrieve top-k chunks within an explicit corpus/document scope | Retrieval tests |
| RET-002 | P0 | Keep similarity score distinct from calibrated relevance probability | Schema/documentation review |
| GEN-001 | P0 | Generate answer from retrieved context through a provider interface | Provider contract tests |
| CITE-001 | P0 | Validate all cited chunk IDs against actual retrieved/stored chunks | Citation tests |
| CITE-002 | P0 | Show source title, page where available, and supporting excerpt | E2E test |
| GEN-002 | P0 | Handle insufficient evidence explicitly | Abstention tests |
| UI-001 | P0 | Upload, query, inspect citation, and view evaluation from the UI | Playwright |
| EVAL-001 | P0 | Store versioned evaluation datasets | Schema/persistence tests |
| EVAL-002 | P0 | Compute retrieval metrics from explicit relevance ground truth | Metric unit tests |
| EVAL-003 | P0 | Store all configuration needed to explain experiment results | Serialization tests |
| EVAL-004 | P1 | Support optional LLM-judge evaluation behind a separate interface | Contract tests |
| EXP-001 | P0 | Compare two configurations against the same dataset version | Integration tests |
| EXP-002 | P0 | Preserve failed samples and report their count | Evaluation tests |
| OPS-001 | P0 | Local deterministic Mock mode works without paid API keys | Clean setup E2E |
| OPS-002 | P0 | Docker Compose setup, health checks, and persistent volumes work | Docker smoke test |
| SEC-001 | P0 | Secrets, real uploads, and database/vector volumes are excluded from Git | Secret scan and review |
| SEC-002 | P0 | Untrusted document instructions are never treated as trusted system instructions | Adversarial tests + review |
| OBS-001 | P1 | Log stage latency and safe error category with correlation IDs | Integration tests |
| PERF-001 | P1 | Provide reproducible latency/throughput benchmark scripts | Benchmark smoke test |
| CI-001 | P0 | Required CI runs without paid keys and uses deterministic fixtures | CI run |

---

## 7. Non-Functional Requirements and Initial Limits

The initial values below are conservative configuration defaults for the MVP, not universal product guarantees. Antigravity MUST confirm and document values actually implemented.

| Control | Initial default target | Notes |
|---|---:|---|
| Max upload size | 20 MiB | Configurable; reject before expensive processing |
| Max PDF pages | 200 | Configurable; reject or fail with clear reason |
| Max extracted text | 1,000,000 characters per document | Configurable |
| Max chunk size | 1,200 characters | Baseline strategy; model/token-aware chunking may be added |
| Chunk overlap | 150 characters | Must be less than chunk size |
| Default retrieval top-k | 5 | Configurable per experiment |
| Max retrieval top-k | 20 | Configurable hard bound for MVP |
| Max answer context | Configurable character/token budget | Must not be unbounded |
| Max generation output | Configurable token budget | Enforced when provider supports it; otherwise bounded by adapter/application |
| Mock E2E runtime | Target under 10 seconds for tiny fixture corpus | Measured locally; not a general performance promise |
| API upload acceptance | Target p95 under 1 second before full ingestion, on local dev hardware | Only if upload is asynchronous; measure rather than assume |
| Required external credentials | Zero | Mock path must function without them |

### 7.1 Performance reporting

Every benchmark report MUST identify hardware, OS, software versions, corpus size, dataset size, relevant configuration, warm/cold status, and actual result. Do not publish an unqualified latency or quality number.

### 7.2 Reliability

- A failed parse MUST NOT appear as successful ingestion.
- Indexing is complete only when the configured vector index is usable.
- Partial results and missing samples MUST be reported, not silently discarded.
- Retries MUST be bounded and only applied to suitable transient failures.
- Re-ingestion of the same document version/configuration MUST be deterministic or explicitly versioned.
- Deleting a document MUST also remove or invalidate associated vectors and derived records according to the documented retention policy.

---

## 8. Document Ingestion Specification

### 8.1 Accepted input

MVP accepts only PDF, TXT, and Markdown. The system MUST NOT accept archives, executables, arbitrary binary content, or remote URLs by default.

### 8.2 Ingestion states

Recommended states:

`uploaded -> validating -> parsing -> chunking -> embedding -> indexing -> ready`

Terminal/error states:

`rejected`, `failed`, `cancelled`, and optionally `ready_with_warnings`.

Transitions must be explicit; a failed stage must not be marked successful because a database row exists.

### 8.3 Pipeline

1. Validate size and format hints.
2. Store source safely under a generated identifier (or process via safe temporary storage).
3. Calculate content hash.
4. Parse text and metadata. PDF page number should be retained when available.
5. Normalize text while preserving meaningful line and paragraph boundaries.
6. Calculate chunks using versioned chunking configuration.
7. Generate embeddings in bounded batches.
8. Validate vector dimension and finite numeric values.
9. Upsert vectors to the correct versioned Qdrant collection/index.
10. Verify indexing outcome and persist final status.

### 8.4 Re-indexing rules

An index identity must include or reference corpus/document version, chunking configuration/version, embedding provider/model/version, embedding dimension, and relevant vector-store settings. Changing embedding model or chunking must create a new compatible index version or perform a safe rebuild. Do not mix incompatible embeddings silently.

### 8.5 File security

- Do not use the original filename as a filesystem path.
- Enforce parser time and resource limits.
- Reject malformed, empty, encrypted/unsupported, or oversized documents clearly.
- Clean up temporary files on success and failure.
- Do not render extracted HTML as trusted code.
- Treat file content as untrusted text, including prompt-injection instructions.
- No SSRF scope exists while remote URL import is disabled. If URL import is added later, it requires a separate threat review and SSRF defense before implementation.

---

## 9. Chunking and Embedding Specification

### 9.1 Baseline chunker

Implement a deterministic character-based chunker first. Suggested initial configuration: `chunk_size_chars=1200`, `overlap_chars=150`. These are tunable defaults, not claims of optimality.

Requirements:
- `chunk_size_chars > 0`
- `0 <= overlap_chars < chunk_size_chars`
- No empty chunks
- No infinite loops
- Stable chunk order
- Source page/section metadata retained when possible
- Tests for Unicode, RTL text, short text, huge text, empty page, and overlap behavior

A second paragraph-aware or structure-aware chunker can be added as an experiment after the baseline is working.

### 9.2 Chunk metadata

Every chunk must have a stable identity and record:
- `chunk_id`
- `document_id`
- `document_version_id`
- `corpus_id` or equivalent scope identifier
- `chunk_index`
- `text_hash`
- `page_number` when available
- source offsets or section metadata when available
- chunking strategy and configuration hash
- embedding provider/model/version and dimension
- index version

For Qdrant point IDs use a format supported by the pinned client/server; stable UUIDv5 derived from namespace and canonical chunk identity is a suitable option. Do not assume arbitrary strings are valid point IDs.

### 9.3 Embedding interface

The provider interface must receive a list of texts and return vectors associated with the input order, with metadata including provider/model/version/dimension. Validate response length, vector dimensions, finite values, errors, and batch limits.

Mock embeddings are for interface and deterministic retrieval tests only. They must not be described as semantic embeddings or used to claim real retrieval quality.

---

## 10. Retrieval and Answer Specification

### 10.1 Retrieval baseline

Start with dense vector retrieval and configurable top-k. Do not add hybrid retrieval or reranking before the baseline can be evaluated and compared. Retrieval score/distance is a ranking signal; it MUST NOT be presented as a calibrated probability of correctness or relevance.

### 10.2 Context construction

- Retrieve from an explicit document/corpus scope.
- Deduplicate chunks when appropriate.
- Enforce context size limits.
- Preserve chunk ID, document ID/version, page, and source title in context metadata.
- Do not pass arbitrary metadata fields as instructions.
- Treat retrieved content as untrusted evidence.

### 10.3 Answer contract

A normalized answer should contain:
- `answer_id`
- `question`
- `answer_text`
- `status`: `answered`, `insufficient_evidence`, or `failed`
- `citations[]`
- `limitations[]`
- provider/model and prompt version metadata
- latency/usage metadata if available

Each citation should contain only valid server-resolved values, such as `chunk_id`, `document_id`, `document_version_id`, `page_number` when available, source title, and a short excerpt. The model must not be trusted to invent these identifiers. The backend validates citations against the actual retrieved set and stored metadata before returning the answer.

### 10.4 Abstention

If retrieval returns no usable evidence, or the evidence does not support a reliable response, the system must state that the selected documents do not provide sufficient evidence. It must not fabricate a source or fill missing facts from hidden model knowledge while presenting them as document-grounded.

### 10.5 Prompt injection

Prompts should clearly label retrieved text as untrusted reference material. This is defense-in-depth, not a complete defense. Tests must include hostile instructions embedded in documents and verify that no tool execution, secret disclosure, or policy override results from those instructions.

---

## 11. Evaluation Dataset Specification

### 11.1 Dataset fields

Each sample should include:

- `sample_id`: stable unique identifier
- `question`: query to test
- `corpus_id` or corpus definition
- `relevant_document_ids`: optional set of known relevant documents
- `relevant_chunk_ids`: optional set of known relevant chunks for a specific, versioned index
- `relevance_grades`: optional graded relevance for nDCG
- `reference_answer`: optional gold/reference answer
- `expected_citation_ids`: optional expected source IDs
- `answerable`: boolean or explicit answerability label
- `tags`: topics/difficulty/failure category
- `provenance`: source/licensing or dataset origin
- `dataset_version`

Do not place private or unlicensed full documents inside the public repository. Samples may refer to the repository's small synthetic/openly licensed fixture corpus.

### 11.2 Example JSONL sample

```json
{
  "sample_id": "sample-001",
  "question": "What is the stated retention period?",
  "corpus_id": "demo-corpus-v1",
  "relevant_document_ids": ["doc-policy-001"],
  "relevant_chunk_ids": ["chunk-policy-001-003"],
  "relevance_grades": {"chunk-policy-001-003": 3},
  "reference_answer": "The stated retention period is 30 days.",
  "expected_citation_ids": ["chunk-policy-001-003"],
  "answerable": true,
  "tags": ["policy", "direct-fact"],
  "provenance": "Synthetic fixture document created for RAGBench tests.",
  "dataset_version": "1.0.0"
}
```

This is an illustrative fixture only. If identifiers refer to index-specific chunks, the dataset and index version must be compatible or mapping rules must be explicitly documented.

### 11.3 Dataset immutability

Published dataset versions used by experiments must be immutable. Creating a changed sample set creates a new dataset version. Every run records the exact dataset hash/version.

---

## 12. Metrics Specification

Retrieval metrics and answer-quality metrics must remain separate. Metric names must indicate the measured component.

### 12.1 Deterministic retrieval metrics

Let `R_q` be the set of relevant chunks for query `q`, and `TopK_q` be the ranked retrieved chunks at cutoff `k`.

**Precision@k**

`|TopK_q ∩ R_q| / k`

If fewer than `k` results are returned, use the configured convention consistently. Recommended convention: divide by `k` to measure precision at the requested cutoff, and also report result count.

**Recall@k**

`|TopK_q ∩ R_q| / |R_q|`

If no relevant items are defined for a sample, return an undefined/missing value for this metric and report the sample separately; do not divide by zero or silently count it as perfect.

**Reciprocal Rank / MRR**

The reciprocal rank for a sample is `1 / rank` of the first relevant result, or zero if none appears in the evaluated result list. MRR is the mean across the declared valid sample set; skipped/invalid samples must be reported.

**nDCG@k**

Use graded relevance labels when available. Document the gain function and discount. A commonly used gain is `2^rel - 1` and discount `log2(rank + 1)`. If only binary relevance is available, document the chosen binary convention.

**Citation validity**

Count whether every citation ID returned by the model resolves to a chunk that was actually retrieved and belongs to the appropriate corpus/document scope. Report both invalid citation count and validity rate; a valid ID does not prove semantic support.

### 12.2 Answer quality

Where reference answers or reviewed evidence exist, optionally measure:
- Exact match only for questions where it is appropriate
- Token F1 for suitable short-answer datasets
- Answerability/abstention precision and recall
- Claim-to-evidence support through human-reviewed labels or an explicitly labeled evaluator
- Faithfulness / groundedness estimates using a compatible Ragas evaluator or equivalent
- Context precision/recall estimates when required reference information exists

LLM-judge scores are estimates and can be biased. Each result must include judge provider/model/version, metric version, prompt version, run timestamp, and failure state. Never present judge output as ground truth.

### 12.3 Performance and resource metrics

Record where available:
- Parsing and ingestion duration
- Embedding duration and number of vectors
- Vector upsert and retrieval latency
- Generation latency
- Total request latency
- Token usage and estimated cost when provider returns usage and pricing is configured
- Failed/partial sample count

Every report must say whether it measures cold or warm runs and include hardware/software/configuration context.

---

## 13. Experiment Specification

An experiment configuration must be immutable once a run begins. It should include:

- Dataset ID, version, and hash
- Corpus and document versions
- Parser version
- Chunker name/version/configuration
- Embedding provider/model/version/dimension
- Index/collection version
- Retrieval strategy and settings
- Top-k
- Optional metadata filters
- Optional reranker and configuration
- Generation provider/model/version
- Prompt template version/hash
- Answer context/output limits
- Evaluator type/provider/model/version
- Metric names and versions
- Software version/commit ID when available
- Run timestamp and environment details

### 13.1 Comparison rules

- Compare configurations against the same dataset version and compatible corpus/index definitions.
- If the index differs because embeddings or chunking changed, record the change explicitly and explain comparability limitations.
- Never compare a Mock provider score to real model quality as if they were equivalent.
- Never turn missing metrics into zero without an explicit rule.
- Failed samples remain visible and count toward failure reporting.
- Preserve previous experiment results when a configuration changes.

### 13.2 Experiment outputs

Each experiment should generate:
- Machine-readable result JSON
- Aggregate metrics
- Per-sample metrics and status
- Failure list
- Configuration manifest
- Summary Markdown or UI report
- Relevant latency/resource summaries

---

## 14. Suggested API Contract

Routes may be adjusted if an ADR documents a good reason. Do not invent routes in the frontend that are not implemented by FastAPI.

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health/live` | Liveness check |
| `GET` | `/health/ready` | Dependency readiness |
| `POST` | `/api/v1/documents` | Upload a supported document |
| `GET` | `/api/v1/documents` | List/search documents with pagination |
| `GET` | `/api/v1/documents/{document_id}` | Document metadata/status |
| `GET` | `/api/v1/documents/{document_id}/chunks` | List chunk metadata safely |
| `POST` | `/api/v1/documents/{document_id}/reindex` | Re-index with validated configuration |
| `DELETE` | `/api/v1/documents/{document_id}` | Delete document and associated vectors |
| `POST` | `/api/v1/query` | Ask a question against explicit corpus/document scope |
| `GET` | `/api/v1/datasets` | List evaluation datasets |
| `POST` | `/api/v1/datasets` | Create a dataset version |
| `GET` | `/api/v1/datasets/{dataset_id}` | Retrieve dataset metadata/samples |
| `POST` | `/api/v1/evaluations` | Start an evaluation run |
| `GET` | `/api/v1/evaluations/{evaluation_id}` | Get evaluation status/summary |
| `GET` | `/api/v1/evaluations/{evaluation_id}/samples` | Get paginated per-sample results |
| `GET` | `/api/v1/experiments` | List experiments |
| `GET` | `/api/v1/experiments/{experiment_id}` | Get configuration and results |
| `POST` | `/api/v1/experiments/compare` | Compare compatible experiment runs |

For long-running ingestion/evaluation, use asynchronous job semantics where needed. Return HTTP 202 for accepted work and persist an explicit job/run status. Errors should use a consistent schema with stable error codes and safe user-facing messages.

---

## 15. Core Data Model

The final schema should follow the approved ADRs. Suggested entities:

- `documents`: logical document identity, display name, media type, status, content hash, size, created/updated timestamps.
- `document_versions`: immutable source version, parser metadata, content hash, storage reference, page count, ingestion status.
- `ingestion_jobs`: attempt, state, start/end timestamps, failure category, safe error detail.
- `chunks`: chunk identity, document version, chunk index, text or approved reference to text, page/offset metadata, chunker config hash, text hash.
- `index_versions`: corpus/version, embedding provider/model/version/dimension, vector collection, chunking configuration, status.
- `datasets`: logical dataset identity and current metadata.
- `dataset_versions`: immutable dataset version, schema version, hash, provenance, created timestamp.
- `dataset_samples`: question, answerability label, references, relevant chunks/documents, tags.
- `experiments`: immutable configuration manifest and hash.
- `evaluation_runs`: dataset/index/experiment linkage, status, timing, software version.
- `sample_results`: query-level retrieval/generation output metadata, metrics, status, safe error.
- `metric_results`: metric name/version, value, denominator, evaluator metadata, sample count.
- `audit_events`: relevant state transitions and deletion operations if required by the threat model.

Vector payloads in Qdrant should carry only metadata required for retrieval and citation resolution, not arbitrary secret or unrelated application state. Source metadata must be checked against PostgreSQL before trust-sensitive citation rendering.

---

## 16. Security and Privacy Requirements

### 16.1 Local-first boundary

- Bind development-facing services to loopback by default.
- Do not publish PostgreSQL or Qdrant admin interfaces.
- Keep secrets in ignored local environment files or a suitable secret manager.
- Use `.env.example` with placeholders only.
- Do not commit uploaded documents, actual embeddings/vector storage, database volumes, model weights, or private evaluation data.
- Public deployment is blocked until authentication, authorization, TLS, rate limiting, and deployment-specific hardening have been implemented and tested.

### 16.2 Upload security

- Accept only PDF, TXT, Markdown in MVP.
- Validate file size and format; never trust extension alone.
- Use safe generated storage names.
- Limit parser time, pages, text size, and temporary storage.
- Clean up partial files on error.
- Do not accept archives in the MVP.

### 16.3 RAG-specific threat model

- Uploaded/retrieved content is untrusted data, not instructions.
- Do not give the model arbitrary filesystem, shell, database, or network capabilities.
- Validate model output with schemas and resolve citations server-side.
- Do not claim that prompt wording alone prevents injection.
- Add adversarial test documents containing instructions to reveal secrets or ignore policies; verify they do not change the system's authorized behavior.

### 16.4 Logging and retention

- Never log API keys or authorization headers.
- Bound log payloads and redact sensitive fields.
- Do not log full document contents by default.
- Document deletion semantics for source file, parsed text, chunks, vectors, derived results, and retained audit metadata.

---

## 17. Testing Strategy

### 17.1 Unit tests

Test chunking boundaries, metadata preservation, vector dimension validation, metric formulas, configuration hashing, citation validation, abstention logic, and dataset validation.

### 17.2 Integration tests

Test parser to chunks, chunks to embeddings, Qdrant upsert/query/delete, database migrations, ingestion status, document deletion, query processing, and evaluation persistence.

### 17.3 End-to-end tests

A browser E2E test must upload a fixture document, wait for indexing, ask an answerable question, inspect the citation, ask an unanswerable question, execute a small evaluation, and inspect a comparison report.

### 17.4 Security regression tests

Test oversized input, malformed PDF, path traversal-like filenames, empty documents, prompt injection, invalid citation IDs, model output containing HTML, missing secrets, cross-scope access if scope boundaries are implemented, and accidental secret logging.

### 17.5 Evaluation tests

Include known ranking cases for perfect retrieval, no relevant results, partial retrieval, duplicate results, ties, empty references, missing sample results, and metric-denominator handling.

### 17.6 CI rules

Required CI must use deterministic fixtures and Mock providers. Real API evaluation may run manually or in a separately configured optional workflow, but must not be required for ordinary CI. Test failures must remain visible; never weaken assertions solely to achieve a green build.

---

## 18. Initial Acceptance Gates

RAGBench is ready for portfolio demonstration only when all P0 requirements are verified.

### Gate A — Setup
- [ ] Documented Docker Compose startup succeeds from a clean local state.
- [ ] Required services become healthy.
- [ ] The basic path works without paid API credentials or large model downloads.
- [ ] Actual ports and persistence behavior match documentation.

### Gate B — Ingestion
- [ ] PDF, TXT, Markdown fixtures are accepted.
- [ ] Unsupported/invalid/oversized inputs fail safely.
- [ ] Source and page metadata survive ingestion.
- [ ] Chunk IDs and index configuration are traceable.

### Gate C — RAG answer
- [ ] Query is constrained to the chosen corpus/document scope.
- [ ] Answer citations resolve to actual retrieved/stored chunks.
- [ ] Invalid citations are rejected or flagged.
- [ ] Unanswerable questions produce a clear insufficient-evidence state.
- [ ] Retrieved prompt injection does not grant additional capabilities.

### Gate D — Evaluation
- [ ] Dataset versions and sample ground truth are stored.
- [ ] At least the deterministic retrieval metrics work against test fixtures.
- [ ] Sample failures are visible and not silently dropped.
- [ ] Two configurations can be compared against the same dataset version.
- [ ] LLM-judge metrics, if present, are clearly labeled and optional.

### Gate E — Quality
- [ ] Python/frontend tests and required CI pass with actual outputs.
- [ ] Docker and dependency configuration validate.
- [ ] Secret scanning finds no committed credentials.
- [ ] README setup and benchmark claims are verified.
- [ ] Final independent audit reports no unresolved Critical release blocker.

---

## 19. Portfolio Evidence to Produce

The repository should contain or link to evidence generated by the real implementation:

- Architecture diagram
- Real application screenshots
- One short demo recording or GIF
- Example question with citations
- Example unanswerable question with abstention
- Dataset sample and documented provenance
- Retrieval benchmark report
- Experiment comparison report
- Test and CI status
- Docker instructions
- Security and limitations summary

Do not add screenshots or numbers that were not generated from the actual running application. If a section is not implemented yet, label it as planned.

---

## 20. Implementation Phase Mapping

Use `RAGBench_Antigravity_Roadmap.md` as the execution sequence. In summary:

1. Product vision and MVP boundaries
2. PRD, requirements, acceptance criteria
3. Architecture and ADRs
4. Repository scaffold and Markdown map
5. Dependency/runtime strategy and developer tooling
6. Local Docker infrastructure
7. Database models and migrations
8. Provider interfaces and Mock mode
9. Secure ingestion
10. Chunking and embedding
11. Qdrant retrieval baseline
12. RAG orchestration and citation validation
13. Frontend design system
14. Frontend/API integration
15. Evaluation dataset and deterministic metrics
16. Optional answer-quality evaluation
17. Experiment runner and comparison
18. Security and privacy hardening
19. Reliability and observability
20. Performance and benchmarks
21. Automated testing and CI
22. Final Docker workflow
23. README/demo/licensing
24. Independent final audit
25. Root-cause remediation when needed

Each phase must have its own acceptance check. Do not run all prompts in a single task and do not continue on a failed foundational phase.

---

## 21. Official Technical References

Verify current version-specific instructions when implementing:

- FastAPI uploads: https://fastapi.tiangolo.com/tutorial/request-files/
- Docker Compose: https://docs.docker.com/compose/
- Docker Compose startup order: https://docs.docker.com/compose/how-tos/startup-order/
- Qdrant quickstart: https://qdrant.tech/documentation/quickstart/
- Ollama documentation: https://docs.ollama.com/
- Ragas metrics overview: https://docs.ragas.io/en/stable/concepts/metrics/overview/
- Ragas available metrics: https://docs.ragas.io/en/latest/concepts/metrics/available_metrics/
- OpenTelemetry Python: https://opentelemetry.io/docs/languages/python/
- OWASP GenAI / LLM Top 10: https://genai.owasp.org/llm-top-10/
- pgvector (only if reconsidering vector storage in PostgreSQL): https://github.com/pgvector/pgvector

This document is the requirements baseline, not evidence that features have already been implemented. Actual behavior must be verified against code and test output.
