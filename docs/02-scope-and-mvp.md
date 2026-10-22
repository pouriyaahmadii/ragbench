# RAGBench — Scope and MVP Definition

**Version:** 1.0  
**Date:** 2026-10-22  
**Status:** Initialization baseline

---

## MVP Scope Statement

The Minimum Viable Product delivers a **local-first RAG application with a reproducible evaluation lab**. It enables ingestion of PDF/TXT/Markdown documents, grounded question answering with validated citations, versioned evaluation datasets, deterministic retrieval metrics, and experiment comparison — all runnable via Docker Compose without paid credentials.

---

## In-Scope Capabilities (MVP)

### 1. Document Management
- Upload PDF, TXT, Markdown files via API and UI
- Configurable limits: file size (default 20 MiB), PDF pages (default 200), extracted text (default 1M chars)
- Ingestion pipeline with explicit states: `uploaded → validating → parsing → chunking → embedding → indexing → ready`
- Terminal states: `rejected`, `failed`, `cancelled`, `ready_with_warnings`
- Document metadata persistence: ID, version, display name, media type, content hash, size, page count, timestamps
- Document deletion with cascade to chunks, vectors, derived records
- Safe file handling: generated storage names, no path traversal, cleanup on failure

### 2. Text Processing Pipeline
- **Parsing:** PDF (page-aware), TXT, Markdown with structure preservation
- **Normalization:** Line endings, whitespace; preserve paragraph/page boundaries
- **Chunking:** Fixed-size character chunking (configurable size/overlap), stable IDs, page/offset metadata
- **Chunk Metadata:** chunk_id, document_id, document_version_id, corpus_id, chunk_index, text_hash, page_number, offsets, chunker_config_hash, embedding_provider/model/version/dimension, index_version

### 3. Embedding Generation
- **Provider Interface:** `EmbeddingProvider` with `embed(texts: List[str]) -> EmbeddingResult`
- **Mock Provider:** Deterministic fixed vectors for test inputs (CI, demo)
- **Optional Local:** Ollama embedding endpoint (configured separately)
- **Optional External:** Configurable API provider (OpenAI, Cohere, etc.)
- **Validation:** Dimension check, finite values, batch limits, response length matching
- **Index Versioning:** Embedding provider/model/version/dimension part of index identity

### 4. Vector Indexing (Qdrant)
- Explicit collection per index version (corpus + chunking + embedding config)
- Stable point IDs (UUIDv5 from namespace + canonical chunk identity)
- Payload: chunk_id, document_id, document_version_id, page_number, source_title, text_excerpt
- Upsert with duplicate protection; clean rebuild on config change
- Document deletion → vector removal/invalidation

### 5. Retrieval
- Dense vector search with configurable top-k (default 5, max 20)
- Explicit corpus/document scope filter
- Metadata filtering where supported by data model
- RetrievalResult schema: rank, score/distance, chunk_id, document_id, document_version_id, page, metadata, text
- Score treated as ranking signal, NOT calibrated probability

### 6. Context Construction
- Deduplication of retrieved chunks
- Context size budget enforcement (character/token limit)
- Preserve chunk_id, document_id, page, source_title in context metadata
- Retrieved content labeled as untrusted evidence in prompt

### 7. Answer Generation
- **Provider Interface:** `ChatGenerationProvider` with `generate(messages, config) -> GenerationResult`
- **Mock Provider:** Deterministic answers for test inputs
- **Optional Local:** Ollama chat endpoint
- **Optional External:** Configurable API provider
- Prompt template version recorded in experiment metadata
- Output token budget enforcement
- Response parsed into strict answer schema

### 8. Citation Validation
- Every cited chunk_id validated against retrieval results AND PostgreSQL metadata
- Resolved citations include: chunk_id, document_id, document_version_id, page_number (when available), source_title, excerpt
- Invalid citations → flagged, answer status adjusted
- Model-invented IDs never accepted

### 9. Answer Response Schema
```json
{
  "answer_id": "uuid",
  "question": "string",
  "answer_text": "string",
  "status": "answered | insufficient_evidence | failed",
  "citations": [
    {
      "chunk_id": "string",
      "document_id": "string",
      "document_version_id": "string",
      "page_number": "int|null",
      "source_title": "string",
      "excerpt": "string"
    }
  ],
  "limitations": ["string"],
  "provider_metadata": {
    "provider": "string",
    "model": "string",
    "version": "string",
    "prompt_version": "string"
  },
  "latency_metadata": {
    "retrieval_ms": "int",
    "generation_ms": "int",
    "total_ms": "int"
  }
}
```

