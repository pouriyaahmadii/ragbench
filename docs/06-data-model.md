# RAGBench — Data Model

**Version:** 1.0  
**Date:** 2026-10-22  
**Status:** Initialization baseline

---

## Design Principles

1. **Immutability by Default:** Document versions, dataset versions, experiment configs, index versions are immutable once created.
2. **Traceability:** Every chunk, vector, answer, and metric links back to its source configuration.
3. **Versioning:** All configuration that affects vectors or metrics is versioned (chunking, embedding, retrieval, generation, prompt).
4. **Separation of Concerns:** PostgreSQL owns metadata and relationships; Qdrant owns vectors and retrieval payloads.
5. **Explicit State Machines:** Ingestion, evaluation, experiment runs have explicit states — no implicit "success because row exists".

---

## Entity Definitions

### 1. Document (Logical Identity)

```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    display_name TEXT NOT NULL,
    media_type TEXT NOT NULL CHECK (media_type IN ('application/pdf', 'text/plain', 'text/markdown')),
    status TEXT NOT NULL CHECK (status IN ('active', 'deleted', 'archived')),
    content_hash CHAR(64) NOT NULL,  -- SHA-256 hex
    size_bytes BIGINT NOT NULL CHECK (size_bytes >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);
```

**Purpose:** Stable logical identity for a document across versions.  
**Indexes:** `unique (content_hash, size_bytes)` for duplicate detection (optional).  
**Deletion:** Soft delete (`deleted_at`); cascade to versions handled by application logic.

---

### 2. Document Version (Immutable Source)

```sql
CREATE TABLE document_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    version_number INT NOT NULL CHECK (version_number > 0),
    parser_version TEXT NOT NULL,
    parser_metadata JSONB NOT NULL DEFAULT '{}',
    content_hash CHAR(64) NOT NULL,
    storage_ref TEXT NOT NULL,  -- Path in object storage or filesystem
    page_count INT NOT NULL DEFAULT 0 CHECK (page_count >= 0),
    ingestion_status TEXT NOT NULL CHECK (ingestion_status IN (
        'uploaded', 'validating', 'parsing', 'chunking', 'embedding', 'indexing',
        'ready', 'rejected', 'failed', 'cancelled', 'ready_with_warnings'
    )),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (document_id, version_number)
);
```

**Purpose:** Immutable snapshot of a document at ingestion time. Parser metadata includes page-level info when available.  
**Indexes:** `idx_doc_ver_doc_id (document_id)`, `idx_doc_ver_status (ingestion_status)`.

---

### 3. Ingestion Job (Attempt Tracking)

```sql
CREATE TABLE ingestion_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_version_id UUID NOT NULL REFERENCES document_versions(id) ON DELETE CASCADE,
    attempt INT NOT NULL DEFAULT 1 CHECK (attempt > 0),
    state TEXT NOT NULL CHECK (state IN (
        'pending', 'running', 'succeeded', 'failed', 'cancelled'
    )),
    stage TEXT CHECK (stage IN (
        'validating', 'parsing', 'chunking', 'embedding', 'indexing', 'finalizing'
    )),
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at TIMESTAMPTZ,
    error_category TEXT CHECK (error_category IN (
        'validation', 'parsing', 'chunking', 'embedding', 'indexing', 'internal', 'timeout', 'resource'
    )),
    user_message TEXT,
    technical_details JSONB DEFAULT '{}',
    UNIQUE (document_version_id, attempt)
);
```

**Purpose:** Audit trail for ingestion attempts; supports retry and debugging.  
**Indexes:** `idx_ing_job_doc_ver (document_version_id)`, `idx_ing_job_state (state)`.

---

### 4. Chunk Metadata (PostgreSQL)

```sql
CREATE TABLE chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_version_id UUID NOT NULL REFERENCES document_versions(id) ON DELETE CASCADE,
    corpus_id UUID NOT NULL,  -- Logical corpus/grouping; FK to future corpus table
    chunk_index INT NOT NULL CHECK (chunk_index >= 0),
    text_hash CHAR(64) NOT NULL,  -- SHA-256 of chunk text
    page_number INT CHECK (page_number > 0),
    start_offset INT CHECK (start_offset >= 0),
    end_offset INT CHECK (end_offset >= start_offset),
    chunker_config_hash CHAR(64) NOT NULL,  -- SHA-256 of canonical chunking config
    embedding_provider TEXT NOT NULL,
    embedding_model TEXT NOT NULL,
    embedding_version TEXT NOT NULL,
    embedding_dimension INT NOT NULL CHECK (embedding_dimension > 0),
    index_version UUID NOT NULL,  -- Ref to index_versions.id
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (document_version_id, chunk_index, chunker_config_hash)
);
```

