# Services/Backend — FastAPI Backend Service

This directory contains the FastAPI backend application with the complete RAG pipeline implementation.

## Structure

```
services/backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── routes/          # FastAPI route modules (documents, query, datasets, evaluations, experiments)
│   ├── core/                    # Cross-cutting concerns
│   │   ├── config.py            # Pydantic Settings (environment configuration)
│   │   ├── security.py          # Security utilities (secret redaction, validation)
│   │   ├── exceptions.py        # Custom exception classes
│   │   ├── middleware.py        # Request ID, logging, error handling middleware
│   │   └── database.py          # SQLAlchemy engine/session setup
│   ├── config/                  # Provider-specific configuration models
│   │   ├── providers.py         # Embedding/Generation/Judge provider configs
│   │   └── pipeline.py          # Chunking, retrieval, generation configs
│   ├── db/                      # Database layer
│   │   ├── base.py              # Declarative base
│   │   ├── session.py           # Async session management
│   │   └── init.py              # Database initialization
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── document.py          # Document, DocumentVersion, IngestionJob
│   │   ├── chunk.py             # Chunk metadata
│   │   ├── index.py             # IndexVersion
│   │   ├── dataset.py           # Dataset, DatasetVersion, DatasetSample
│   │   ├── experiment.py        # Experiment, ExperimentRun, SampleResult, MetricResult
│   │   ├── answer.py            # Answer, Citation
│   │   └── audit.py             # AuditEvent
│   ├── schemas/                 # Pydantic request/response schemas (API contracts)
│   │   ├── document.py
│   │   ├── query.py
│   │   ├── dataset.py
│   │   ├── evaluation.py
│   │   ├── experiment.py
│   │   └── common.py            # Shared schemas (pagination, errors)
│   ├── repositories/            # Data access layer (SQLAlchemy queries)
│   │   ├── document.py
│   │   ├── chunk.py
│   │   ├── dataset.py
│   │   ├── experiment.py
│   │   └── answer.py
│   ├── services/                # Business logic orchestration
│   │   ├── ingestion_service.py     # Document ingestion pipeline coordination
│   │   ├── rag_orchestrator.py      # Query → Retrieve → Generate → Validate
│   │   ├── evaluation_service.py    # Dataset runner, metrics aggregation
│   │   └── experiment_service.py    # Experiment CRUD, comparison
│   ├── ingestion/               # Document ingestion pipeline stages
│   │   ├── parser.py            # PDF/TXT/MD parsing with page metadata
│   │   ├── validator.py         # File validation (size, MIME, signature)
│   │   ├── normalizer.py        # Text normalization (line endings, whitespace)
│   │   └── pipeline.py          # Ingestion orchestration with status updates
│   ├── chunking/                # Chunking strategies
│   │   ├── base.py              # Chunker protocol, base class
│   │   ├── fixed_size.py        # Fixed-size character chunker (baseline)
│   │   ├── structure_aware.py   # Paragraph/heading-aware chunker (experiment)
│   │   └── metadata.py          # Chunk metadata construction
│   ├── embeddings/              # Embedding generation
│   │   ├── provider.py          # EmbeddingProvider protocol
│   │   ├── mock.py              # MockEmbeddingProvider (deterministic)
│   │   ├── ollama.py            # OllamaEmbeddingProvider
│   │   ├── openai.py            # OpenAIEmbeddingProvider
│   │   ├── factory.py           # Provider factory
│   │   └── pipeline.py          # Batch embedding with validation
│   ├── vectorstore/             # Qdrant operations
│   │   ├── client.py            # Qdrant client wrapper
│   │   ├── collections.py       # Collection management (create, delete, versioning)
│   │   ├── upsert.py            # Vector upsert with payload
│   │   ├── query.py             # Vector search with filters
│   │   └── models.py            # Point ID generation, payload schemas
│   ├── retrieval/               # Retrieval logic
│   │   ├── service.py           # Scoped retrieval with top-k
│   │   ├── models.py            # RetrievalResult, RetrievalConfig
│   │   └── filters.py           # Metadata filter construction
│   ├── generation/              # Answer generation
│   │   ├── provider.py          # ChatGenerationProvider protocol
│   │   ├── mock.py              # MockGenerationProvider (fixture-based)
│   │   ├── ollama.py            # OllamaGenerationProvider
│   │   ├── openai.py            # OpenAIGenerationProvider
│   │   ├── anthropic.py         # AnthropicGenerationProvider
│   │   ├── factory.py           # Provider factory
│   │   ├── prompt.py            # Prompt template management (versioned)
│   │   └── parser.py            # Response parsing → AnswerDraft
│   ├── citations/               # Citation validation
│   │   ├── validator.py         # CitationValidator (server-side resolution)
│   │   ├── models.py            # ValidatedCitation, CitationValidationResult
│   │   └── resolver.py          # Metadata resolution from PG + Qdrant
│   ├── evaluation/              # Evaluation pipeline
│   │   ├── metrics/             # Deterministic metric implementations
│   │   │   ├── retrieval.py     # Precision@k, Recall@k, MRR, nDCG@k
│   │   │   ├── citation.py      # Citation Validity
│   │   │   └── base.py          # Metric protocol, base classes
│   │   ├── judge/               # LLM-judge evaluation (optional)
│   │   │   ├── provider.py      # EvaluationJudgeProvider protocol
│   │   │   ├── ragas.py         # RagasJudgeProvider (if available)
│   │   │   └── mock.py          # MockJudgeProvider
│   │   ├── runner.py            # Dataset runner (sample → retrieve → generate → metrics)
│   │   ├── models.py            # ExperimentConfig, ExperimentRun, SampleResult
│   │   └── reporting.py         # JSON/Markdown report generation
│   ├── providers/               # Provider abstraction layer
│   │   ├── protocols.py         # EmbeddingProvider, ChatGenerationProvider, EvaluationJudgeProvider
│   │   ├── factory.py           # Provider factory (Mock/Ollama/OpenAI/Anthropic)
│   │   └── registry.py          # Provider registration
│   ├── workers/                 # Background job definitions (Celery tasks, if enabled)
│   │   ├── ingestion_tasks.py
│   │   ├── evaluation_tasks.py
│   │   └── celery_app.py        # Celery configuration
│   ├── observability/           # Logging, metrics, tracing
│   │   ├── logging.py           # Structured JSON logging setup
│   │   ├── correlation.py       # Correlation ID contextvars
│   │   ├── metrics.py           # Prometheus metrics (if enabled)
│   │   └── tracing.py           # OpenTelemetry setup (Phase 19)
│   └── main.py                  # FastAPI app factory, lifespan, middleware
├── migrations/                  # Alembic database migrations
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
├── tests/
│   ├── unit/                    # Pure logic tests (no external deps)
│   │   ├── test_chunking.py
│   │   ├── test_metrics.py
│   │   ├── test_citations.py
│   │   ├── test_config_hashing.py
│   │   └── test_parsers.py
│   ├── integration/             # Tests with PostgreSQL + Qdrant
│   │   ├── test_ingestion.py
│   │   ├── test_retrieval.py
│   │   ├── test_generation.py
│   │   ├── test_evaluation.py
│   │   └── test_migrations.py
│   ├── contract/                # Provider interface contract tests
│   │   ├── test_embedding_provider.py
│   │   ├── test_generation_provider.py
│   │   └── test_judge_provider.py
│   └── fixtures/                # Test fixtures (sample documents, expected outputs)
├── pyproject.toml               # Project metadata, dependencies, tool config
├── requirements.txt             # Pinned production dependencies
├── requirements-dev.txt         # Pinned development dependencies
├── Dockerfile                   # Multi-stage build (dev/prod targets)
└── alembic.ini                  # Alembic configuration
```