### 10. Evaluation Datasets
- Versioned dataset format (immutable once published)
- Sample fields: sample_id, question, corpus_id, relevant_document_ids, relevant_chunk_ids, relevance_grades, reference_answer, expected_citation_ids, answerable, tags, provenance, dataset_version
- Dataset hash recorded for reproducibility
- Synthetic fixture dataset included for CI/demo

### 11. Deterministic Retrieval Metrics
- **Precision@k:** `|TopK ∩ Relevant| / k` (denominator = k)
- **Recall@k:** `|TopK ∩ Relevant| / |Relevant|` (undefined if no relevant; reported separately)
- **MRR:** Mean of `1/rank` of first relevant result (0 if none)
- **nDCG@k:** Graded relevance when available (gain `2^rel-1`, discount `log2(rank+1)`)
- **Citation Validity:** Fraction of cited IDs resolving to retrieved chunks in scope

### 12. Experiment Framework
- Immutable experiment configuration manifest (hash recorded)
- Configuration includes: dataset version, corpus/index versions, parser version, chunking config, embedding provider/model/version/dimension, retrieval method/params, top-k, generation provider/model/version, prompt version, judge config, software version, timestamp
- Runner executes dataset against config, stores per-sample results, computes metrics, produces summary
- Comparison: same dataset version, compatible corpus/index; warns on incompatibility
- Failed samples preserved and counted; missing ≠ zero

### 13. Frontend (Core Screens)
- Dashboard/Overview
- Documents Library (list, search, pagination)
- Upload with ingestion status
- Document Detail (metadata, pages, chunks)
- Chat/Question Answering (answer, citations, evidence drawer)
- Evaluation Datasets (list, detail, run)
- Experiment Comparison (side-by-side metrics, deltas, config diff)
- Settings (provider status, no secrets)

### 14. Infrastructure & Operations
- Docker Compose: PostgreSQL, Qdrant, API, Web
- Loopback-only binding for dev ports
- Persistent named volumes
- Health checks with dependency waiting
- `.env.example` with placeholders only
- Non-destructive Makefile targets: `up`, `down`, `logs`, `test`, `lint`, `eval`
- Mock mode default (no paid keys needed)

### 15. Testing & CI
- Unit tests (pytest): chunking, metrics, citation validation, config hashing
- Integration tests: parser→chunks, Qdrant upsert/query, DB migrations, ingestion, query, evaluation
- E2E tests (Playwright): upload→ingest→query→citation→eval→compare
- Security regression tests
- GitHub Actions: lint, typecheck, unit, integration, contract, frontend, E2E (where feasible), Docker validation, secret scan
- Required CI uses Mock providers only

---

## Out-of-Scope (Explicitly Deferred)

| Capability | Deferred To | Reason |
|------------|-------------|--------|
| Authentication/Authorization | Post-MVP | Single-user local MVP; public deployment blocked |
| Hybrid search (BM25 + dense) | Post-MVP | Dense baseline must be evaluated first |
| Reranking (cross-encoder) | Post-MVP | Requires baseline comparison |
| Query expansion/rewriting | Post-MVP | Core retrieval must work first |
| Conversation history/multi-turn | Post-MVP | Single-turn grounded QA is MVP |
| Ragas/LLM-judge evaluation | Phase 16 (P1) | Deterministic metrics are P0; judge is optional |
| Celery/Redis background workers | ADR-005 decision | In-process sufficient for MVP; add only if justified |
| Multi-corpus/collection management | Post-MVP | Single corpus scope sufficient for MVP |
| Document update/incremental reindex | Post-MVP | Full reindex on config change is clearer |
| Cost tracking/estimation UI | Post-MVP | Token usage recorded; UI deferred |
| Export/import of datasets/experiments | Post-MVP | API + file-based sufficient for MVP |
| Webhook/callback notifications | Post-MVP | Not needed for local demo |
| Multi-language document support | Post-MVP | English-only MVP |
| Accessibility audit (WCAG) | Post-MVP | Basic accessibility in design system; full audit later |