**Purpose:** Authoritative chunk metadata for citation resolution and experiment reproducibility.  
**Text Storage:** Chunk text NOT stored in PostgreSQL (avoids duplication). Retrieved from Qdrant payload or object storage when needed for citation display.  
**Indexes:** 
- `idx_chunk_doc_ver (document_version_id)`
- `idx_chunk_corpus (corpus_id)`
- `idx_chunk_index_ver (index_version)`
- `idx_chunk_text_hash (text_hash)`

---

### 5. Index Version (Vector Index Identity)

```sql
CREATE TABLE index_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    corpus_id UUID NOT NULL,
    chunking_config_hash CHAR(64) NOT NULL,
    embedding_provider TEXT NOT NULL,
    embedding_model TEXT NOT NULL,
    embedding_version TEXT NOT NULL,
    embedding_dimension INT NOT NULL CHECK (embedding_dimension > 0),
    vector_collection TEXT NOT NULL,  -- Qdrant collection name
    status TEXT NOT NULL CHECK (status IN ('building', 'ready', 'deprecated', 'failed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (corpus_id, chunking_config_hash, embedding_provider, embedding_model, embedding_version, embedding_dimension)
);
```

**Purpose:** Immutable identity for a vector index. Changing ANY of the key configuration fields creates a new index version.  
**Indexes:** `idx_idx_ver_corpus (corpus_id)`, `idx_idx_ver_status (status)`.

---

### 6. Dataset (Logical)