## Key Conventions

- **Protocol-based providers:** All external integrations (embeddings, generation, judge) behind protocols in `providers/protocols.py`
- **Immutable config versioning:** Every config hashed (SHA-256 canonical JSON) and stored with outputs
- **Explicit stage interfaces:** Each pipeline stage has typed input/output (Pydantic models)
- **Server-side citation validation:** Never trust model-generated citations; resolve against PG + Qdrant
- **Deterministic Mock providers:** CI and demo work without paid APIs or model downloads
- **Structured logging:** JSON lines with correlation IDs, stage durations, error categories

## Development

```bash
# From services/backend/
pip install -e ".[dev]"     # Install with dev dependencies
cp ../.env.example .env     # Configure environment
alembic upgrade head        # Run migrations
uvicorn app.main:app --reload --port 8000

# Testing
pytest tests/unit -v        # Unit tests (fast, no external deps)
pytest tests/integration -v # Integration tests (requires PG + Qdrant)
pytest tests/contract -v    # Contract tests (all provider implementations)
pytest --cov=app --cov-fail-under=80  # Coverage check

# Code Quality
ruff check .                # Lint
ruff format .               # Format
mypy .                      # Type check (strict)
```

## Environment Variables

Key variables (see `.env.example` in repository root):

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL async connection string |
| `QDRANT_URL` | Qdrant gRPC/HTTP endpoint |
| `MOCK_MODE` | Force Mock providers (`true`/`false`) |
| `EMBEDDING_PROVIDER` | `mock` \| `ollama` \| `openai` \| `cohere` |
| `GENERATION_PROVIDER` | `mock` \| `ollama` \| `openai` \| `anthropic` |
| `OLLAMA_EMBEDDING_URL` | Ollama endpoint for embeddings |
| `OLLAMA_GENERATION_URL` | Ollama endpoint for generation |
| `OPENAI_API_KEY` | OpenAI API key (if provider=openai) |
| `ANTHROPIC_API_KEY` | Anthropic API key (if provider=anthropic) |

## Docker

```bash
# Development (with hot reload via volume mounts)
docker compose up --build api

# Production build
docker build --target production -t ragbench-api .
```

## Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```