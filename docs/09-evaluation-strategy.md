# RAGBench — Evaluation Strategy

**Version:** 1.0  
**Date:** 2026-10-22  
**Status:** Initialization baseline

---

## Evaluation Philosophy

RAGBench separates **deterministic retrieval evaluation** from **judge-based answer quality evaluation**. Deterministic metrics are the mandatory baseline; LLM-judge metrics are optional, clearly labeled estimates.

> **Core Principle:** Never present an LLM judge score as ground truth. Always distinguish: "we measured X" vs "a judge estimated Y".

---

## Three Evaluation Concerns

### A. Retrieval Quality (Deterministic, Mandatory)
Measures: Does the retriever find the relevant chunks?
- **Precision@k:** Of the top-k retrieved, what fraction are relevant?
- **Recall@k:** Of all relevant chunks, what fraction appear in top-k?
- **MRR:** How high is the first relevant result?
- **nDCG@k:** Ranking quality with graded relevance (when available)
- **Citation Validity:** Do generated citations resolve to retrieved chunks?

### B. Answer & Evidence Quality (Judge-Based, Optional)
Measures: Is the generated answer faithful, relevant, well-cited?
- **Faithfulness/Groundedness:** Does answer claim only what evidence supports?
- **Answer Relevance:** Does answer address the question?
- **Citation Completeness/Validity:** Are claims cited? Do citations support claims?
- **Abstention Correctness:** Does system abstain when it should?
- **Reference Answer Match:** Exact match / Token F1 (where appropriate)

### C. Engineering Performance (Measured, Reported)
Measures: What resources does the pipeline consume?
- Latency: parsing, chunking, embedding, indexing, retrieval, generation, total
- Throughput: docs/hour, chunks/sec, queries/sec
- Token usage & estimated cost (when provider reports)
- Indexing time, storage size
- Failed/partial sample rates

---

## Evaluation Dataset Design

### Dataset Versioning (Immutable)
- **Dataset** = logical collection (e.g., "ragbench-demo")
- **DatasetVersion** = immutable snapshot with hash
- **Schema Version** = dataset format version (e.g., "1.0")
- **Hash** = SHA-256 of canonical sample serialization (sorted keys, no whitespace)
- **Provenance** = source/licensing/origin documentation