```sql
CREATE TABLE datasets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---

### 7. Dataset Version (Immutable)

```sql
CREATE TABLE dataset_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    version TEXT NOT NULL,  -- Semantic version or timestamp-based
    schema_version TEXT NOT NULL DEFAULT '1.0',
    hash CHAR(64) NOT NULL,  -- SHA-256 of canonical sample serialization
    provenance TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (dataset_id, version)
);
```

**Immutability:** Once created, samples cannot be modified. New version = new `dataset_versions` row.

---

### 8. Dataset Sample

```sql
CREATE TABLE dataset_samples (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_version_id UUID NOT NULL REFERENCES dataset_versions(id) ON DELETE CASCADE,
    sample_id TEXT NOT NULL,  -- Stable human-readable ID (e.g., "sample-001")
    question TEXT NOT NULL,
    corpus_id UUID NOT NULL,  -- Target corpus for retrieval
    relevant_document_ids UUID[] DEFAULT '{}',
    relevant_chunk_ids UUID[] DEFAULT '{}',
    relevance_grades JSONB DEFAULT '{}',  -- {chunk_id: grade}
    reference_answer TEXT,
    expected_citation_ids UUID[] DEFAULT '{}',
    answerable BOOLEAN NOT NULL DEFAULT true,
    tags TEXT[] DEFAULT '{}',
    provenance TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (dataset_version_id, sample_id)
);
```

**Note:** `relevant_chunk_ids` and `relevance_grades` reference specific chunk IDs from a specific index version. Dataset version must document compatible index version(s).

---

### 9. Experiment (Immutable Configuration)

```sql
CREATE TABLE experiments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    config_manifest JSONB NOT NULL,  -- Full configuration snapshot
    config_hash CHAR(64) NOT NULL,   -- SHA-256 of canonical config serialization
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (config_hash)
);
```

**Config Manifest Includes:**
```json
{
  "dataset_version_id": "uuid",
  "index_version_id": "uuid",
  "parser_version": "string",
  "chunking": {"strategy": "fixed", "size": 1200, "overlap": 150, "config_hash": "..."},
  "embedding": {"provider": "...", "model": "...", "version": "...", "dimension": 384},
  "retrieval": {"method": "dense", "top_k": 5, "filters": {}},
  "generation": {"provider": "...", "model": "...", "version": "...", "prompt_version": "..."},
  "judge": {"enabled": false, "provider": "...", "model": "...", "prompt_version": "..."},
  "software_version": "git-commit-hash",
  "timestamp": "ISO8601"
}
```

---

### 10. Experiment Run (Execution Instance)

```sql
CREATE TABLE experiment_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    dataset_version_id UUID NOT NULL REFERENCES dataset_versions(id) ON DELETE RESTRICT,
    index_version_id UUID NOT NULL REFERENCES index_versions(id) ON DELETE RESTRICT,
    status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at TIMESTAMPTZ,
    software_version TEXT NOT NULL,
    environment JSONB DEFAULT '{}',  -- OS, Python, library versions, hardware summary
    total_samples INT NOT NULL DEFAULT 0,
    completed_samples INT NOT NULL DEFAULT 0,
    failed_samples INT NOT NULL DEFAULT 0,
    skipped_samples INT NOT NULL DEFAULT 0
);
```

**Purpose:** Single execution of an experiment against a specific dataset/index. Multiple runs of same experiment = reproducibility check.

---

### 11. Sample Result (Per-Query Outcome)

```sql
CREATE TABLE sample_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_run_id UUID NOT NULL REFERENCES experiment_runs(id) ON DELETE CASCADE,
    sample_id UUID NOT NULL REFERENCES dataset_samples(id) ON DELETE RESTRICT,
    status TEXT NOT NULL CHECK (status IN ('completed', 'failed', 'skipped')),
    retrieval_results JSONB DEFAULT '[]',  -- Array of {chunk_id, rank, score, ...}
    generation_result JSONB,               -- {answer_text, citations[], status, ...}
    citation_validation JSONB,             -- {valid: [], invalid: [], validity_rate: 0.0}
    error_category TEXT,
    error_message TEXT,
    retrieval_latency_ms INT,
    generation_latency_ms INT,
    total_latency_ms INT,
    completed_at TIMESTAMPTZ,
    UNIQUE (experiment_run_id, sample_id)
);
```

---

### 12. Metric Result (Aggregated)

```sql
CREATE TABLE metric_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_run_id UUID NOT NULL REFERENCES experiment_runs(id) ON DELETE CASCADE,
    metric_name TEXT NOT NULL,  -- e.g., "precision@5", "recall@5", "mrr", "ndcg@5", "citation_validity"
    metric_version TEXT NOT NULL DEFAULT '1.0',
    value DOUBLE PRECISION,
    denominator INT,  -- For precision/recall: k or |R|; for MRR: sample count
    evaluator_metadata JSONB DEFAULT '{}',  -- {provider, model, version, prompt_version} for judge metrics
    sample_count INT NOT NULL,
    failed_sample_count INT NOT NULL DEFAULT 0,
    computed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (experiment_run_id, metric_name, metric_version)
);
```

**Deterministic vs Judge:** `evaluator_metadata` empty for deterministic metrics; populated for LLM-judge metrics.

---

### 13. Answer (Query Response)

```sql
CREATE TABLE answers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question TEXT NOT NULL,
    answer_text TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('answered', 'insufficient_evidence', 'failed')),
    limitations TEXT[] DEFAULT '{}',
    provider_metadata JSONB NOT NULL,  -- {provider, model, version, prompt_version}
    latency_metadata JSONB NOT NULL,   -- {retrieval_ms, generation_ms, total_ms}
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---

### 14. Citation (Validated Source Reference)

```sql
CREATE TABLE citations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    answer_id UUID NOT NULL REFERENCES answers(id) ON DELETE CASCADE,
    chunk_id UUID NOT NULL REFERENCES chunks(id) ON DELETE RESTRICT,
    document_id UUID NOT NULL,
    document_version_id UUID NOT NULL,
    page_number INT,
    source_title TEXT NOT NULL,
    excerpt TEXT NOT NULL,  -- From stored chunk text (validated)
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**Validation:** Every citation inserted only after `CitationValidator` confirms `chunk_id` exists in retrieval results AND in `chunks` table with matching document/version.

---

### 15. Audit Event (Optional, Threat Model Dependent)

```sql
CREATE TABLE audit_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type TEXT NOT NULL,  -- e.g., "document_deleted", "experiment_run", "config_changed"
    entity_type TEXT NOT NULL, -- "document", "dataset", "experiment", etc.
    entity_id UUID NOT NULL,
    user_identifier TEXT,      -- For future auth; "local" for MVP
    metadata JSONB DEFAULT '{}',
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---

