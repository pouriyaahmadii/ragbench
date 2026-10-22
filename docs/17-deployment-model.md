# RAGBench — Deployment and Development

**Version:** 1.0  
**Date:** 2026-10-22  
**Status:** Initialization baseline

---

## Local Development Environment

### Prerequisites
- Docker Engine 24+ and Docker Compose v2+
- Git
- Make (optional; commands also runnable directly)
- 4+ GB available RAM
- 2+ GB disk space for volumes

### Quick Start
```bash
git clone <repo-url> ragbench
cd ragbench
cp .env.example .env  # Edit if needed (Mock mode works with defaults)
make up               # Or: docker compose up --wait
# Web UI: http://127.0.0.1:3000
# API:    http://127.0.0.1:8000
# API Docs: http://127.0.0.1:8000/docs
```

### Service URLs (Default)
| Service | URL | Notes |
|---------|-----|-------|
| Web UI | http://127.0.0.1:3000 | Next.js dev server in container |
| API | http://127.0.0.1:8000 | FastAPI with auto-reload |
| API Docs (Swagger) | http://127.0.0.1:8000/docs | OpenAPI 3.1 |
| API Docs (ReDoc) | http://127.0.0.1:8000/redoc | Alternative |

---

## Docker Compose Architecture

### compose.yaml Structure
```yaml
services:
  postgres:
    image: postgres:16
    environment: [POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD]
    volumes: [postgres_data:/var/lib/postgresql/data]
    healthcheck: pg_isready
    ports: []  # Not published

  qdrant:
    image: qdrant/qdrant:1.10
    volumes: [qdrant_data:/qdrant/storage]
    healthcheck: HTTP /healthz
    ports: []  # Not published

  redis:  # Optional (ADR-005)
    image: redis:7-alpine
    volumes: [redis_data:/data]
    healthcheck: redis-cli ping
    ports: []

  api:
    build: ./services/backend
    environment: [DATABASE_URL, QDRANT_URL, REDIS_URL, PROVIDER_CONFIG]
    depends_on: [postgres, qdrant, redis]  # With healthcheck conditions
    ports: ["127.0.0.1:8000:8000"]
    volumes: [./services/backend:/app]  # Dev mount for auto-reload

  web:
    build: ./apps/web
    environment: [NEXT_PUBLIC_API_URL]
    depends_on: [api]
    ports: ["127.0.0.1:3000:3000"]
    volumes: [./apps/web:/app, /app/node_modules, /app/.next]  # Dev mount

  worker:  # Optional (ADR-005)
    build: ./services/backend
    command: celery -A app.workers worker -l info
    depends_on: [redis, postgres, qdrant]
    volumes: [./services/backend:/app]

volumes:
  postgres_data:
  qdrant_data:
  redis_data:
```

### Key Compose Features
- **Healthchecks:** API waits for PG/Qdrant/Redis to be healthy before starting
- **Loopback Binding:** `127.0.0.1:PORT` for all dev-facing ports
- **No Published DB Ports:** PostgreSQL, Qdrant, Redis only on internal Docker network
- **Persistent Volumes:** Named volumes for data survival across restarts
- **Dev Mounts:** Source code mounted for hot-reload (API and Web)
- **Pinned Images:** Exact tags (no `latest`)

---

## Environment Configuration

### .env.example (Template)
```bash
# Application
APP_ENV=development
LOG_LEVEL=INFO

# Database
POSTGRES_DB=ragbench
POSTGRES_USER=ragbench
POSTGRES_PASSWORD=changeme
DATABASE_URL=postgresql+asyncpg://ragbench:changeme@postgres:5432/ragbench

# Vector Store
QDRANT_URL=http://qdrant:6333
QDRANT_API_KEY=  # Optional

# Redis (if Celery enabled)
REDIS_URL=redis://redis:6379/0

# Embedding Provider
EMBEDDING_PROVIDER=mock  # mock | ollama | openai | cohere
EMBEDDING_MODEL=mock
EMBEDDING_DIMENSION=384
OLLAMA_EMBEDDING_URL=http://host.docker.internal:11434  # For Mac native Ollama
OPENAI_API_KEY=  # Required if provider=openai

# Generation Provider
GENERATION_PROVIDER=mock  # mock | ollama | openai | anthropic
GENERATION_MODEL=mock
OLLAMA_GENERATION_URL=http://host.docker.internal:11434
OPENAI_API_KEY=  # Shared or separate
ANTHROPIC_API_KEY=

# Ingestion Limits
MAX_UPLOAD_SIZE_MB=20
MAX_PDF_PAGES=200
MAX_EXTRACTED_CHARS=1000000
PARSER_TIMEOUT_SECONDS=30

# Chunking
CHUNK_SIZE_CHARS=1200
CHUNK_OVERLAP_CHARS=150

# Retrieval
DEFAULT_TOP_K=5
MAX_TOP_K=20

# Generation
MAX_CONTEXT_CHARS=4000
MAX_OUTPUT_TOKENS=1024

# Mock Mode
MOCK_MODE=true  # Forces mock providers regardless of other settings
```

