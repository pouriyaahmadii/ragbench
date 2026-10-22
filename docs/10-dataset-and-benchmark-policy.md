# RAGBench — Dataset and Benchmark Policy

**Version:** 1.0  
**Date:** 2026-10-22  
**Status:** Initialization baseline

---

## Policy Overview

This document establishes the policy for evaluation datasets, benchmark claims, and result reporting in RAGBench. The goal is **honest, reproducible, and verifiable** evaluation — no fabricated numbers, no cherry-picked results, no misleading comparisons.

---

## Dataset Policy

### 1. Dataset Immutability
- **Rule:** Published dataset versions used by experiments are immutable.
- **Enforcement:** Database constraint + application logic. Modifying samples requires creating a new `DatasetVersion` with new hash.
- **Hash:** SHA-256 of canonical JSON serialization (sorted keys, no whitespace, deterministic ordering).

### 2. Dataset Provenance
Every dataset version MUST document:
- **Source:** Origin of questions and ground truth (synthetic, public benchmark, proprietary, human-annotated)
- **License:** License for dataset content (CC-BY, MIT, custom, proprietary)
- **Creation Method:** How samples were constructed (human-written, LLM-generated + verified, extracted from docs)
- **Annotators:** Who created/verified ground truth (if applicable)
- **Version History:** Changelog from previous version

### 3. Ground Truth Requirements
| Ground Truth Type | Required For | Quality Bar |
|-------------------|--------------|-------------|
| `relevant_chunk_ids` | Retrieval metrics (Precision, Recall, MRR, nDCG) | Must match specific `IndexVersion` chunk IDs |
| `relevance_grades` | nDCG | Graded 1-3 by human or verified process |
| `reference_answer` | Answer similarity (Exact Match, Token F1) | Human-verified or canonical |
| `expected_citation_ids` | Citation completeness | Subset of `relevant_chunk_ids` |
| `answerable` | Abstention evaluation | Binary, human-verified |

### 4. Synthetic vs. Real Data
- **Synthetic Data:** Allowed for CI, demo, and development. MUST be labeled `"provenance": "Synthetic fixture..."`.
- **Real Data:** Public benchmarks (e.g., HotpotQA, MS MARCO, NQ) allowed with proper attribution and license compliance.
- **Proprietary Data:** Not committed to repository. Referenced by name only; actual data loaded at runtime from external source.

### 5. Dataset Size Guidelines
| Purpose | Minimum Samples | Target Samples |
|---------|-----------------|----------------|
| CI Smoke Test | 3 | 5-10 |
| Development Iteration | 10 | 20-50 |
| MVP Demo | 20 | 30-50 |
| Portfolio Benchmark | 50 | 100-200 |
| Publication-Grade | 200 | 500+ |

**Rule:** Never claim "benchmark results" on < 50 reviewed samples without explicit "preliminary" label.

### 6. Dataset Distribution
- **Repository:** Only synthetic fixture datasets committed (small, openly licensed).
- **Runtime:** Real datasets loaded via documented download script or manual placement in `data/samples/`.
- **Privacy:** No PII in committed datasets. Real datasets with PII require separate handling (not MVP).

---

## Benchmark Policy

### 1. No Fabricated Numbers
- **Rule:** Every reported number must come from an actual execution of the codebase on actual data.
- **Verification:** Benchmark reports must include the command used, exact output, and environment details.
- **Prohibited:** "Projected", "estimated", "up to", "theoretical" performance numbers presented as measured.

### 2. Required Context for Every Measurement
Every benchmark claim MUST be accompanied by:
```
Hardware: [CPU, RAM, GPU if any]
OS: [e.g., macOS 14.6, Ubuntu 22.04]
Software Versions: [Python, FastAPI, Qdrant, PostgreSQL, provider SDKs]
Corpus: [document count, chunk count, total chars, format mix]
Dataset: [dataset_id, version, sample count, ground truth coverage]
Configuration: [chunking, embedding, retrieval, generation params]
Run Type: [cold start / warmed (N queries)]
Date: [ISO8601]
```

