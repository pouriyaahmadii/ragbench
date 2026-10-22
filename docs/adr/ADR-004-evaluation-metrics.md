# ADR-004: Evaluation Metrics Strategy

**Status:** Accepted  
**Date:** 2026-10-22  
**Deciders:** Architecture Team  
**Technical Story:** RAGBench initialization

## Context

RAGBench's core value proposition is **reproducible, honest evaluation** of RAG pipelines. The metrics strategy must:
- Separate deterministic measurement from judge-based estimation
- Support experiment comparison with clear validity rules
- Enable CI validation with zero external dependencies
- Produce portfolio-quality reports with full context

## Decision

### Two-Tier Metric System

| Tier | Metrics | Source | Required for MVP |
|------|---------|--------|------------------|
| **Deterministic (Tier 1)** | Precision@k, Recall@k, MRR, nDCG@k, Citation Validity | Explicit ground truth in dataset | ✅ Yes |
| **Judge-Based (Tier 2)** | Faithfulness, Answer Relevance, Citation Completeness, Abstention Accuracy | LLM judge (Ragas or custom) | ❌ Optional (Phase 16) |

### Deterministic Metric Definitions (Tier 1)

**Ground Truth:** `relevant_chunk_ids` and `relevance_grades` in `DatasetSample` (referencing specific `IndexVersion` chunk IDs).

| Metric | Formula | Denominator Convention |
|--------|---------|------------------------|
| **Precision@k** | `|TopK ∩ Relevant| / k` | Always `k` (even if fewer results) |
| **Recall@k** | `|TopK ∩ Relevant| / |Relevant|` | Undefined if `|Relevant|=0` (report separately) |
| **MRR** | `mean(1 / rank_first_relevant)` | 0 if no relevant in TopK; exclude no-ground-truth samples |
| **nDCG@k** | `DCG@k / IDCG@k` with gain `2^rel-1`, discount `log2(rank+1)` | 0 if no graded relevance |
| **Citation Validity** | `valid_citations / total_citations` | 1.0 if no citations generated |

**Edge Case Handling:**
- Samples with no `relevant_chunk_ids`: Excluded from Recall/MRR/nDCG aggregates; counted in `samples_without_ground_truth`
- Fewer than `k` results returned: Precision denominator still `k`
- Tied scores: Stable sort by chunk_id; MRR uses first position
- Duplicate retrieved IDs: Deduplicated before metric calculation (keep highest rank)

### Judge-Based Metrics (Tier 2)

**Implementation:** Behind `EvaluationJudgeProvider` protocol (similar to embedding/generation providers).

**Required Metadata for Every Judge Metric:**
```json
{
  "judge_provider": "ragas|custom",
  "judge_model": "gpt-4|llama-3.1-70b|...",
  "judge_version": "prompt_hash_or_version",
  "metric_version": "1.0",
  "run_timestamp": "ISO8601",
  "failure_state": "success|timeout|error|refusal"
}
```

**Storage:** In `metric_results.evaluator_metadata` JSONB column.

**UI Labeling:** All Tier 2 metrics displayed with "Estimated (Judge)" badge; never mixed with Tier 1 in tables.

### Experiment Configuration for Evaluation

Every experiment records the complete evaluation configuration:

```json
{
  "dataset_version_id": "uuid",
  "dataset_hash": "sha256",
  "index_version_id": "uuid",
  "retrieval_config": {"method": "dense", "top_k": 5},
  "generation_config": {"provider": "...", "model": "...", "prompt_version": "..."},
  "judge_config": {"enabled": false, "provider": "...", "model": "..."},
  "metric_versions": {
    "precision@k": "1.0",
    "recall@k": "1.0",
    "mrr": "1.0",
    "ndcg@k": "1.0",
    "citation_validity": "1.0"
  }
}
```

### Comparison Validity Rules

| Comparison | Valid For | Warning Required |
|------------|-----------|------------------|
| Same dataset, same index, different chunking | Tier 1 only | No (index differs but retrievable) |
| Same dataset, different embedding model | Tier 1 only | Yes (index rebuilt) |
| Same dataset, same index, different generation | Tier 1 + Tier 2 | No |
| Different dataset versions | None | Yes (ground truth differs) |
| Mock vs Real provider | None | Yes (not equivalent) |

**Comparison Output:** Includes `compatibility_warning` field; deltas computed only for compatible metrics.

### CI Validation

**Required CI:** Runs fixture dataset (3-10 samples) with Mock providers.
- Asserts exact metric values (bit-identical reproducibility)
- Tier 1 metrics only
- No external network calls
- Runtime < 30 seconds

**Optional CI:** Real provider evaluation (manual trigger, requires secrets).
- Tier 1 + Tier 2
- Results labeled "real-provider-eval"
- Not required for merge

## Alternatives Considered

| Alternative | Rejected Because |
|-------------|------------------|
| Single metric tier (all judge-based) | Judge bias; non-deterministic; requires paid APIs for CI |
| Ragas as primary | API instability; heavy dependency; judge-based not deterministic |
| Custom judge only | Reinventing wheel; Ragas has community validation |
| No citation validity metric | Critical for RAG honesty; distinguishes retrieval from generation |
| Recall denominator = k (not \|R\|) | Standard IR definition uses \|R\|; k misrepresents coverage |

## Consequences

### Positive
- **Honest reporting:** Clear separation of measured vs estimated
- **CI reliability:** Deterministic metrics = deterministic CI
- **Reproducibility:** Config hashes + dataset hashes = bit-identical re-runs
- **Portfolio credibility:** Reviewers can verify every number
- **Flexibility:** Tier 2 pluggable; Tier 1 always available

### Negative
- **Ground truth effort:** Requires `relevant_chunk_ids` per sample per index version
- **Judge complexity:** Tier 2 adds provider management, prompt versioning, cost
- **Comparison restrictions:** Must document compatibility; cannot freely compare all configs

### Risks
| Risk | Mitigation |
|------|------------|
| Ground truth becomes stale | Dataset versioning; index version compatibility documented |
| Judge prompt drift | Judge config versioned; prompt hash recorded |
| Metric implementation bugs | Unit tests with known fixtures; property-based testing |
| Misleading comparisons | `compatibility_warning` in API/UI; documentation |

## Implementation Notes

1. **Metric Modules:** `services/backend/app/evaluation/metrics/` — pure functions, no I/O
2. **Dataset Version Hash:** SHA-256 of canonical JSON (sorted keys, no whitespace)
3. **Experiment Config Hash:** SHA-256 of canonical config JSON
4. **Result Storage:** `sample_results` (per-sample), `metric_results` (aggregates)
5. **Report Generation:** `services/backend/app/evaluation/reporting.py` → JSON + Markdown
6. **Ragas Integration (Phase 16):** Behind `RagasJudgeProvider` implementing `EvaluationJudgeProvider`

## Related ADRs
- ADR-001: Initial Technology Stack
- ADR-002: RAG Pipeline Boundaries
- ADR-003: Provider Abstraction
- ADR-005: Background Processing (for async evaluation)