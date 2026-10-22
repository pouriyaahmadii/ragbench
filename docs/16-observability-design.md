# RAGBench — Observability and Performance

**Version:** 1.0  
**Date:** 2026-10-22  
**Status:** Initialization baseline

---

## Observability Strategy

RAGBench implements **structured logging** as the MVP observability foundation. OpenTelemetry tracing and metrics are deferred to Phase 19.

### Logging

#### Format
All services emit **JSON lines** to stdout for container log aggregation.

```json
{
  "timestamp": "2026-10-22T10:30:45.123Z",
  "level": "INFO",
  "logger": "ingestion.pipeline",
  "message": "Document ingestion completed",
  "request_id": "req-abc123",
  "document_id": "doc-uuid",
  "document_version_id": "ver-uuid",
  "stage": "indexing",
  "duration_ms": 1250,
  "status": "success",
  "metadata": {
    "chunk_count": 42,
    "embedding_provider": "mock",
    "index_version": "idx-uuid"
  }
}
```

#### Standard Fields
| Field | Required | Description |
|-------|----------|-------------|
| `timestamp` | Yes | ISO8601 UTC |
| `level` | Yes | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `logger` | Yes | Module path (e.g., `ingestion.parser`) |
| `message` | Yes | Human-readable summary |
| `request_id` | Yes* | Correlation ID (generated at API boundary) |
| `stage` | For pipeline | Current pipeline stage |
| `duration_ms` | For timed ops | Operation latency |
| `status` | For operations | success, failed, timeout, retry |
| `error_category` | For errors | validation, parsing, embedding, indexing, generation, internal |
| `user_message` | For errors | Safe message for API response |

*Generated at API entry; propagated via contextvars.

#### Redaction Rules
**Never log:**
- API keys, tokens, secrets
- Authorization headers
- Full document content (> 500 chars)
- PII (emails, names, IDs from documents)
- Model outputs (may contain sensitive info)

**Redact automatically:**
- `api_key`, `password`, `secret`, `token` fields → `[REDACTED]`
- Long strings → truncated to 500 chars with `...[truncated]`
- JSON payloads → sanitized by middleware

#### Log Levels by Component
| Component | Default Level | Debug Level |
|-----------|---------------|-------------|
| API Routes | INFO | DEBUG (request/response bodies) |
| Ingestion Pipeline | INFO | DEBUG (per-stage timing) |
| Parser | WARNING | INFO (page counts, warnings) |
| Chunking | INFO | DEBUG (chunk boundaries) |
| Embeddings | INFO | DEBUG (batch sizes, provider calls) |
| Qdrant | WARNING | INFO (query params, latency) |
| Generation | INFO | DEBUG (prompt hash, token counts) |
| Citations | INFO | DEBUG (validation details) |
| Evaluation | INFO | DEBUG (per-sample metrics) |

---

## Correlation IDs

### Generation
- Created at API entry: `request_id = uuid4().hex[:12]` (e.g., `req-a1b2c3d4e5f6`)
- Propagated via `contextvars` through all async calls
- Included in all log lines for that request
- Returned in API response headers: `X-Request-ID`

### Distributed Tracing (Future)
- OpenTelemetry trace ID = `request_id` (or separate)
- Span per pipeline stage
- Exported to OTLP endpoint (configurable)

---

## Metrics (MVP: Log-Based)

### Key Metrics (Logged at Stage Completion)

| Metric | Log Event | Fields |
|--------|-----------|--------|
| `ingestion.duration_ms` | `ingestion.completed` | `document_id`, `version_id`, `stage_durations`, `chunk_count` |
| `ingestion.status` | `ingestion.failed` | `document_id`, `error_category`, `stage` |
| `parse.duration_ms` | `parser.completed` | `document_version_id`, `page_count`, `char_count` |
| `chunk.duration_ms` | `chunker.completed` | `document_version_id`, `chunk_count`, `avg_size` |
| `embed.duration_ms` | `embedding.completed` | `document_version_id`, `batch_count`, `vector_count`, `provider` |
| `index.duration_ms` | `indexing.completed` | `index_version_id`, `point_count`, `collection` |
| `retrieve.duration_ms` | `retrieval.completed` | `corpus_id`, `top_k`, `result_count`, `score_stats` |
| `generate.duration_ms` | `generation.completed` | `provider`, `model`, `prompt_tokens`, `completion_tokens` |
| `citation.validation_ms` | `citation.validated` | `total_citations`, `valid_count`, `validity_rate` |
| `query.total_ms` | `query.completed` | `question_hash`, `status`, `citation_count` |
| `eval.sample_duration_ms` | `evaluation.sample_completed` | `sample_id`, `status`, `metrics` |
| `eval.run_duration_ms` | `evaluation.run_completed` | `experiment_run_id`, `total_samples`, `metrics_summary` |