### 3. Warm vs. Cold Reporting
- **Cold Start:** First query after service startup (includes model loading, connection pooling, JIT)
- **Warmed:** After N warmup queries (document N)
- **Rule:** Report both or explicitly state which. Never report warmed as "typical latency" without qualification.

### 4. Statistical Rigor
- **Single Run:** Reported as "single run"; not statistically significant.
- **Multiple Runs:** Report mean ± std over N runs (N ≥ 5 recommended).
- **Confidence Intervals:** Bootstrap 95% CI for metric deltas in comparisons (recommended).
- **Outlier Handling:** Document if outliers excluded and why.

### 5. Comparison Validity
| Comparison Type | Valid If | Invalid If |
|-----------------|----------|------------|
| Same config, different runs | Reproducibility check | N/A |
| Different chunking, same embedding/index | Retrieval metrics only | Generation metrics (index differs) |
| Different embedding, same chunking | New index required | Comparing old index vectors |
| Different generation, same retrieval | Answer quality metrics | Retrieval metrics (unchanged) |
| Mock vs Real provider | Never equivalent | Any quality claim |

### 6. Prohibited Claims
- "X% accuracy" without defining accuracy metric
- "Outperforms [commercial product]" without reproducible head-to-head
- "Eliminates hallucination" (system abstains; does not guarantee factuality)
- "Production-ready" based on local tests only
- Any claim without reproducible command + environment

---

## Result Reporting Standards

### 1. Deterministic vs. Judge Metrics
| Metric Type | Label | Required Metadata |
|-------------|-------|-------------------|
| Precision@k, Recall@k, MRR, nDCG, Citation Validity | `deterministic` | Metric version, denominator, sample count |
| Faithfulness, Answer Relevance, Judge scores | `judge_estimate` | Judge provider, model, version, prompt version, run timestamp, failure state |

**UI Rule:** Judge metrics displayed in separate section with "Estimated (Judge)" badge.

### 2. Denominator Transparency
Every aggregate metric MUST report:
- `value`: the metric value
- `denominator`: what the denominator was (k, |R|, sample count)
- `sample_count`: number of samples contributing
- `failed_count`: samples that failed/skipped
- `undefined_count`: samples where metric undefined (e.g., Recall with no ground truth)

### 3. Failed Sample Handling
- **Rule:** Failed samples are NEVER silently dropped from denominators.
- **Reporting:** `failed_sample_count`, `skipped_sample_count` always reported.
- **Metrics:** Computed over `valid_sample_count` only; denominator reflects this.

### 4. Reproducibility Artifacts
For any reported result, the repository must be able to produce:
- Exact experiment configuration (config hash)
- Dataset version hash
- Index version identity
- Software commit hash
- Command to re-run: `make eval EXPERIMENT=uuid`

---

## Fixture Dataset (Committed)

The repository includes a minimal synthetic fixture dataset at:
```
evals/datasets/ragbench-demo/v1.0.0/dataset.json
```

**Contents:** 3 samples (see `RAGBench_Evaluation_Sample.json`)
**Purpose:** CI smoke test, local demo, developer onboarding
**License:** CC0 (public domain) — synthetic, authored for RAGBench
**Status:** Immutable v1.0.0; changes → v1.1.0

---

## Benchmark Report Template

All benchmark reports (generated or manual) MUST follow this structure:

