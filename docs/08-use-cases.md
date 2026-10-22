# RAGBench — Use Cases

**Version:** 1.0  
**Date:** 2026-10-22  
**Status:** Phase 2 deliverable

---

## Use Case Diagram (Textual)

```
┌─────────────────────────────────────────────────────────────────┐
│                        RAGBench System                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────┐    ┌────────────────────────────────────────┐    │
│  │  User    │───▶│ UC-01: Upload Document                 │    │
│  └──────────┘    │ UC-02: View Document Library           │    │
│                  │ UC-03: View Document Detail            │    │
│  ┌──────────┐    │ UC-04: Delete Document                 │    │
│  │  User    │───▶│ UC-05: Ask Question (Chat)             │    │
│  └──────────┘    │ UC-06: Inspect Citation Evidence       │    │
│                  │ UC-07: View Evaluation Datasets        │    │
│  ┌──────────┐    │ UC-08: Run Evaluation                  │    │
│  │  User    │───▶│ UC-09: View Experiment Comparison      │    │
│  └──────────┘    │ UC-10: Configure Providers             │    │
│                  └────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Detailed Use Cases

### UC-01: Upload Document

**Primary Actor:** User  
**Preconditions:** System running; user at Documents page  
**Trigger:** User clicks "Upload" and selects file  

**Main Flow:**
1. User selects PDF/TXT/MD file (≤20 MiB)
2. System validates: file size, MIME type, file signature
3. System generates document_id, version_id, safe storage name
4. System computes SHA-256 content hash
5. System stores file, creates document/version records (status: `uploaded`)
6. System returns 202 Accepted with document_id, version_id, ingestion_job_id
7. Background ingestion begins: `validating` → `parsing` → `chunking` → `embedding` → `indexing` → `ready`
8. User sees real-time status updates in UI

**Alternative Flows:**
- **A1: Oversized file** → 413 Payload Too Large with clear message
- **A2: Unsupported format** → 415 Unsupported Media Type
- **A3: Corrupted/malformed** → Ingestion status `failed` with error category
- **A4: Path traversal filename** → Sanitized; stored with UUID name

**Postconditions:** Document record created; ingestion job queued; user sees status

---

### UC-02: View Document Library

**Primary Actor:** User  
**Preconditions:** System running; documents exist  
**Trigger:** User navigates to Documents page  

**Main Flow:**
1. System fetches paginated document list (default 20/page)
2. UI displays: document name, type, size, page count, current version, ingestion status, created date
3. User can search by name, filter by status, sort by date
4. User clicks document to view detail (UC-03)

**Postconditions:** User sees document overview with actions

---

### UC-03: View Document Detail

**Primary Actor:** User  
**Preconditions:** Document exists (any status)  
**Trigger:** User clicks document from library  

**Main Flow:**
1. System fetches document metadata and all versions
2. UI displays: document info, version history, ingestion job status per version
3. For `ready` versions: shows chunk list with pagination (chunk index, page, size, hash)
4. User can click chunk to preview text excerpt
5. User can trigger re-index (UC-04 variant) or delete (UC-04)

**Postconditions:** User has full visibility into document processing

---

### UC-04: Delete Document

**Primary Actor:** User  
**Preconditions:** Document exists  
**Trigger:** User clicks "Delete" and confirms  

**Main Flow:**
1. System shows confirmation dialog with impact: "This will delete document, all versions, chunks, vectors, and ingestion jobs"
2. User confirms
3. System deletes: Qdrant points → PostgreSQL chunks/versions/jobs → document record
4. System returns 204 No Content
5. UI removes document from library

**Alternative Flow:**
- **A1: Document referenced by experiment runs** → Warning shown; force delete option

**Postconditions:** All associated data removed; audit event recorded

---

### UC-05: Ask Question (Chat)

**Primary Actor:** User  
**Preconditions:** At least one corpus has `ready` documents; user at Chat page  
**Trigger:** User types question and submits  

**Main Flow:**
1. User selects corpus (or document scope) and optionally top-k
4. System validates question (non-empty, ≤2000 chars)
5. System embeds question via configured embedding provider
6. System retrieves top-k chunks from Qdrant (corpus-scoped)
7. System builds bounded context with chunk metadata headers
8. System calls generation provider with prompt (question + context + instructions)
9. System parses response into AnswerDraft (text + raw citations)
10. System validates every citation against retrieval results + PostgreSQL
11. System assembles AnswerResponse:
    - `status`: `answered` | `insufficient_evidence` | `failed`
    - `citations`: validated with chunk_id, document_id, page, title, excerpt
    - `limitations`: auto-generated (truncation, mock mode, no evidence)
    - `latency_metadata`: retrieval_ms, generation_ms, total_ms
12. System persists answer and citations
13. UI displays answer with citation links; clicking opens evidence drawer (UC-06)

**Alternative Flows:**
- **A1: No relevant chunks retrieved** → Status `insufficient_evidence`; empty citations; limitation "No relevant evidence found"
- **A2: Generation provider fails** → Status `failed`; safe error message; retry option
- **A3: Citations invalid** → Invalid citations removed; status adjusted; limitation "Some citations could not be validated"

**Postconditions:** Answer displayed with validated citations; answer persisted

---

### UC-06: Inspect Citation Evidence

**Primary Actor:** User  
**Preconditions:** Answer displayed with citations (UC-05 completed)  
**Trigger:** User clicks citation link/badge  

**Main Flow:**
1. System fetches chunk metadata from PostgreSQL (source of truth)
2. System fetches text excerpt from Qdrant payload or chunk storage
3. UI opens drawer/panel showing:
    - Source document title
    - Page number (if PDF)
    - Chunk index
    - Full excerpt (configurable length)
    - Chunk ID, Document ID, Version ID
4. User can close drawer and continue chat

**Postconditions:** User verified citation against actual source

---

### UC-07: View Evaluation Datasets

**Primary Actor:** User  
**Preconditions:** System running; datasets exist  
**Trigger:** User navigates to Evaluations page  

**Main Flow:**
1. System lists datasets with: name, description, current version, sample count, created date
2. User clicks dataset to view versions
3. Version detail shows: version string, schema version, hash, provenance, sample count, compatible index versions
4. User can view paginated samples: sample_id, question, answerable, tags, relevant chunk count
5. User can create new dataset version (if permitted)

**Postconditions:** User understands available evaluation benchmarks

---

### UC-08: Run Evaluation

**Primary Actor:** User  
**Preconditions:** Dataset version selected; compatible index version exists  
**Trigger:** User selects experiment config and clicks "Run Evaluation"  

**Main Flow:**
1. User selects: dataset version, experiment config (or creates new), judge enabled/disabled
2. System validates: dataset version compatible with index version (warns if not)
3. System creates experiment_run record (status: `pending`)
4. For each sample in dataset version:
    a. Retrieve top-k using experiment retrieval config
    b. Generate answer using experiment generation config
    c. Validate citations
    d. Compute deterministic metrics (Precision@k, Recall@k, MRR, nDCG@k, Citation Validity)
    e. If judge enabled: run judge evaluator (record metadata)
    f. Persist sample_result with status, metrics, latency
5. System aggregates metrics across valid samples
6. System persists experiment_run with summary, metric_results, failed/skipped counts
7. UI shows real-time progress; final summary with metrics table

**Alternative Flows:**
- **A1: Sample fails** → Status `failed`; error recorded; excluded from metric denominators
- **A2: Judge fails** → Judge metrics omitted; deterministic metrics still computed
- **A3: User cancels** → Run status `cancelled`; partial results preserved

**Postconditions:** Experiment run completed; results stored; comparison available

---

### UC-09: View Experiment Comparison

**Primary Actor:** User  
**Preconditions:** At least two experiment runs on same dataset version  
**Trigger:** User navigates to Experiments → Compare  

**Main Flow:**
1. User selects two experiment runs (Run A, Run B)
2. System validates: same dataset version; warns if index versions differ
3. System computes:
    - Side-by-side metrics (Precision@5, Recall@5, MRR, nDCG@5, Citation Validity)
    - Deltas (Run B − Run A)
    - Config diff (highlighted changed fields)
    - Sample-level changes (which queries improved/regressed)
    - Failed/skipped counts per run
4. UI displays comparison table with visual indicators (green/red deltas)
5. User can drill into specific sample to see per-sample metrics

**Postconditions:** User understands impact of configuration changes

---

### UC-10: Configure Providers

**Primary Actor:** User  
**Preconditions:** System running; user at Settings page  
**Trigger:** User views/modifies provider configuration  

**Main Flow:**
1. UI displays current provider status:
    - Embedding: provider, model, dimension, Mock mode indicator
    - Generation: provider, model, Mock mode indicator
    - Judge (if enabled): provider, model
2. User can toggle Mock mode (global override)
3. User can view configuration help (required env vars per provider)
4. Changes require API restart (documented)

**Alternative Flow:**
- **A1: Real provider credentials missing** → Clear error: "OPENAI_API_KEY not set; enable Mock mode or configure credentials"

**Postconditions:** User understands current provider setup and requirements

---

## System-Level Use Cases (Background)

### UC-SYS-01: Ingestion Pipeline Execution
**Trigger:** Ingestion job created (UC-01)  
**Flow:** Parse → Normalize → Chunk → Embed → Index → Update status  
**Error Handling:** Each stage catches exceptions; updates job with error_category; cleanup temp files

### UC-SYS-02: Index Version Creation
**Trigger:** New chunking config or embedding model used  
**Flow:** Compute config hash → Check existing index_versions → Create new if different → Update status to `building` → On completion `ready`

### UC-SYS-03: Experiment Reproducibility
**Trigger:** Re-run same experiment config  
**Flow:** Load experiment config → Verify dataset/index versions exist → Execute → Compare metrics bit-identical (Mock)

### UC-SYS-04: Health Monitoring
**Trigger:** Periodic /health/ready checks  
**Flow:** API checks PostgreSQL connectivity → Qdrant connectivity → Returns dependency status

---

## Acceptance Criteria Mapping

| Use Case | Acceptance Criteria (from docs/09-acceptance-criteria.md) |
|----------|----------------------------------------------------------|
| UC-01 | Gate B: B.1-B.8, B.13-B.14 |
| UC-02 | Gate B: B.1-B.3, B.9-B.12 |
| UC-03 | Gate B: B.10-B.12 |
| UC-04 | Gate B: B.15 |
| UC-05 | Gate C: C.1-C.11 |
| UC-06 | Gate C: C.6 |
| UC-07 | Gate D: D.1-D.2 |
| UC-08 | Gate D: D.3-D.10 |
| UC-09 | Gate D: D.6 |
| UC-10 | Gate A: A.5, A.7; Gate E: E.8 |