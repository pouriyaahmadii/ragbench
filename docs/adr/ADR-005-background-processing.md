# ADR-005: Background Processing (Celery + Redis)

**Status:** Proposed  
**Date:** 2026-10-22  
**Deciders:** Architecture Team (pending validation)  
**Technical Story:** RAGBench initialization

## Context

RAGBench has potentially long-running operations:
- Document ingestion (parsing, chunking, embedding, indexing)
- Evaluation runs (retrieval + generation per sample)
- Experiment comparison (multiple runs)

For MVP, we must decide: **in-process (synchronous) vs background job queue (Celery + Redis)**.

## Current MVP Requirements

| Operation | Expected Duration (Mock) | Expected Duration (Real) | Concurrency Need |
|-----------|--------------------------|--------------------------|------------------|
| Single document ingestion | < 5s | 10-60s | Low (sequential OK) |
| Evaluation (50 samples) | < 30s | 5-15 min | Low (one at a time) |
| Experiment comparison | < 10s | 10-30 min | Low |

**Key Constraint:** MVP is local-first, single-user. No multi-tenancy, no horizontal scaling.

## Options

### Option A: In-Process Only (Recommended for MVP)
- API request handles ingestion/evaluation synchronously
- For long operations: return 202 Accepted with job ID; poll status endpoint
- Background work runs in `asyncio.create_task()` or thread pool
- No Redis, no Celery, no worker containers

### Option B: Celery + Redis from Start
- Add Redis service to Compose
- Add Celery worker service
- Ingestion/evaluation submitted as Celery tasks
- API returns 202 immediately; worker processes async

### Option C: Hybrid (In-Process + Optional Celery)
- Default: in-process with 202/poll pattern
- Celery + Redis available but disabled by default
- Enable via config flag when needed (e.g., large documents, concurrent evaluations)

## Decision

**Choose Option A (In-Process Only) for MVP.**

### Rationale
1. **YAGNI:** MVP workloads fit comfortably in synchronous request/response with 202/poll
2. **Simplicity:** Fewer moving parts = fewer failures, easier debugging, smaller Compose
3. **Local-first alignment:** Single-user local tool doesn't need distributed job queue
4. **Portfolio clarity:** In-process orchestration is more inspectable for reviewers
5. **Deferral cost low:** Adding Celery later is a localized change (API layer only)

### When to Revisit (Trigger for Option B/C)
- Ingestion of >100MB documents causes request timeouts
- Concurrent evaluation runs requested (multi-user future)
- Need for task persistence across API restarts
- Horizontal scaling of workers required

## Implementation (Option A)

### API Pattern for Long Operations
```python
# POST /documents → 202 Accepted
{
  "document_id": "uuid",
  "document_version_id": "uuid",
  "ingestion_job_id": "uuid",
  "status": "validating",
  "poll_url": "/api/v1/ingestion/jobs/{job_id}"
}

# GET /ingestion/jobs/{job_id} → 200 OK
{
  "job_id": "uuid",
  "status": "indexing",
  "stage": "embedding",
  "progress": 0.6,
  "started_at": "ISO8601",
  "estimated_completion": "ISO8601"
}
```

### Background Task Execution
```python
# In API route
async def upload_document(...):
    job_id = uuid4()
    # Persist job record with status="pending"
    await ingestion_repo.create_job(job_id, ...)
    
    # Schedule background work
    asyncio.create_task(run_ingestion_job(job_id, file_path, config))
    
    return AcceptedResponse(job_id=job_id, poll_url=...)

# Background task
async def run_ingestion_job(job_id: UUID, file_path: str, config: IngestionConfig):
    try:
        await ingestion_repo.update_status(job_id, "running", stage="parsing")
        # ... run pipeline stages with status updates ...
        await ingestion_repo.update_status(job_id, "succeeded")
    except Exception as e:
        await ingestion_repo.update_status(job_id, "failed", error=...)
```

### Status Polling (Frontend)
```typescript
// Poll every 2s until terminal state
const pollJob = async (jobId: string) => {
  const response = await api.get(`/ingestion/jobs/${jobId}`);
  if (['succeeded', 'failed', 'cancelled'].includes(response.status)) {
    return response;
  }
  await sleep(2000);
  return pollJob(jobId);
};
```

## Consequences

### Positive
- **Zero infrastructure overhead:** No Redis, no worker containers
- **Simpler deployment:** Fewer services to configure, monitor, debug
- **Easier testing:** No queue mocking; direct function calls in tests
- **Deterministic ordering:** In-process = predictable execution order
- **Lower resource usage:** No Redis memory, no worker processes

### Negative
- **Request timeout risk:** Very large docs may exceed HTTP timeout
- **No persistence across restarts:** Job lost if API crashes mid-ingestion
- **No horizontal scaling:** Can't add workers for throughput
- **Blocking event loop:** CPU-heavy tasks (chunking, embedding) block async loop

### Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| API timeout on large ingestion | Nginx/proxy timeout > max ingestion time; return 202 immediately |
| Event loop blocking | `run_in_executor` for CPU-bound stages (chunking, embedding batch) |
| Job loss on crash | Acceptable for MVP (user re-uploads); document in runbook |
| Concurrent job conflicts | Single-user MVP; queue in frontend if needed |

## Alternatives Rejected

| Alternative | Reason |
|-------------|--------|
| Celery from start | Unnecessary complexity for MVP scale |
| Redis Streams (no Celery) | Still adds Redis; partial solution |
| RQ (Redis Queue) | Same infrastructure cost as Celery |
| Database-backed queue (pg_cron) | Adds PG load; less mature tooling |
| Temporal/Workflow engine | Massive overkill |

## Future Migration Path (If Needed)

1. Add Redis to Compose
2. Add Celery worker service
3. Refactor `run_ingestion_job` → Celery task
4. Update API to dispatch to Celery instead of `create_task`
5. Add Celery monitoring (Flower) if needed
6. **No schema changes** (ingestion_jobs table already exists)

## Related ADRs
- ADR-001: Initial Technology Stack
- ADR-002: RAG Pipeline Boundaries

## Validation Checklist (Before Finalizing)

- [ ] Confirm max document size × processing time < HTTP timeout (default 60s)
- [ ] Confirm `asyncio.to_thread` / `run_in_executor` handles CPU-bound work
- [ ] Test: 200MB PDF (rejected) vs 20MB PDF (processed) with status polling
- [ ] Test: Evaluation run with 100 samples → 202 + poll works
- [ ] Document: How to add Celery later (this ADR serves as guide)