```markdown
# Benchmark Report: [Experiment Name]

## Executive Summary
- **Experiment:** [name/config_hash]
- **Date:** [ISO8601]
- **Status:** [completed/partial/failed]
- **Key Finding:** [one-sentence summary]

## Environment
| Property | Value |
|----------|-------|
| Hardware | [e.g., MacBook Pro M2, 16GB] |
| OS | [e.g., macOS 14.6] |
| Python | [e.g., 3.11.9] |
| FastAPI | [e.g., 0.110.1] |
| Qdrant | [e.g., 1.10.1] |
| PostgreSQL | [e.g., 16.3] |
| Provider SDKs | [versions] |

## Corpus
| Property | Value |
|----------|-------|
| Corpus ID | [uuid] |
| Documents | [count] |
| Total Chunks | [count] |
| Total Characters | [count] |
| Formats | [PDF: N, TXT: M, MD: K] |
| Chunking Config | [strategy, size, overlap] |
| Embedding Config | [provider, model, dimension] |
| Index Version | [uuid] |

## Dataset
| Property | Value |
|----------|-------|
| Dataset ID | [e.g., ragbench-demo] |
| Version | [e.g., 1.0.0] |
| Hash | [sha256...] |
| Samples | [count] |
| Ground Truth Coverage | [relevant_chunk_ids: X%, relevance_grades: Y%] |
| Provenance | [synthetic/public/proprietary] |

## Configuration
[Full experiment config manifest JSON]

## Results

### Deterministic Retrieval Metrics
| Metric | Value | Denominator | Valid Samples | Failed Samples |
|--------|-------|-------------|---------------|----------------|
| Precision@5 | 0.72 | 5 | 50 | 0 |
| Recall@5 | 0.68 | 42* | 42 | 0 |
| MRR | 0.81 | 42* | 42 | 0 |
| nDCG@5 | 0.75 | 42* | 42 | 0 |
| Citation Validity | 0.95 | 48** | 48 | 0 |

* 8 samples had no ground truth chunks defined
** 2 samples generated no citations

### Judge-Based Answer Quality Metrics (if run)
| Metric | Value | Judge Provider | Judge Model | Samples |
|--------|-------|----------------|-------------|---------|
| Faithfulness | 0.82 | ragas | gpt-4 | 50 |
| Answer Relevance | 0.79 | ragas | gpt-4 | 50 |

### Performance Metrics
| Metric | Value | Unit |
|--------|-------|------|
| Avg Total Latency | 1,240 | ms |
| Avg Retrieval Latency | 45 | ms |
| Avg Generation Latency | 850 | ms |
| Peak Memory | 2.1 | GB |
| Tokens Used (est.) | 45,000 | tokens |
| Estimated Cost | $0.00 | USD (Mock) |

## Failures
| Sample ID | Stage | Error Category | Details |
|-----------|-------|----------------|---------|
| sample-042 | generation | timeout | Mock provider delay simulated |

## Reproducibility
- **Command:** `make eval EXPERIMENT=exp-uuid-123`
- **Config Hash:** `sha256:...`
- **Dataset Hash:** `sha256:...`
- **Index Version:** `uuid`
- **Commit:** `git rev-parse HEAD`

## Limitations
- [List known limitations: small dataset, Mock providers, hardware-specific, etc.]
```

---

## CI Benchmark Gate

### Required (Every PR)
- Run fixture dataset with Mock providers
- Assert deterministic metrics match expected values (exact equality)
- Fail if any metric deviates
- Runtime target: < 30 seconds

### Optional (Scheduled/Manual)
- Real provider evaluation
- Larger dataset (if available)
- Performance regression detection (alert if > 20% latency increase)

---

## Portfolio Presentation Rules

When presenting RAGBench as a portfolio project:

1. **Label Status:** "MVP — In Development" or "MVP — [Date] Release"
2. **Separate Implemented vs. Planned:** Clear feature matrix
3. **Show Real Screenshots:** Only from actual running application
4. **Show Real Metrics:** Only from actual benchmark reports
5. **Disclose Limitations:** Mock mode, local-only, no auth, synthetic data
6. **Link to Reproducible Artifacts:** GitHub Actions run URL, benchmark report in repo
7. **No Fake Badges:** No "tests passing" badge unless CI actually passes

---

## Compliance Checklist for Releases

Before any portfolio demonstration or release claim:

- [ ] All reported metrics generated from actual code execution
- [ ] Benchmark reports include full environment context
- [ ] Dataset provenance documented for all used datasets
- [ ] Deterministic vs. judge metrics clearly separated
- [ ] Failed samples reported in all aggregates
- [ ] Comparison validity warnings present where applicable
- [ ] No unqualified latency/quality claims
- [ ] Synthetic data labeled as synthetic
- [ ] Real data licenses respected and attributed
- [ ] Reproduction commands documented and tested