### Sample Schema
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
  "provenance": "Synthetic fixture document created for RAGBench tests."
}
```

### Field Definitions

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `sample_id` | Yes | string | Stable human-readable ID |
| `question` | Yes | string | Query to test |
| `corpus_id` | Yes | UUID | Target corpus for retrieval |
| `relevant_document_ids` | No | UUID[] | Known relevant documents (coarse) |
| `relevant_chunk_ids` | No | UUID[] | Known relevant chunks for specific index version |
| `relevance_grades` | No | {chunk_id: int} | Graded relevance (1-3) for nDCG |
| `reference_answer` | No | string | Gold answer for comparison |
| `expected_citation_ids` | No | UUID[] | Expected source chunk IDs |
| `answerable` | Yes | boolean | Can this be answered from corpus? |
| `tags` | No | string[] | Topic/difficulty/failure category |
| `provenance` | Yes | string | Source/licensing/origin |

### Dataset Integrity Rules
1. **Immutability:** Once a `DatasetVersion` is created, its samples CANNOT be modified. Changes → new version.
2. **Index Compatibility:** `relevant_chunk_ids` reference specific chunk IDs from a specific `IndexVersion`. Dataset version metadata MUST document compatible index version(s).
3. **Hash Verification:** Every evaluation run records the dataset version hash. Reproducibility check: re-run → same hash.
4. **Provenance:** Every sample documents its origin. Synthetic samples labeled "Synthetic fixture". Public datasets cited with license.

---

## Deterministic Retrieval Metrics (Mandatory)

### Formal Definitions

Let:
- `q` = query
- `R_q` = set of relevant chunk IDs for query `q` (from `relevant_chunk_ids`)
- `TopK_q` = ranked list of retrieved chunk IDs at cutoff `k`
- `rel(c, q)` = relevance grade of chunk `c` for query `q` (from `relevance_grades`), default 1 if binary

#### Precision@k
```
Precision@k(q) = |TopK_q ∩ R_q| / k
```
**Convention:** Denominator is always `k`, even if fewer than `k` results returned. Also report `result_count`.

#### Recall@k
```
Recall@k(q) = |TopK_q ∩ R_q| / |R_q|   if |R_q| > 0
Recall@k(q) = undefined (reported as null)   if |R_q| = 0
```
**Rule:** Samples with no defined relevant chunks are excluded from Recall aggregate; reported separately as `samples_without_ground_truth`.

#### Mean Reciprocal Rank (MRR)
```
RR(q) = 1 / rank of first relevant chunk in TopK_q   (0 if none)
MRR = mean(RR(q)) over all samples with |R_q| > 0
```
**Rule:** Samples with no relevant chunks → RR=0 but reported in `samples_without_ground_truth`.

#### nDCG@k (When Grades Available)
```
DCG@k = Σ_{i=1}^{k} (2^{rel_i} - 1) / log2(i + 1)
IDCG@k = DCG@k of ideal ranking (sorted by relevance grade)
nDCG@k = DCG@k / IDCG@k   (0 if IDCG=0)
```
**Default Gain:** `2^rel - 1` (rel ∈ {1,2,3})
**Default Discount:** `log2(rank + 1)`
**Binary Convention:** If only binary relevance, `rel=1` for relevant, `rel=0` for non-relevant.

#### Citation Validity
```
CitationValidity(q) = |ValidCitations(q)| / |AllCitations(q)|   if |AllCitations| > 0
CitationValidity(q) = 1.0   if |AllCitations| = 0 (no citations made)
```
Where `ValidCitations(q)` = cited chunk IDs that resolve to retrieved chunks in scope.

### Aggregate Reporting
For a dataset with `N` samples:
- Report per-sample metrics + aggregate (mean, std, median)
- Report `valid_sample_count`, `failed_sample_count`, `skipped_sample_count`
- For Recall/MRR: report `samples_with_ground_truth` denominator
- **Never** substitute missing values with 0 without explicit rule

---

## Answer Quality Metrics (Optional, Judge-Based)

### When to Use
- Reference answers exist (`reference_answer` populated)
- Human-reviewed evidence available
- Comparing generation configurations (prompt, model, context budget)

### Metrics

#### Faithfulness / Groundedness (Ragas-style)
**Question:** Does every claim in the answer have support in the retrieved context?
**Method:** LLM judge prompted to verify each claim against context.
**Output:** Score 0-1 + explanation.
**Required Metadata:** Judge provider, model, version, prompt version, timestamp.

#### Answer Relevance
**Question:** Does the answer address the question?
**Method:** LLM judge rates relevance 1-5 or binary.
**Required Metadata:** Same as above.

#### Citation Completeness
**Question:** Are all factual claims accompanied by citations?
**Method:** Rule-based (claim detection) + judge verification.
**Note:** Distinct from Citation Validity (which is deterministic).

#### Abstention Precision/Recall
**Question:** Does system correctly abstain on unanswerable questions?
**Ground Truth:** `answerable: false` samples.
**Metrics:**
- Abstention Precision = TP / (TP + FP) where TP = correct abstention
- Abstention Recall = TP / (TP + FN) where FN = answered but should abstain

#### Reference Answer Similarity
**Exact Match:** Only for closed-form questions (e.g., "What is X?").
**Token F1:** For short-answer datasets with reference answers.
**Semantic Similarity:** Embedding-based (judge or deterministic).

### Judge Metadata (Required for Every Judge Metric)
```json
{
  "judge_provider": "ragas|custom",
  "judge_model": "gpt-4|llama-3.1-70b|...",
  "judge_version": "prompt_version_hash",
  "metric_version": "1.0",
  "run_timestamp": "ISO8601",
  "failure_state": "success|timeout|error|refusal"
}
```

**Storage:** In `metric_results.evaluator_metadata` JSONB.

---

## Engineering Performance Metrics

### Per-Stage Latency
| Stage | Metric | Unit |
|-------|--------|------|
| Parsing | `parse_duration_ms` | ms |
| Chunking | `chunk_duration_ms` | ms |
| Embedding | `embed_duration_ms` | ms |
| Indexing | `index_duration_ms` | ms |
| Retrieval | `retrieval_duration_ms` | ms |
| Generation | `generation_duration_ms` | ms |
| Citation Validation | `citation_validation_ms` | ms |
| **Total** | `total_pipeline_ms` | ms |

### Throughput
- `docs_per_hour` (ingestion)
- `chunks_per_second` (chunking)
- `vectors_per_second` (embedding + indexing)
- `queries_per_second` (retrieval + generation)

### Resource Usage
- Peak memory (RSS)
- GPU memory (if local models)
- Token usage (input/output per provider)
- Estimated cost (if pricing configured)

### Reporting Requirements
Every benchmark report MUST include:
- Hardware: CPU, RAM, GPU (if any)
- OS and version
- Software versions: Python, FastAPI, Qdrant, PostgreSQL, provider SDKs
- Corpus size: document count, chunk count, total chars
- Dataset size: sample count
- Configuration: chunking, embedding, retrieval, generation params
- Warm/cold status: "cold start" vs "warmed (N queries)"
- Actual measurements (not targets)

---

## Experiment Design

### Experiment Configuration (Immutable)
An experiment captures the complete pipeline configuration:
```json
{
  "dataset_version_id": "uuid",
  "dataset_hash": "sha256...",
  "index_version_id": "uuid",
  "parser_version": "string",
  "chunking": {"strategy": "fixed", "size": 1200, "overlap": 150, "config_hash": "..."},
  "embedding": {"provider": "...", "model": "...", "version": "...", "dimension": 384},
  "retrieval": {"method": "dense", "top_k": 5, "filters": {}},
  "generation": {"provider": "...", "model": "...", "version": "...", "prompt_version": "..."},
  "judge": {"enabled": false, "provider": "...", "model": "...", "prompt_version": "..."},
  "software_version": "git-commit-hash",
  "environment": {"os": "...", "python": "...", "hardware": "..."},
  "timestamp": "ISO8601"
}
```

### Experiment Run
- Single execution of an experiment against a dataset/index
- Produces: per-sample results, aggregate metrics, latency/resource summaries
- Multiple runs of same experiment = reproducibility verification

### Comparison Rules
1. **Same Dataset Version:** Both runs must use identical `dataset_version_id` and `dataset_hash`.
2. **Compatible Index:** If `index_version_id` differs (e.g., different embedding model), comparison is valid ONLY for retrieval metrics that don't depend on generation. Generation comparison requires same index.
3. **Explicit Warning:** Comparison API returns `compatibility_warning` if index versions differ.
4. **No Mock vs Real Comparison:** Never compare Mock provider scores to real model quality as equivalent.
5. **Failed Samples Visible:** Comparison shows `failed_sample_count` for each run.
6. **Missing ≠ Zero:** Missing metric (e.g., Recall on no-ground-truth samples) reported as null, not 0.

### Comparison Output
```json
{
  "run_a": {"id": "...", "metrics": {...}, "config": {...}},
  "run_b": {"id": "...", "metrics": {...}, "config": {...}},
  "deltas": {"precision@5": 0.06, "recall@5": 0.06, "mrr": 0.04},
  "config_diff": {"changed": ["chunking.size", "embedding.model"], "details": {...}},
  "compatibility_warning": null,
  "sample_level_changes": [
    {"sample_id": "...", "metric": "precision@5", "a": 1.0, "b": 0.8, "change": -0.2}
  ]
}
```

---

## Evaluation Execution Flow

```
1. Load DatasetVersion (immutable, hash verified)
2. Load Experiment config (immutable, hash verified)
3. Verify IndexVersion compatibility with Experiment config
4. For each sample in DatasetVersion:
   a. Retrieve top-k using Experiment retrieval config
   b. Generate answer using Experiment generation config
   c. Validate citations
   d. Compute deterministic metrics (Precision@k, Recall@k, MRR, nDCG, Citation Validity)
   e. If judge enabled: run judge evaluator
   f. Persist SampleResult
