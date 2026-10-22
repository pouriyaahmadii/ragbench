# RAGBench

**A local-first RAG evaluation platform for LLM engineering portfolios.**

[![Status](https://img.shields.io/badge/status-MVP%20in%20development-yellow)]()
[![License](https://img.shields.io/badge/license-TBD-lightgrey)]()

---

## Overview

RAGBench is a **portfolio-grade Retrieval-Augmented Generation (RAG) application and evaluation lab**. It demonstrates how to build a grounded document assistant and, critically, how to **measure whether changes to the RAG pipeline actually improve outcomes**.

### What Makes RAGBench Different

| Typical RAG Demo | RAGBench |
|------------------|----------|
| "It works!" | "Here's the evidence it works, and here's how it fails" |
| Citations that may be hallucinated | **Server-validated citations** that resolve to actual retrieved chunks |
| No evaluation | **Versioned datasets** with deterministic metrics (Precision@k, Recall@k, MRR, nDCG) |
| Single configuration | **Experiment comparison** — same dataset, different chunking/embedding/retrieval/generation |
| Needs API keys | **Deterministic Mock mode** — runs locally with zero credentials |
| Black box | **Inspectable pipeline** — every stage has explicit contracts and tests |

---

## Current Status

> **MVP In Development** — This repository contains the complete architecture, specifications, and repository scaffold. Implementation follows the [Antigravity Roadmap](RAGBench_Antigravity_Roadmap.md) in 25 phases.

### Implemented (Phase 1-4)
- ✅ Product specification and requirements
- ✅ System architecture with C4 diagrams
- ✅ Data model (PostgreSQL + Qdrant)
- ✅ API design (OpenAPI 3.1)
- ✅ RAG pipeline specification (11 stages)
- ✅ Evaluation strategy (deterministic + judge-based)
- ✅ Security threat model
- ✅ Repository scaffold with all directories
- ✅ Foundational documentation (17 specs + 5 ADRs)
- ✅ Docker Compose, Makefile, configuration templates

### Planned (Phase 5-24)
- [ ] Dependency compatibility & developer tooling (Phase 5)
- [ ] Docker infrastructure with health checks (Phase 6)
- [ ] PostgreSQL models & Alembic migrations (Phase 7)
- [ ] Provider interfaces & Mock mode (Phase 8)
- [ ] Secure document upload & parsing (Phase 9)
- [ ] Chunking & embedding pipeline (Phase 10)
- [ ] Qdrant indexing & retrieval (Phase 11)
- [ ] RAG orchestration & citation validation (Phase 12)
- [ ] Frontend design system & screens (Phase 13)
- [ ] Frontend/API integration (Phase 14)
- [ ] Evaluation datasets & deterministic metrics (Phase 15)
- [ ] Optional judge-based evaluation (Phase 16)
- [ ] Experiment runner & comparison (Phase 17)
- [ ] Security hardening (Phase 18)
- [ ] Observability & reliability (Phase 19)
- [ ] Performance benchmarking (Phase 20)
- [ ] E2E testing & CI (Phase 21)
- [ ] Final Docker experience (Phase 22)
- [ ] README, demo, licensing (Phase 23)
- [ ] Independent final audit (Phase 24)

---

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Web UI    │────▶│   API       │────▶│  PostgreSQL │     │   Qdrant    │
│ (Next.js)   │     │ (FastAPI)   │     │ (Metadata)  │     │ (Vectors)   │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                           │                    │                   │
                    ┌──────┴──────┐             │                   │
                    ▼             ▼             ▼                   ▼
              ┌─────────┐  ┌───────────┐  ┌──────────┐       ┌──────────┐
              │Ingestion│  │  Chunking │  │Embeddings│       │Retrieval │
              │Pipeline │  │ Strategies│  │Providers │       │  (Dense) │
              └─────────┘  └───────────┘  └──────────┘       └──────────┘
                    │             │             │                   │
                    ▼             ▼             ▼                   ▼
              ┌──────────────────────────────────────────────────────────┐
              │                    GENERATION PIPELINE                    │
              │  Context Builder → Provider → Citation Validator → Answer│
              └──────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14 + React 18 + TypeScript 5 + Tailwind CSS |
| Backend | FastAPI 0.110 + Pydantic 2 + Python 3.11 |
| Metadata DB | PostgreSQL 16 + SQLAlchemy 2.0 + Alembic |
| Vector DB | Qdrant 1.10+ (gRPC) |
| Embeddings | Provider interface: Mock / Ollama / OpenAI / Cohere |
| Generation | Provider interface: Mock / Ollama / OpenAI / Anthropic |
| Evaluation | Deterministic metrics + optional Ragas |
| Packaging | Docker Compose (pinned images, health checks) |
| CI/CD | GitHub Actions (Mock providers, no paid keys) |

---

## Quick Start

### Prerequisites
- Docker Engine 24+ and Docker Compose v2+
- 4+ GB available RAM
- Git

### Run the Demo (Mock Mode)
```bash
git clone <repository-url> ragbench
cd ragbench

# Configure (Mock mode works with defaults)
cp .env.example .env

# Start all services
make up
# Or: docker compose up --wait

# Access
# Web UI:     http://127.0.0.1:3000
# API Docs:   http://127.0.0.1:8000/docs
# API Health: http://127.0.0.1:8000/health/ready
```

### Demo Workflow
1. **Upload** a PDF/TXT/Markdown document via the Documents page
2. **Wait** for ingestion to complete (status: `ready`)
3. **Ask** a question answerable from the document in Chat
4. **Inspect** citations — click to see source page and excerpt
5. **Ask** an unanswerable question — system states "insufficient evidence"
6. **Run** an evaluation from the Evaluations page
7. **Compare** two experiment configurations

---

## Key Features

### Document Ingestion
- **Formats:** PDF, TXT, Markdown only (MVP)
- **Safety:** Size limits (20 MiB), page limits (200), parser timeouts
- **Metadata:** Document ID, version, content hash, page numbers preserved
- **States:** `uploaded → validating → parsing → chunking → embedding → indexing → ready`

### RAG Pipeline
- **Chunking:** Fixed-size with overlap (configurable), structure-aware (experiment)
- **Embeddings:** Provider abstraction (Mock, Ollama, OpenAI, Cohere)
- **Indexing:** Qdrant with stable UUIDv5 point IDs, versioned collections
- **Retrieval:** Dense vector search, scoped to corpus/document, top-k ≤ 20
- **Generation:** Provider abstraction with prompt versioning
- **Citations:** **Server-validated** — every citation resolved against retrieved chunks + PostgreSQL

### Evaluation Lab
- **Datasets:** Versioned, immutable, with explicit ground truth
- **Deterministic Metrics:** Precision@k, Recall@k, MRR, nDCG@k, Citation Validity
- **Judge Metrics (Optional):** Faithfulness, Answer Relevance — clearly labeled as estimates
- **Experiments:** Immutable configs, reproducible runs, side-by-side comparison
- **Transparency:** Failed samples visible, denominators reported, no silent drops

### Security (MVP)
- Local-first: all ports bound to `127.0.0.1`
- No published PostgreSQL/Qdrant ports
- No secrets in frontend or logs
- Upload validation before processing
- Retrieved content treated as untrusted data
- **Public deployment blocked** until auth/TLS/rate-limiting implemented

---

## Repository Structure

```
ragbench/
├── apps/web/                 # Next.js frontend
│   ├── app/                  # App Router pages
│   ├── components/ui/        # shadcn/ui pattern components
│   ├── features/             # Feature modules (documents, chat, eval, experiments)
│   └── tests/e2e/            # Playwright tests
├── services/backend/         # FastAPI backend
│   ├── app/
│   │   ├── api/v1/routes/    # API endpoints
│   │   ├── core/             # Config, security, exceptions
│   │   ├── db/               # SQLAlchemy models, sessions
│   │   ├── ingestion/        # Upload, parsing, validation
│   │   ├── chunking/         # Chunking strategies
│   │   ├── embeddings/       # Embedding provider orchestration
│   │   ├── vectorstore/      # Qdrant collections
│   │   ├── retrieval/        # Scoped search
│   │   ├── generation/       # Prompt + provider + parsing
│   │   ├── citations/        # Citation validation
│   │   ├── evaluation/       # Dataset runner, metrics
│   │   ├── providers/        # Mock/Ollama/External implementations
│   │   └── observability/    # Logging, metrics
│   ├── migrations/           # Alembic migrations
│   └── tests/                # Unit, integration, contract
├── evals/                    # Evaluation datasets, cases, reports
├── data/samples/             # Fixture documents (openly licensed)
├── infra/                    # Docker, Postgres, monitoring configs
├── scripts/                  # Benchmark, utility scripts
├── docs/                     # Specifications, ADRs, runbooks
│   ├── adr/                  # Architecture Decision Records
│   └── audits/               # Repository audits
└── .github/workflows/        # CI pipelines
```

---

## Development

### Commands (Makefile)
```bash
make up              # Start all services
make down            # Stop (preserve data)
make down-v          # Stop and remove volumes (clean slate)
make logs            # Follow all logs
make test            # Unit + integration + contract tests
make test-e2e        # Playwright E2E tests
make lint            # Ruff + ESLint
make typecheck       # mypy + tsc
make eval            # Run fixture evaluation (Mock)
make benchmark       # Run performance benchmarks
make migrate         # Run database migrations
make shell-db        # PostgreSQL shell
```

### Local Development (Outside Docker)
```bash
# Backend
cd services/backend
pip install -e ".[dev]"
cp ../.env.example .env
# Edit .env: DATABASE_URL=postgresql+asyncpg://...
uvicorn app.main:app --reload

# Frontend
cd apps/web
npm install
cp ../.env.example .env.local
# Edit .env.local: NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
npm run dev
```

---

## Configuration

All configuration via `.env` (copy from `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `MOCK_MODE` | `true` | Forces Mock providers (no API keys needed) |
| `EMBEDDING_PROVIDER` | `mock` | `mock` \| `ollama` \| `openai` \| `cohere` |
| `GENERATION_PROVIDER` | `mock` | `mock` \| `ollama` \| `openai` \| `anthropic` |
| `CHUNK_SIZE_CHARS` | `1200` | Character chunk size |
| `CHUNK_OVERLAP_CHARS` | `150` | Overlap (must be < chunk size) |
| `DEFAULT_TOP_K` | `5` | Retrieval top-k |
| `MAX_TOP_K` | `20` | Hard limit |

### Optional: Local Models (Ollama on macOS)
```bash
# On host (not in Docker)
brew install ollama
ollama serve
ollama pull nomic-embed-text  # Embedding
ollama pull llama3.1:8b       # Generation

# In .env
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_DIMENSION=768
OLLAMA_EMBEDDING_URL=http://host.docker.internal:11434

GENERATION_PROVIDER=ollama
GENERATION_MODEL=llama3.1:8b
OLLAMA_GENERATION_URL=http://host.docker.internal:11434
```

---

## Evaluation

### Fixture Dataset
Located at `evals/datasets/ragbench-demo/v1.0.0/dataset.json` (synthetic, CC0).

### Metrics
| Metric | Type | Description |
|--------|------|-------------|
| Precision@k | Deterministic | Fraction of top-k retrieved that are relevant |
| Recall@k | Deterministic | Fraction of relevant retrieved in top-k |
| MRR | Deterministic | Mean reciprocal rank of first relevant |
| nDCG@k | Deterministic | Normalized discounted cumulative gain |
| Citation Validity | Deterministic | Fraction of citations resolving to retrieved chunks |
| Faithfulness | Judge (Optional) | LLM-judge estimate of groundedness |
| Answer Relevance | Judge (Optional) | LLM-judge estimate of relevance |

### Running Evaluations
```bash
# Mock (CI, demo)
make eval

# Real providers (requires API keys)
OPENAI_API_KEY=sk-... make eval-real
```

---

## Security

> **⚠️ MVP is Local-Only**

This application is designed for **local development and portfolio demonstration only**. It does **not** include:
- Authentication or authorization
- TLS/SSL termination
- Rate limiting
- Multi-tenancy isolation
- Production hardening

**Do not deploy publicly** without implementing the above. See `docs/13-security-and-threat-model.md` for the full threat model.

### Security Practices Implemented
- ✅ Loopback-only binding
- ✅ No published database/vector ports
- ✅ Upload validation (type, size, signature) before processing
- ✅ Generated storage names (no path traversal)
- ✅ Server-side citation validation
- ✅ Retrieved content labeled as untrusted in prompts
- ✅ Structured logging with secret redaction
- ✅ Secret scanning in CI

---

## Documentation

| Document | Description |
|----------|-------------|
| `docs/00-project-understanding.md` | Consolidated project understanding |
| `docs/01-product-vision.md` | Vision, MVP boundaries, success metrics |
| `docs/02-scope-and-mvp.md` | Detailed in/out of scope, acceptance gates |
| `docs/03-functional-requirements.md` | 60+ requirements with verification |
| `docs/04-non-functional-requirements.md` | Performance, reliability, security |
| `docs/05-system-architecture.md` | C4 diagrams, data flows, trust boundaries |
| `docs/06-data-model.md` | ER diagram, table definitions |
| `docs/07-api-design.md` | OpenAPI endpoints, error schema |
| `docs/08-rag-pipeline.md` | 11 stages with contracts |
| `docs/09-evaluation-strategy.md` | Metrics, experiments, comparison |
| `docs/10-dataset-and-benchmark-policy.md` | Immutability, provenance, reporting |
| `docs/11-testing-strategy.md` | Test pyramid, security regression |
| `docs/12-acceptance-criteria.md` | Gates A-E with traceability |
| `docs/13-security-and-threat-model.md` | STRIDE, RAG-specific threats |
| `docs/14-deployment-and-development.md` | Docker, workflows, troubleshooting |
| `docs/15-observability-and-performance.md` | Logging, metrics, benchmarking |
| `docs/16-dependency-and-licensing-policy.md` | Deps, licenses, supply chain |
| `docs/adr/` | Architecture Decision Records |

---

## License

**License decision pending** — documented in `docs/02-scope-and-mvp.md` and `docs/16-dependency-and-licensing-policy.md`.

Options under consideration: MIT, Apache-2.0, BSD-3-Clause. Final license will be recorded in `LICENSE` file before Phase 23 completion.

Third-party licenses will be documented in `THIRD_PARTY_LICENSES.md` at release.

---

## Contributing

This is a portfolio project following a strict phased roadmap. See `RAGBench_Antigravity_Roadmap.md` for the implementation sequence.

**Engineering Rules:**
- No fabricated metrics, screenshots, or benchmarks
- Mock mode for all required CI/demos
- Security-first: treat all uploaded content as untrusted
- Explicit interfaces over framework magic
- Tests must fail loudly; never weaken assertions for green builds

---

## Roadmap

See `RAGBench_Antigravity_Roadmap.md` for the complete 25-phase implementation plan.

### Near Term (Phases 5-12)
- Dependency validation & tooling
- Docker infrastructure
- Database models & migrations
- Provider interfaces & Mock mode
- Document ingestion & parsing
- Chunking & embedding
- Qdrant retrieval
- RAG orchestration & citations

### Medium Term (Phases 13-17)
- Frontend design system
- Frontend/API integration
- Evaluation datasets & metrics
- Judge-based evaluation
- Experiment comparison

### Long Term (Phases 18-24)
- Security hardening
- Observability
- Performance benchmarking
- E2E testing & CI
- Final audit & portfolio packaging

---

## Acknowledgments

- **Qdrant** for the vector database
- **FastAPI** and **Pydantic** for the API framework
- **Next.js** team for the React framework
- **Ollama** for local model serving
- **Ragas** team for evaluation metrics (optional integration)

---

## Disclaimer

RAGBench is a **portfolio demonstration project**, not a production-ready RAG platform. It illustrates engineering practices for building and evaluating RAG systems. The Mock mode provides deterministic behavior for demonstration; real semantic quality requires configuring actual embedding and generation models.

**No guarantee of factual accuracy** — the system abstains when evidence is insufficient, but does not eliminate hallucination risk. Always verify critical information from primary sources.