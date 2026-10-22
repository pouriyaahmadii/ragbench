# RAGBench — API Design

**Version:** 1.0  
**Date:** 2026-10-22  
**Status:** Initialization baseline

---

## Design Principles

1. **Contract-First:** OpenAPI 3.1 generated from FastAPI/Pydantic models; frontend consumes generated types.
2. **Explicit Versioning:** All endpoints under `/api/v1/`; breaking changes → new version.
3. **Consistent Error Schema:** RFC 7807 Problem Details with stable error codes.
4. **Async Where Appropriate:** Long-running operations return 202 with job status; short operations synchronous.
5. **Pagination Standard:** Cursor-based for large collections; offset for small.
6. **Validation at Boundary:** Request/response validated by Pydantic; no unvalidated data in business logic.

---

## Base URL

```
http://127.0.0.1:8000/api/v1
```

---

## Health Endpoints

### GET /health/live
Liveness probe — process is running.

**Response 200:**
```json
{"status": "alive"}
```

### GET /health/ready
Readiness probe — all dependencies (PG, Qdrant) responsive.

**Response 200:**
```json
{"status": "ready", "dependencies": {"postgresql": "ok", "qdrant": "ok"}}
```

**Response 503:**
```json
{"status": "not_ready", "dependencies": {"postgresql": "ok", "qdrant": "timeout"}}
```

---

## Document Endpoints

### POST /documents
Upload a document for ingestion.

**Request:** `multipart/form-data`
- `file`: UploadFile (PDF, TXT, Markdown)
- `corpus_id`: UUID (optional, defaults to "default")

**Response 202 Accepted:**
```json
{
  "document_id": "uuid",
  "document_version_id": "uuid",
  "ingestion_job_id": "uuid",
  "status": "validating",
  "message": "Document accepted for processing"
}
```

**Errors:**
- 413: File too large
- 415: Unsupported media type
- 422: Validation error (empty, corrupted, limits exceeded)

---

### GET /documents
List documents with pagination and filtering.

**Query Parameters:**
- `cursor`: string (opaque cursor for pagination)
- `limit`: int (default 20, max 100)
- `status`: enum (active, deleted, archived)
- `corpus_id`: UUID
- `search`: string (search display_name)

**Response 200:**
```json
{
  "items": [
    {
      "id": "uuid",
      "display_name": "string",
      "media_type": "string",
      "status": "string",
      "size_bytes": 12345,
      "page_count": 10,
      "current_version": 1,
      "ingestion_status": "ready",
      "created_at": "ISO8601",
      "updated_at": "ISO8601"
    }
  ],
  "next_cursor": "string|null",
  "total_count": 42
}
```

---

### GET /documents/{document_id}
Get document metadata and versions.

**Response 200:**
```json
{
  "id": "uuid",
  "display_name": "string",
  "media_type": "string",
  "status": "string",
  "size_bytes": 12345,
  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "versions": [
    {
      "id": "uuid",
      "version_number": 1,
      "parser_version": "string",
      "page_count": 10,
      "ingestion_status": "ready",
      "content_hash": "sha256...",
      "created_at": "ISO8601"
    }
  ]
}
```

---

### GET /documents/{document_id}/chunks
List chunk metadata for a document version.

**Query Parameters:**
- `version_id`: UUID (required)
- `cursor`: string
- `limit`: int (default 50, max 200)

**Response 200:**
```json
{
  "items": [
    {
      "id": "uuid",
      "chunk_index": 0,
      "page_number": 1,
      "start_offset": 0,
      "end_offset": 1200,
      "text_hash": "sha256...",
      "chunker_config_hash": "sha256...",
      "embedding_provider": "string",
      "embedding_model": "string",
      "embedding_dimension": 384,
      "index_version": "uuid"
    }
  ],
  "next_cursor": "string|null"
}
```

---

### POST /documents/{document_id}/reindex
Re-index a document version with new configuration.

**Request Body:**
```json
{
  "version_id": "uuid",
  "chunking": {"strategy": "fixed", "size_chars": 1200, "overlap_chars": 150},
  "embedding": {"provider": "mock", "model": "mock", "version": "1.0"}
}
```

**Response 202 Accepted:**
```json
{
  "ingestion_job_id": "uuid",
  "status": "validating",
  "message": "Re-indexing started"
}
```

---

### DELETE /documents/{document_id}
Delete document and all associated data.

**Response 204 No Content**

**Errors:**
- 404: Not found
- 409: Referenced by experiment runs (use force=true to override)

---

## Query Endpoint

### POST /query
Ask a question against a corpus.

**Request Body:**
```json
{
  "question": "string (1-2000 chars)",
  "corpus_id": "uuid",
  "top_k": 5,
  "generation_config": {
    "provider": "mock",
    "model": "mock",
    "temperature": 0.0,
    "max_tokens": 1024
  },
  "retrieval_config": {
    "top_k": 5,
    "document_ids": ["uuid"]  // optional filter
  }
}
```