5. Aggregate metrics across samples
6. Persist ExperimentRun + MetricResults
7. Return summary + per-sample details (paginated)
```

---

## CI Integration

### Required CI (Mock Providers)
- Dataset: Small synthetic fixture (3-10 samples)
- Providers: Mock embedding + Mock generation
- Metrics: Deterministic only (Precision@k, Recall@k, MRR, Citation Validity)
- Assertions: Exact expected values for fixture (bit-identical reproducibility)

### Optional CI (Real Providers)
- Separate workflow (manual trigger or scheduled)
- Requires secrets (API keys) in GitHub Secrets
- Reports labeled "real-provider-eval"
- Not required for merge

### Test Fixtures
- Perfect retrieval case
- No relevant results case
- Partial retrieval case
- Duplicate results case
- Tied ranking case
- Empty references case
- Missing chunk IDs case
- Metric denominator edge cases

---

## Reporting

### Machine-Readable (JSON)
- Per-sample results
- Aggregate metrics with denominators
- Experiment config manifest
- Sample failure list

### Human-Readable (Markdown)
```markdown
# Experiment Report: chunk-size-comparison

## Configuration
- Dataset: ragbench-demo v1.0.0 (hash: abc123...)
- Index: demo-corpus-v1 (chunking: fixed-1200-150, embedding: mock-384)

## Results (50 samples)
| Metric | Value | Denominator |
|--------|-------|-------------|
| Precision@5 | 0.72 | 50 |
| Recall@5 | 0.68 | 42* |
| MRR | 0.81 | 42* |
| nDCG@5 | 0.75 | 42* |
| Citation Validity | 0.95 | 48** |

* 8 samples had no ground truth (Recall/MRR/nDCG undefined)
** 2 samples had no citations generated

## Failures
- Sample sample-042: Generation timeout
- Sample sample-047: Retrieval returned empty

## Resource Usage
- Total time: 45s
- Avg latency: 900ms
- Tokens: 12,450 (Mock: N/A)
```

---

## Open Questions

1. **Ragas Integration:** Verify current Ragas API compatibility before Phase 16.
2. **Human Review Workflow:** How to collect human labels for claim-to-evidence support?
3. **Cost Estimation:** Pricing config for providers (input/output $/1M tokens)?
4. **Statistical Significance:** Bootstrap confidence intervals for metric deltas?
5. **Longitudinal Tracking:** Experiment history dashboard for trend analysis?