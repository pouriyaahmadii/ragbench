# Scripts — Utility and Benchmark Scripts

This directory contains standalone utility scripts for benchmarking, data management, and operational tasks.

## Structure

```
scripts/
├── benchmarks/               # Performance benchmark scripts
│   ├── ingestion_benchmark.py    # Measure parse/chunk/embed/index throughput
│   ├── retrieval_benchmark.py    # Measure query latency at various top-k, index sizes
│   ├── generation_benchmark.py   # Measure generation latency by provider/model
│   ├── evaluation_benchmark.py   # Measure full evaluation pipeline
│   └── run_all.sh                # Execute full suite with environment capture
├── data/                     # Data management scripts
│   ├── load_fixtures.py          # Load fixture documents into running API
│   ├── export_dataset.py         # Export evaluation dataset to JSON/JSONL
│   └── compute_hashes.py         # Compute dataset/config hashes for verification
├── maintenance/              # Operational maintenance scripts
│   ├── backup_postgres.py        # pg_dump with timestamp
│   ├── backup_qdrant.py          # Qdrant snapshot creation
│   ├── restore_postgres.py       # Restore from pg_dump
│   ├── restore_qdrant.py         # Restore from Qdrant snapshot
│   ├── reindex_all.py            # Re-index all documents with new config
│   └── cleanup_old_runs.py       # Archive old experiment runs
├── ci/                       # CI helper scripts
│   ├── check_licenses.py         # Scan dependencies for license compliance
│   ├── compare_benchmarks.py     # Compare current benchmarks to baselines
│   └── validate_openapi.py       # Validate OpenAPI spec consistency
└── dev/                      # Developer convenience scripts
    ├── generate_api_client.sh    # Generate TypeScript API client from OpenAPI
    └── new_migration.sh          # Create new Alembic migration with template
```

## Running Benchmarks

```bash
# From repository root
make benchmark              # Runs all benchmarks
make bench-ingestion        # Ingestion only
make bench-retrieval        # Retrieval only
make bench-generation       # Generation only
make bench-eval             # Evaluation only

# Or directly:
python scripts/benchmarks/ingestion_benchmark.py
```

Each benchmark produces a JSON report in `benchmarks/results/` with:
- Environment capture (hardware, OS, versions)
- Configuration used
- Raw measurements (not just aggregates)
- Warm/cold distinction

## Running Data Scripts

```bash
# Load fixtures into running API
python scripts/data/load_fixtures.py

# Export dataset
python scripts/data/export_dataset.py --dataset ragbench-demo --version 1.0.0

# Compute hashes
python scripts/data/compute_hashes.py --dataset ragbench-demo --version 1.0.0
```

## Running Maintenance

```bash
# Backup
make backup-db              # pg_dump → backups/
make backup-qdrant          # Qdrant snapshot
make backup-all             # Both

# Restore
make restore-db FILE=backups/pg_2026-10-22.sql
make restore-qdrant SNAPSHOT=snapshot_name

# Re-index (prompts for config)
make reindex
```

## Benchmark Report Format

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
    "top_5": {"p50_ms": 42, "p95_ms": 85, "p99_ms": 120, "samples": 100},
    "top_10": { ... },
    "top_20": { ... }
  },
  "warmup_runs": 10,
  "measured_runs": 100
}
```

## Requirements

- Python 3.11+
- Dependencies: `httpx`, `psycopg`, `qdrant-client`, `pyyaml`
- Install: `pip install -r scripts/requirements.txt` (if created)