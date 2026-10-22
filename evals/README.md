# Evals — Evaluation Datasets and Results

This directory contains versioned evaluation datasets, test cases, baselines, and generated reports.

## Structure

```
evals/
├── datasets/                 # Versioned evaluation datasets (immutable)
│   └── ragbench-demo/
│       └── v1.0.0/
│           ├── dataset.json      # Dataset metadata + samples (canonical format)
│           └── dataset.jsonl     # JSONL format for streaming/processing
├── cases/                    # Individual test cases for specific scenarios
│   ├── adversarial/          # Prompt injection, edge cases
│   ├── retrieval/            # Retrieval-specific test cases
│   └── generation/           # Generation-specific test cases
├── baselines/                # Baseline experiment results for regression detection
│   ├── mock-baseline-v1.json     # Mock provider baseline metrics
│   └── ollama-baseline-v1.json   # Local model baseline (when available)
└── reports/                  # Generated evaluation reports (gitignored)
    ├── experiment-*/         # Per-experiment run reports
    └── comparison-*/         # Experiment comparison reports
```

## Dataset Format

Each dataset version contains:

**`dataset.json`** — Canonical format with metadata:
```json
{
  "dataset_id": "ragbench-demo",
  "dataset_version": "1.0.0",
  "description": "Small synthetic dataset for RAGBench CI/demo",
  "provenance": "Synthetic fixture data authored for local development and testing.",
  "schema_version": "1.0",
  "hash": "sha256:...",
  "samples": [
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
      "provenance": "Synthetic fixture document authored for tests."
    }
  ]
}
```

**`dataset.jsonl`** — JSON Lines format (one sample per line) for streaming.

## Immutability Policy

- **Dataset versions are immutable.** Once published, samples cannot be modified.
- Changes require creating a new version (e.g., `v1.1.0`) with a new hash.
- The `hash` field is SHA-256 of canonical JSON serialization (sorted keys, no whitespace).
- Every evaluation run records the dataset version hash for reproducibility.

## Fixture Dataset

The `ragbench-demo/v1.0.0` dataset is a minimal synthetic fixture (3 samples) for:
- CI smoke tests
- Local demo
- Developer onboarding

All samples are synthetic (CC0 / Public Domain) — see `provenance` field.

## Adding Datasets

1. Create directory: `evals/datasets/<dataset-id>/<version>/`
2. Add `dataset.json` with all required fields
3. Generate `dataset.jsonl` from `dataset.json`
4. Compute and verify `hash` field
4. Document provenance and licensing
5. Update this README if adding new dataset

## Reports

The `reports/` directory is **gitignored**. Generated reports include:
- Per-experiment run: metrics summary, per-sample results, config manifest
- Comparison reports: side-by-side metrics, deltas, config diff

Run evaluations via:
```bash
make eval              # Mock mode (CI, demo)
make eval-real         # Real providers (requires API keys)
```