### Configuration Loading
- **Backend:** Pydantic Settings (`app.config.Settings`) loads from environment
- **Frontend:** `NEXT_PUBLIC_*` variables baked at build; runtime config via `/api/config` endpoint
- **Validation:** Startup validation fails fast with clear messages for missing/invalid config

---

## Development Workflows

### Backend Development
```bash
# Start only infrastructure
make infra-up       # docker compose up -d postgres qdrant redis

# Run API locally (outside Docker) with live reload
cd services/backend
pip install -e ".[dev]"
cp ../.env.example .env  # Adjust DATABASE_URL=postgresql+asyncpg://...
uvicorn app.main:app --reload --port 8000

# Run tests
make test-unit
make test-integration
make test-contract
make lint
make typecheck
```

### Frontend Development
```bash
# Start only infrastructure + API
make infra-up
make api-up

# Run Web locally (outside Docker) with hot reload
cd apps/web
npm install
cp ../.env.example .env.local  # NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
npm run dev

# Run tests
npm run test
npm run lint
npm run typecheck
```

### Full Stack in Docker (Default)
```bash
make up              # Start all services
make logs            # Follow all logs
make logs-api        # Follow API logs only
make down            # Stop (preserve volumes)
make down-v          # Stop AND remove volumes (clean slate)
make restart         # Restart services
```

---

## Database Migrations

### Alembic Commands
```bash
# Generate new migration (after model changes)
cd services/backend
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1  # Or: alembic downgrade base

# Show history
alembic history

# Current revision
alembic current
```

### Migration Rules
- Every schema change → migration file
- `downgrade()` must be implemented
- Test: `upgrade head → downgrade base → upgrade head` on clean DB
- No destructive changes without ADR

---

## Mock Mode vs Real Providers

### Mock Mode (Default for CI/Demo)
```bash
MOCK_MODE=true
EMBEDDING_PROVIDER=mock
GENERATION_PROVIDER=mock
```
- Deterministic embeddings (hash-based)
- Deterministic answers (fixture-based)
- No external network calls
- No API keys needed
- Clearly labeled in UI: "Mock Provider"

### Local Models (Ollama on macOS)
```bash
# On host macOS (not in Docker)
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
**Note:** `host.docker.internal` resolves to host Mac from Docker containers.

### External APIs
```bash
# OpenAI
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSION=1536
OPENAI_API_KEY=sk-...

GENERATION_PROVIDER=openai
GENERATION_MODEL=gpt-4o-mini

# Anthropic (generation only)
GENERATION_PROVIDER=anthropic
GENERATION_MODEL=claude-3-haiku-20240307
ANTHROPIC_API_KEY=sk-ant-...
```

---

## Backup and Restore

### Backup Commands
```bash
# PostgreSQL
make backup-db        # pg_dump > backups/pg_$(date +%F).sql

# Qdrant (snapshot)
make backup-qdrant    # curl -X POST http://localhost:6333/snapshots

# Full backup
make backup-all       # Both above + volumes snapshot
```

### Restore Commands
```bash
# PostgreSQL
make restore-db FILE=backups/pg_2026-10-22.sql

# Qdrant
make restore-qdrant SNAPSHOT=snapshot_name

# Full reset (clean slate)
make down-v && make up
```

### Backup Schedule (Local)
- Manual before major changes
- Automated via cron if desired (not configured by default)

---

## Troubleshooting

### Common Issues

| Symptom | Cause | Resolution |
|---------|-------|------------|
| `connection refused` to PG/Qdrant | Services not healthy | `docker compose ps` → check health; `make logs` |
| `dimension mismatch` | Embedding model changed | Re-index: `make reindex` or delete + re-ingest |
| `CUDA out of memory` | Local model too large | Use smaller model; quantize; CPU only |
| `port already in use` | Another process on 3000/8000 | `lsof -ti:3000,8000 \| xargs kill` |
| Frontend shows "Mock Provider" | `MOCK_MODE=true` | Expected for demo; change `.env` for real |
| Migration fails | Schema conflict | Check `alembic history`; manual fix if needed |
| Qdrant collection not found | Index version mismatch | Re-ingest documents; check `index_versions` table |

### Debug Commands
```bash
# API logs
make logs-api

# Database shell
make shell-db        # psql -U ragbench -d ragbench

# Qdrant shell
make shell-qdrant    # curl commands via alias

# Run single test
cd services/backend && pytest tests/unit/test_chunking.py::test_overlap -v