### Metric Export (Future)
- Prometheus `/metrics` endpoint (Phase 19)
- Key metrics: request rate, latency percentiles, error rate, queue depth
- Custom metrics: ingestion throughput, evaluation progress

---

## Performance Requirements

### Latency Targets (Local Development Hardware)

| Operation | Target (p95) | Measurement |
|-----------|--------------|-------------|
| Upload acceptance (200 response) | < 1s | Time to 202 Accepted |
| PDF parsing (50 pages) | < 10s | Parse stage duration |
| Chunking (1M chars) | < 2s | Chunk stage duration |
| Embedding (100 chunks, Mock) | < 100ms | Embed stage duration |
| Embedding (100 chunks, Ollama) | < 5s | Embed stage duration |
| Vector upsert (1000 chunks) | < 5s | Index stage duration |
| Retrieval (top-5, 10k vectors) | < 200ms | Retrieval stage duration |
| Generation (Mock) | < 50ms | Generation stage duration |
| Generation (Ollama, 8B) | < 10s | Generation stage duration |
| Citation validation | < 50ms | Validation stage duration |
| **Total Query (Mock)** | **< 2s** | End-to-end |
| **Total Query (Ollama)** | **< 15s** | End-to-end |
| Evaluation (50 samples, Mock) | < 60s | Full evaluation run |

### Throughput Targets

| Operation | Target | Conditions |
|-----------|--------|------------|
| Document ingestion | > 5 docs/min | 20 MiB PDFs, Mock providers |
| Chunk processing | > 10,000 chunks/s | Character-based chunker |
| Embedding (Mock) | > 5,000 vectors/s | Batch size 100 |
| Vector upsert | > 500 points/s | Qdrant local |
| Query throughput | > 10 qps | Mock, concurrent |
| Evaluation | > 1 sample/s | Mock, sequential |

### Resource Limits (Default)

| Resource | Limit | Configurable |
|----------|-------|--------------|
| Max upload size | 20 MiB | Yes |
| Max PDF pages | 200 | Yes |
| Max extracted text | 1,000,000 chars | Yes |
| Parser timeout | 30s | Yes |
| Embedding batch size | 100 | Yes |
| Embedding timeout | 60s | Yes |
| Retrieval top-k max | 20 | Yes |
| Context budget | 4,000 chars | Yes |
| Generation max tokens | 1,024 | Yes |
| Generation timeout | 60s | Yes |
| Concurrent ingestion jobs | 1 (in-process) | ADR-005 |
| Concurrent evaluations | 1 | In-process |

---

## Benchmarking

### Benchmark Scripts
Located in `scripts/benchmarks/`:

| Script | Purpose |
|--------|---------|
| `ingestion_benchmark.py` | Measure parse/chunk/embed/index throughput |
| `retrieval_benchmark.py` | Measure query latency at various top-k, index sizes |
| `generation_benchmark.py` | Measure generation latency by provider/model |
| `evaluation_benchmark.py` | Measure full evaluation pipeline |
| `run_all.sh` | Execute full suite with environment capture |

### Benchmark Execution
```bash
# From repo root
make benchmark        # Runs all benchmarks
make bench-ingestion  # Ingestion only
make bench-retrieval  # Retrieval only
make bench-generation # Generation only
make bench-eval       # Evaluation only
```

### Benchmark Report Format
Each benchmark produces `benchmarks/results/benchmark_<name>_<timestamp>.json`:

```json
{
  "benchmark": "retrieval",
  "timestamp": "2026-10-22T10:30:00Z",
  "environment": {
    "hardware": "MacBook Pro M2, 16GB",
    "os": "macOS 14.6",
    "python": "3.11.9",
    "qdrant": "1.10.1",
    "docker": "24.0.7"
  },
  "configuration": {
    "corpus_size": 10000,
    "chunk_count": 50000,
    "embedding_dim": 384,
    "top_k_values": [5, 10, 20]
  },
  "results": {
    "top_5": {
      "p50_ms": 42,
      "p95_ms": 85,
      "p99_ms": 120,
      "samples": 100
    },
    "top_10": { ... },
    "top_20": { ... }
  },
  "warmup_runs": 10,
  "measured_runs": 100
}
```

### Reporting Requirements
Every benchmark claim in documentation MUST reference a reproducible benchmark report with:
- Full environment capture
- Exact command used
- Raw results (not just aggregates)
- Warm/cold distinction

---

## Profiling

### Python Profiling
```bash
# CPU profiling
cd services/backend
python -m cProfile -o profile.stats -m pytest tests/unit/test_chunking.py
# Analyze: python -m pstats profile.stats

# Memory profiling
pip install memray
memray run -m pytest tests/unit/test_chunking.py
memray flamegraph profile.bin
```

### Node.js Profiling
```bash
cd apps/web
npm run build
NODE_OPTIONS="--inspect" npm run start
# Chrome DevTools → Memory/Performance tabs
```

### Database Profiling
```sql
-- Slow queries
SELECT * FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 20;

-- Index usage
SELECT * FROM pg_stat_user_indexes WHERE idx_scan = 0;
```

---

## Alerting (Future)

| Alert | Condition | Severity |
|-------|-----------|----------|
| API down | Health check fails 3x | Critical |
| Ingestion stuck | No progress > 5min | Warning |
| Qdrant unavailable | Health check fails | Critical |
| Disk space | > 80% used | Warning |
| Error rate | > 5% 5xx in 5min | Warning |
| Evaluation failed | Any sample failed | Info |

---

## Performance Testing in CI

### Regression Detection
- Store baseline metrics in `benchmarks/baselines/`
- CI job compares current run to baseline
- Fail if latency increases > 20% or throughput decreases > 20%
- Allow baseline update via manual workflow dispatch

### CI Benchmark Job
```yaml
benchmark:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Start stack
      run: docker compose up --wait
    - name: Run benchmarks
      run: make benchmark
    - name: Compare to baseline
      run: python scripts/compare_benchmarks.py
    - name: Upload results
      uses: actions/upload-artifact@v4
      with:
        name: benchmark-results
        path: benchmarks/results/
```

---

## Capacity Planning (Reference)

| Scale | Documents | Chunks | Vectors | Qdrant RAM | PG Size | Notes |
|-------|-----------|--------|---------|------------|---------|-------|
| Demo | 10 | 500 | 500 | 100 MB | 10 MB | Default MVP |
| Development | 100 | 5,000 | 5,000 | 500 MB | 50 MB | Comfortable |
| Large Local | 1,000 | 50,000 | 50,000 | 2 GB | 500 MB | Near limits |
| Production | 10,000+ | 500,000+ | 500,000+ | 16+ GB | 10+ GB | Requires HA Qdrant |

**Rule:** MVP targets Demo/Development scale. Larger scales require architecture changes (distributed Qdrant, read replicas, etc.).

---

## OpenTelemetry Integration (Phase 19)

### Planned Implementation
- **SDK:** `opentelemetry-instrument` for auto-instrumentation
- **Exporter:** OTLP HTTP to collector (configurable endpoint)
- **Spans:** Per pipeline stage + provider calls
- **Attributes:** Standard semantic conventions + custom (provider, model, corpus)
- **Sampling:** Always sample errors; 10% of success (configurable)

### Span Naming Convention
```
ragbench.ingestion.parse
ragbench.ingestion.chunk
ragbench.ingestion.embed
ragbench.ingestion.index
ragbench.query.retrieve
ragbench.query.generate
ragbench.query.validate_citations
ragbench.evaluation.run
ragbench.evaluation.sample
```

---

## Logging Implementation Checklist

- [ ] Structured JSON logging (structlog or python-json-logger)
- [ ] Request ID middleware (FastAPI)
- [ ] Contextvars propagation for request_id
- [ ] Redaction middleware (secrets, PII, long fields)
- [ ] Stage timing decorators/context managers
- [ ] Standard log fields enforced by base logger
- [ ] Log level configurable via env var
- [ ] Frontend logging (console + optional remote)
- [ ] Docker logging driver configured (json-file with max-size)