## Qdrant Payload Schema

Each vector point in Qdrant carries minimal metadata for retrieval and citation resolution:

```json
{
  "chunk_id": "uuid-string",
  "document_id": "uuid-string",
  "document_version_id": "uuid-string",
  "corpus_id": "uuid-string",
  "page_number": 3,
  "source_title": "Policy Document v1",
  "text_excerpt": "First 200 chars of chunk text...",
  "chunk_index": 5
}
```

**Validation Rule:** Before trusting payload metadata for citation display, API verifies `chunk_id` exists in PostgreSQL `chunks` table with matching `document_id`, `document_version_id`, `corpus_id`.

---

## Vector Point ID Strategy

**Format:** UUIDv5 with namespace `ragbench.chunk` and canonical name:  
`{corpus_id}:{document_version_id}:{chunk_index}:{chunker_config_hash}`

**Rationale:** Deterministic, stable, collision-resistant, encodes key identity components.  
**Qdrant Compatibility:** UUID strings supported as point IDs.

---

## Configuration Hashing

All versioned configurations use canonical JSON serialization (sorted keys, no whitespace) + SHA-256.

**Example (Chunking Config):**
```json
{"strategy": "fixed", "size_chars": 1200, "overlap_chars": 150}
→ hash: "a1b2c3d4..."
```

**Example (Embedding Config):**
```json
{"provider": "ollama", "model": "nomic-embed-text", "version": "latest", "dimension": 768}
→ hash: "e5f6g7h8..."
```

---

## Relationships Summary

| Parent | Child | Cardinality | Cascade |
|--------|-------|-------------|---------|
| Document | DocumentVersion | 1:N | CASCADE DELETE |
| DocumentVersion | IngestionJob | 1:N | CASCADE DELETE |
| DocumentVersion | Chunk | 1:N | CASCADE DELETE |
| IndexVersion | Chunk | 1:N (via index_version FK) | RESTRICT |
| Dataset | DatasetVersion | 1:N | CASCADE DELETE |
| DatasetVersion | DatasetSample | 1:N | CASCADE DELETE |
| Experiment | ExperimentRun | 1:N | CASCADE DELETE |
| ExperimentRun | SampleResult | 1:N | CASCADE DELETE |
| ExperimentRun | MetricResult | 1:N | CASCADE DELETE |
| Answer | Citation | 1:N | CASCADE DELETE |
| Chunk | Citation | 1:N | RESTRICT |

---

## Migration Strategy

- **Tool:** Alembic (SQLAlchemy)
- **Naming:** `YYYYMMDD_HHMMSS_description.py`
- **Baseline:** Initial migration creates all tables above
- **Subsequent:** Add columns, indexes, constraints only — no destructive changes without ADR
- **Rollback:** Every migration must have `downgrade()` implemented
- **Testing:** CI runs `alembic upgrade head` → `alembic downgrade base` → `alembic upgrade head` on clean DB

---

## Data Retention and Deletion

| Trigger | Action |
|---------|--------|
| Document soft delete | `documents.deleted_at` set; versions/chunks/jobs remain for audit |
| Document hard delete (admin) | Cascade: versions → chunks → Qdrant points → ingestion_jobs |
| Dataset version | Immutable; never deleted |
| Experiment run | Retained for comparison; manual cleanup only |
| Answer/Citation | Retained with experiment run; linked to chunks |

---

## Open Questions

1. **Corpus Table:** Should `corpus_id` reference a `corpora` table? (Currently UUID only; table deferred)
2. **Chunk Text Storage:** Store full chunk text in PostgreSQL for citation excerpt? (Currently: Qdrant payload only; excerpt retrieved from Qdrant at citation display time)
3. **Conversation History:** Add `conversations` and `messages` tables? (Deferred post-MVP)
4. **Provider Config Table:** Store provider configurations (non-secret) in DB? (Currently: Pydantic Settings only)