---

## MVP Acceptance Gates (from SPEC §18)

### Gate A — Setup
- [ ] Docker Compose startup succeeds from clean local state
- [ ] Required services become healthy
- [ ] Basic path works without paid API credentials or large model downloads
- [ ] Actual ports and persistence behavior match documentation

### Gate B — Ingestion
- [ ] PDF, TXT, Markdown fixtures accepted
- [ ] Unsupported/invalid/oversized inputs fail safely
- [ ] Source and page metadata survive ingestion
- [ ] Chunk IDs and index configuration traceable

### Gate C — RAG Answer
- [ ] Query constrained to chosen corpus/document scope
- [ ] Answer citations resolve to actual retrieved/stored chunks
- [ ] Invalid citations rejected or flagged
- [ ] Unanswerable questions produce clear insufficient-evidence state
- [ ] Retrieved prompt injection does not grant additional capabilities

### Gate D — Evaluation
- [ ] Dataset versions and sample ground truth stored
- [ ] Deterministic retrieval metrics work against test fixtures
- [ ] Sample failures visible and not silently dropped
- [ ] Two configurations comparable against same dataset version
- [ ] LLM-judge metrics clearly labeled and optional

### Gate E — Quality
- [ ] Python/frontend tests and required CI pass with actual outputs
- [ ] Docker and dependency configuration validate
- [ ] Secret scanning finds no committed credentials
- [ ] README setup and benchmark claims verified
- [ ] Independent audit reports no unresolved Critical release blocker

---

## Dependencies Between MVP Capabilities

```
Document Upload (9)
    ↓
Parsing & Metadata (9)
    ↓
Chunking (10)
    ↓
Embedding (8) ──→ Vector Indexing (11)
    ↓                    ↓
Retrieval (11) ←────────┘
    ↓
Context Construction (12)
    ↓
Generation (8)
    ↓
Citation Validation (12)
    ↓
Answer Response (12)
    ↓
Evaluation Dataset (15) ──→ Deterministic Metrics (15)
    ↓                              ↓
Experiment Runner (17) ←──────────┘
    ↓
Comparison & Reporting (17)
    ↓
Frontend Integration (14)
```

**Critical Path:** Upload → Parse → Chunk → Embed → Index → Retrieve → Generate → Validate → Answer → Evaluate → Compare

---

## Configuration Defaults (MVP)

| Parameter | Default | Configurable | Validation |
|-----------|---------|--------------|------------|
| Max upload size | 20 MiB | Yes | Reject before processing |
| Max PDF pages | 200 | Yes | Reject with clear reason |
| Max extracted text | 1,000,000 chars | Yes | Reject with clear reason |
| Chunk size | 1,200 chars | Yes | > 0 |
| Chunk overlap | 150 chars | Yes | < chunk_size |
| Default top-k | 5 | Yes | ≤ 20 |
| Max top-k | 20 | Yes | Hard bound |
| Context budget | 4,000 chars | Yes | > 0 |
| Generation output | 1,024 tokens | Yes | Provider-dependent |
| Mock E2E target | < 10 sec | N/A | Measured, not guaranteed |

---

## Data Retention and Deletion (MVP)

| Entity | Deletion Behavior |
|--------|-------------------|
| Document | Soft delete → cascade to versions, chunks, vectors, ingestion jobs |
| Document Version | Hard delete only if no dependent experiments; otherwise mark deprecated |
| Chunks | Deleted with document version; vectors removed from Qdrant |
| Vectors | Removed from Qdrant collection on document/version delete |
| Ingestion Jobs | Retained for audit; linked to deleted document |
| Evaluation Datasets | Immutable once published; new version for changes |
| Experiments | Immutable configuration; runs retained for comparison |
| Sample Results | Retained with experiment run |
| Uploaded Files | Deleted from storage on document delete |

---

## License Decision

**Status:** Unresolved — documented here, not silently selected.

Options under consideration:
- MIT (permissive, common for portfolio projects)
- Apache-2.0 (patent grant, explicit contributions)
- BSD-3-Clause (permissive, no endorsement)

**Decision Process:** Final license will be selected before Phase 23 (README/Licensing) and recorded in `LICENSE` file with third-party notices. Until then, this document serves as the license decision note.