**Response 200:**
```json
{
  "answer_id": "uuid",
  "question": "string",
  "answer_text": "string",
  "status": "answered | insufficient_evidence | failed",
  "citations": [
    {
      "chunk_id": "uuid",
      "document_id": "uuid",
      "document_version_id": "uuid",
      "page_number": 3,
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
    "retrieval_ms": 45,
    "generation_ms": 120,
    "total_ms": 185
  }
}
```

**Errors:**
- 400: Invalid question, corpus_id not found, top_k out of bounds
- 422: Validation error
- 500: Provider failure (with safe error message)

---

## Dataset Endpoints

### GET /datasets
List datasets.

**Response 200:**
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "string",
      "description": "string",
      "current_version": "1.0.0",
      "sample_count": 50,
      "created_at": "ISO8601"
    }
  ]
}
```

---

### POST /datasets
Create a new dataset.

**Request Body:**
```json
{
  "name": "string",
  "description": "string"
}
```

**Response 201:**
```json
{
  "id": "uuid",
  "name": "string",
  "description": "string",
  "created_at": "ISO8601"
}
```

---

### GET /datasets/{dataset_id}
Get dataset with versions.

**Response 200:**
```json
{
  "id": "uuid",
  "name": "string",
  "description": "string",
  "versions": [
    {
      "id": "uuid",
      "version": "1.0.0",
      "schema_version": "1.0",
      "hash": "sha256...",
      "provenance": "string",
      "sample_count": 50,
      "created_at": "ISO8601"
    }
  ]
}
```

---

### POST /datasets/{dataset_id}/versions
Create a new dataset version (immutable).

**Request Body:**
```json
{
  "version": "1.1.0",
  "samples": [
    {
      "sample_id": "sample-001",
      "question": "string",
      "corpus_id": "uuid",
      "relevant_document_ids": ["uuid"],
      "relevant_chunk_ids": ["uuid"],
      "relevance_grades": {"uuid": 3},
      "reference_answer": "string",
      "expected_citation_ids": ["uuid"],
      "answerable": true,
      "tags": ["tag1"],
      "provenance": "string"
    }
  ]
}
```

**Response 201:**
```json
{
  "id": "uuid",
  "dataset_id": "uuid",
  "version": "1.1.0",
  "hash": "sha256...",
  "sample_count": 50,
  "created_at": "ISO8601"
}
```

---

### GET /datasets/{dataset_id}/versions/{version_id}/samples
Get samples for a dataset version (paginated).

**Response 200:**
```json
{
  "items": [
    {
      "id": "uuid",
      "sample_id": "sample-001",
      "question": "string",
      "corpus_id": "uuid",
      "relevant_document_ids": ["uuid"],
      "relevant_chunk_ids": ["uuid"],
      "relevance_grades": {"uuid": 3},
      "reference_answer": "string",
      "expected_citation_ids": ["uuid"],
      "answerable": true,
      "tags": ["tag1"],
      "provenance": "string"
    }
  ],
  "next_cursor": "string|null"
}
```

---

## Evaluation Endpoints

### POST /evaluations
Start an evaluation run.

**Request Body:**
```json
{
  "experiment_id": "uuid",
  "dataset_version_id": "uuid",
  "index_version_id": "uuid",
  "judge_config": {
    "enabled": false,
    "provider": "ragas",
    "model": "gpt-4",
    "prompt_version": "1.0"
  }
}
```

**Response 202 Accepted:**
```json
{
  "evaluation_id": "uuid",
  "experiment_run_id": "uuid",
  "status": "pending",
  "message": "Evaluation queued"
}
```

---

### GET /evaluations/{evaluation_id}
Get evaluation status and summary.

**Response 200:**
```json
{
  "id": "uuid",
  "experiment_run_id": "uuid",
  "status": "completed",
  "started_at": "ISO8601",
  "ended_at": "ISO8601",
  "total_samples": 50,
  "completed_samples": 48,
  "failed_samples": 2,
  "skipped_samples": 0,
  "metrics_summary": {
    "precision@5": 0.72,
    "recall@5": 0.68,
    "mrr": 0.81,
    "ndcg@5": 0.75,
    "citation_validity": 0.95
  }
}
```

---

### GET /evaluations/{evaluation_id}/samples
Get paginated per-sample results.

**Query Parameters:**
- `cursor`: string
- `limit`: int (default 20, max 100)
- `status`: enum (completed, failed, skipped)

**Response 200:**
```json
{
  "items": [
    {
      "sample_id": "uuid",
      "question": "string",
      "status": "completed",
      "retrieval_results": [
        {"chunk_id": "uuid", "rank": 1, "score": 0.92, "page_number": 3}
      ],
      "generation_result": {
        "answer_text": "string",
        "status": "answered",
        "citations": [{"chunk_id": "uuid", "page_number": 3}]
      },
      "citation_validation": {
        "valid": ["uuid"],
        "invalid": [],
        "validity_rate": 1.0
      },
      "metrics": {
        "precision@5": 1.0,
        "recall@5": 1.0,
        "reciprocal_rank": 1.0
      },
      "latency": {"retrieval_ms": 45, "generation_ms": 120, "total_ms": 185}
    }
  ],
  "next_cursor": "string|null"
}
```

---

## Experiment Endpoints

### GET /experiments
List experiments.

**Response 200:**
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "string",
      "description": "string",
      "config_hash": "sha256...",
      "run_count": 3,
      "created_at": "ISO8601"
    }
  ]
}
```

