# API Documentation

## Overview
This document describes the REST API for the RAGBench platform, providing programmatic access to document ingestion, querying, evaluation, and experimentation features.

## Base URL
- **Development**: `http://localhost:8000/api/v1`
- **Staging**: `https://staging.ragbench.dev/api/v1`
- **Production**: `https://api.ragbench.dev/api/v1`

## Authentication
All API endpoints (except health checks) require authentication via Bearer token in the Authorization header:
```
Authorization: Bearer <your-api-token>
```

Tokens can be obtained through the authentication endpoint or generated in the web UI.

## Rate Limiting
- Default: 100 requests/minute per API key
- Burst allowance: 200 requests
- Rate limit headers included in responses:
  - `X-RateLimit-Limit`
  - `X-RateLimit-Remaining`
  - `X-RateLimit-Reset`

## Error Handling
All errors follow RFC 7807 Problem Details format:
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

Common HTTP status codes:
- `200`: Success
- `201`: Created
- `202`: Accepted (async operation)
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `413`: Payload Too Large
- `415`: Unsupported Media Type
- `422`: Unprocessable Entity
- `429`: Too Many Requests
- `500`: Internal Server Error
- `503`: Service Unavailable

## Endpoints

### Health Checks
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe (checks dependencies)

### Documents

#### Upload Document
```
POST /documents
Content-Type: multipart/form-data

Fields:
- file: File (PDF, TXT, MD) - max 20MB
- corpus_id: string (optional)
```

Response (202 Accepted):
```json
{
  "document_id": "uuid",
  "document_version_id": "uuid",
  "ingestion_job_id": "uuid",
  "status": "validating",
  "message": "Document accepted for processing"
}
```

#### List Documents
```
GET /documents?skip=0&limit=20&status=ready&corpus_id=uuid
```

Response:
```json
{
  "items": [...],
  "next_cursor": "string",
  "total_count": 42
}
```

#### Get Document
```
GET /documents/{document_id}
```

#### Get Document Chunks
```
GET /documents/{document_id}/chunks?version_id=uuid&skip=0&limit=50
```

#### Delete Document
```
DELETE /documents/{document_id}
```

#### Re-index Document
```
POST /documents/{document_id}/reindex
{
  "version_id": "uuid",
  "chunking": {"strategy": "fixed", "size_chars": 1200, "overlap_chars": 150},
  "embedding": {"provider": "mock", "model": "mock", "version": "1.0"}
}
```

### Query

#### Ask Question
```
POST /query
{
  "question": "What is the retention period?",
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
    "document_ids": ["uuid"]
  }
}
```

Response:
```json
{
  "answer_id": "uuid",
  "question": "What is the retention period?",
  "answer_text": "The stated retention period is 30 days.",
  "status": "answered",
  "citations": [
    {
      "chunk_id": "uuid",
      "document_id": "uuid",
      "document_version_id": "uuid",
      "page_number": 3,
      "source_title": "Policy Document",
      "excerpt": "The retention period is 30 days."
    }
  ],
  "limitations": [],
  "provider_metadata": {
    "provider": "mock",
    "model": "mock",
    "version": "1.0",
    "prompt_version": "1.0"
  },
  "latency_metadata": {
    "retrieval_ms": 45,
    "generation_ms": 120,
    "total_ms": 185
  }
}
```

### Datasets

#### List Datasets
```
GET /datasets
```

#### Create Dataset
```
POST /datasets
{
  "name": "string",
  "description": "string"
}
```

#### Create Dataset Version
```
POST /datasets/{dataset_id}/versions
{
  "version": "1.0.0",
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

### Evaluations

#### Start Evaluation
```
POST /evaluations
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

Response (202 Accepted):
```json
{
  "evaluation_id": "uuid",
  "experiment_run_id": "uuid",
  "status": "pending",
  "message": "Evaluation queued"
}
```

#### Get Evaluation Status
```
GET /evaluations/{evaluation_id}
```

#### Get Evaluation Samples
```
GET /evaluations/{evaluation_id}/samples?skip=0&limit=20&status=completed
```

### Experiments

#### List Experiments
```
GET /experiments
```

#### Get Experiment
```
GET /experiments/{experiment_id}
```

#### Compare Experiments
```
POST /experiments/compare
{
  "run_id_a": "uuid",
  "run_id_b": "uuid"
}
```

Response:
```json
{
  "run_a": { "id": "uuid", "config": {...}, "metrics": {...} },
  "run_b": { "id": "uuid", "config": {...}, "metrics": {...} },
  "deltas": { "precision@5": 0.06, "recall@5": 0.06, "mrr": 0.04 },
  "config_diff": {
    "changed": ["chunking.size_chars", "embedding.model"],
    "details": { "chunking.size_chars": {"a": 1200, "b": 800} }
  },
  "compatibility_warning": null
}
```

## Webhooks
Webhooks can be configured for async notifications:

### Events
- `document.ingestion.completed`
- `document.ingestion.failed`
- `evaluation.completed`
- `evaluation.failed`

### Webhook Payload
```json
{
  "event": "document.ingestion.completed",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "document_id": "uuid",
    "ingestion_job_id": "uuid"
  }
}
```

## SDKs
- **Python**: `pip install ragbench-client`
- **TypeScript**: `npm install @ragbench/client`
- **Go**: `go get github.com/ragbench/go-client`

## Versioning
API versioned via URL path (`/api/v1/`). Breaking changes require new version.

## Support
- Documentation: https://docs.ragbench.dev
- Issues: https://github.com/ragbench/ragbench/issues
- Email: support@ragbench.dev