# Inspect OpenAPI
curl http://127.0.0.1:8000/openapi.json | jq .
```

---

## CI/CD Integration

### GitHub Actions Workflows
| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `ci.yml` | Push, PR | Lint, typecheck, unit, integration, contract, Docker validate, secret scan |
| `ci-e2e.yml` | Manual, schedule | Playwright E2E (requires browser) |
| `ci-eval.yml` | Manual | Real provider evaluation (requires secrets) |
| `dependency-review.yml` | PR | Dependency license/vulnerability review |

### Required Secrets (GitHub)
| Secret | Purpose | Required For |
|--------|---------|--------------|
| `OPENAI_API_KEY` | Real provider eval | `ci-eval.yml` |
| `ANTHROPIC_API_KEY` | Real provider eval | `ci-eval.yml` |

---

## Production Deployment (Post-MVP)

**Not implemented in MVP.** Documented for future reference.

### Required Before Public Deployment
1. Authentication (OIDC/OAuth2)
2. Authorization (corpus-level RBAC)
3. TLS certificates (Let's Encrypt or custom)
4. Rate limiting (API + Web)
5. Secret manager (HashiCorp Vault, AWS Secrets Manager, etc.)
6. Log aggregation (Loki, Elasticsearch, Datadog)
7. Metrics/tracing (Prometheus + Grafana, OpenTelemetry)
8. Backup automation (scheduled, tested restores)
9. Disaster recovery plan (RTO/RPO documented)
10. Security audit (penetration test, code review)

### Kubernetes Considerations
- Separate namespaces per environment
- Network policies (deny by default)
- Pod security standards (restricted)
- Horizontal pod autoscaling (API, worker)
- Qdrant operator for HA
- PostgreSQL operator (CloudNativePG) or managed service
- External secrets operator

---

## Makefile Targets Reference

```makefile
# Infrastructure
up              # Start all services (docker compose up --wait)
down            # Stop services (preserve volumes)
down-v          # Stop and remove volumes (clean slate)
restart         # Restart services
logs            # Follow all logs
logs-api        # Follow API logs
logs-web        # Follow Web logs

# Database
migrate         # Run alembic upgrade head
migrate-create  # Create new migration (interactive)
shell-db        # PostgreSQL shell

# Testing
test            # All tests (unit + integration + contract)
test-unit       # Unit tests only
test-integration # Integration tests only
test-contract   # Contract tests only
test-e2e        # Playwright E2E (requires running stack)

# Code Quality
lint            # Ruff + ESLint
format          # Ruff format + Prettier
typecheck       # mypy + tsc

# Evaluation
eval            # Run fixture evaluation (Mock)
eval-real       # Run real provider evaluation (requires keys)

# Backup/Restore
backup-db       # pg_dump to backups/
backup-qdrant   # Qdrant snapshot
backup-all      # Both
restore-db      # Restore PostgreSQL
restore-qdrant  # Restore Qdrant

# Utilities
clean           # Remove build artifacts, caches
reindex         # Re-index all documents (prompts for config)
shell-api       # Shell into API container
shell-web       # Shell into Web container
```

---

## IDE Setup Recommendations

### VS Code
- Extensions: Python, Pylance, Ruff, TypeScript, ESLint, Prettier, Docker, GitHub Actions
- Settings: Format on save; Ruff as formatter; Pylance strict mode

### PyCharm / IntelliJ
- Python interpreter: Docker Compose service (API)
- Database tool: Connect to PostgreSQL (127.0.0.1:5432 when port forwarded)
- HTTP Client: Use `.http` files for API testing

---

## Performance Tuning (Local)

| Bottleneck | Tuning |
|------------|--------|
| Slow embedding | Reduce batch size; use smaller model; Mock for dev |
| Slow Qdrant | Increase `hnsw_ef` for accuracy; reduce for speed |
| Slow generation | Reduce `max_tokens`; lower temperature; Mock for dev |
| High memory | Limit parser pages/chars; use streaming upload |
| Slow UI | Check Network tab; enable React DevTools profiler |

---

## Upgrading Dependencies

### Python
```bash
cd services/backend
pip install --upgrade pip
pip-compile --upgrade pyproject.toml  # If using pip-tools
# Or: poetry update / uv lock --upgrade
```

### Node
```bash
cd apps/web
npm update
# Or: npx npm-check-updates -u && npm install
```

### Docker Images
```bash
# Update compose.yaml tags
# Test locally
make down-v && make up
# Run full test suite
make test-ci
```

---

## Developer Onboarding Checklist

- [ ] Clone repository
- [ ] Install Docker Desktop
- [ ] `cp .env.example .env`
- [ ] `make up`
- [ ] Verify Web UI at http://127.0.0.1:3000
- [ ] Verify API docs at http://127.0.0.1:8000/docs
- [ ] Upload fixture document (`data/samples/policy.pdf`)
- [ ] Wait for ingestion → `ready`
- [ ] Ask question → see answer with citations
- [ ] Run evaluation → see metrics
- [ ] Run tests: `make test`
- [ ] Read `docs/00-project-understanding.md`