---

### GET /experiments/{experiment_id}
Get experiment configuration and runs.

**Response 200:**
```json
{
  "id": "uuid",
  "name": "string",
  "description": "string",
  "config_manifest": {...},
  "config_hash": "sha256...",
  "runs": [
    {
      "id": "uuid",
      "dataset_version_id": "uuid",
      "index_version_id": "uuid",
      "status": "completed",
      "started_at": "ISO8601",
      "ended_at": "ISO8601",
      "metrics": {
        "precision@5": 0.72,
        "recall@5": 0.68,
        "mrr": 0.81
      }
    }
  ]
}
```

---

### POST /experiments/compare
Compare two experiment runs.

**Request Body:**
```json
{
  "run_id_a": "uuid",
  "run_id_b": "uuid"
}
```

**Response 200:**
```json
{
  "run_a": {
    "id": "uuid",
    "config": {...},
    "metrics": {"precision@5": 0.72, "recall@5": 0.68, "mrr": 0.81}
  },
  "run_b": {
    "id": "uuid",
    "config": {...},
    "metrics": {"precision@5": 0.78, "recall@5": 0.74, "mrr": 0.85}
  },
  "deltas": {
    "precision@5": 0.06,
    "recall@5": 0.06,
    "mrr": 0.04
  },
  "config_diff": {
    "changed": ["chunking.size_chars", "embedding.model"],
    "details": {
      "chunking.size_chars": {"a": 1200, "b": 800},
      "embedding.model": {"a": "model-a", "b": "model-b"}
    }
  },
  "compatibility_warning": null  // or "Index versions differ; comparison may not be valid"
}
```

---

## Error Schema (RFC 7807)

All error responses use this format:

```json
{
  "type": "https://ragbench.dev/errors/validation-error",
  "title": "Validation Error",
  "status": 422,
  "detail": "Request validation failed",
  "instance": "/api/v1/documents",
  "errors": [
    {
      "field": "file",
      "code": "FILE_TOO_LARGE",
      "message": "File size 25MB exceeds maximum 20MB"
    }
  ]
}
```

**Standard Error Codes:**
- `VALIDATION_ERROR` (422)
- `FILE_TOO_LARGE` (413)
- `UNSUPPORTED_MEDIA_TYPE` (415)
- `NOT_FOUND` (404)
- `CONFLICT` (409)
- `CONFIGURATION_ERROR` (500) — missing provider credentials, etc.
- `PROVIDER_ERROR` (502) — upstream provider failure
- `PROVIDER_TIMEOUT` (504)
- `INTERNAL_ERROR` (500)

---

## Pagination

**Cursor-based (preferred for large collections):**
- Request: `?cursor=opaque_token&limit=20`
- Response: `{items: [...], next_cursor: "token|null"}`

**Offset-based (small collections, UI tables):**
- Request: `?offset=0&limit=20`
- Response: `{items: [...], total_count: 42}`

---

## Rate Limiting (MVP: Advisory)

- API returns `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` headers
- Default: 60 requests/minute per IP (configurable)
- Exceeded → 429 with `Retry-After` header
- Not enforced in Mock mode; documented for production hardening

---

## OpenAPI Generation

```bash
# From API service directory
python -m uvicorn app.main:app --reload
# OpenAPI JSON at http://127.0.0.1:8000/openapi.json
# Frontend: fetch and generate TypeScript types with openapi-typescript
```

---

## API Evolution Policy

| Change | Versioning |
|--------|------------|
| Add optional field | Same version |
| Add new endpoint | Same version |
| Add new enum value | Same version (clients must handle unknown) |
| Remove field | New version (`/api/v2/`) |
| Change field type | New version |
| Change error code | New version |
| Change pagination style | New version |

---

## Mock Mode Headers

When running in Mock mode, responses include:
```
X-RAGBench-Mode: mock
X-RAGBench-Mock-Provider: mock-embedding|mock-generation
```

Frontend uses this to display "Mock Provider" badges.