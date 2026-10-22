# RAGBench — Development Workflow

**Version:** 1.0  
**Date:** 2026-10-22  
**Status:** Phase 5 deliverable

---

## Quick Start

### Prerequisites

- Docker Engine 24+ and Docker Compose v2+
- Git
- 4+ GB RAM available
- (Optional) Python 3.11+, Node.js 20+ for native development

### One-Command Setup

```bash
git clone <repo-url> ragbench
cd ragbench
cp .env.example .env
make up
```

**Access:**
- Web UI: http://127.0.0.1:3000
- API Docs: http://127.0.0.1:8000/docs
- API Health: http://127.0.0.1:8000/health/ready

---

## Development Modes

### Mode 1: Full Docker (Recommended)

All services in containers with hot-reload via volume mounts.

```bash
make up           # Start all services
make logs         # Follow all logs
make logs-api     # API logs only
make down         # Stop (keep volumes)
make down-v       # Stop and remove volumes (clean slate)
make restart      # Restart services
```

**Services:**
- `postgres` — Metadata database (port 5432, internal only)
- `qdrant` — Vector database (port 6333, internal only)
- `redis` — Job queue (optional, profile `with-workers`)
- `api` — FastAPI backend (port 8000, loopback)
- `web` — Next.js frontend (port 3000, loopback)
- `worker` — Celery worker (optional, profile `with-workers`)

### Mode 2: Hybrid (Native Backend + Docker Infra)

Run API locally for faster iteration; infra in Docker.

```bash
# Terminal 1: Start infra only
make infra-up

# Terminal 2: Run API locally
cd services/backend
cp ../.env.example .env
# Edit .env: DATABASE_URL=postgresql+asyncpg://ragbench:changeme@localhost:5432/ragbench
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Mode 3: Hybrid (Native Frontend + Docker Infra + API)

```bash
# Terminal 1: Start infra + API
make infra-up
make api-up

# Terminal 2: Run Web locally
cd apps/web
npm install
cp ../.env.example .env.local
# Edit .env.local: NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
npm run dev
```

### Mode 4: Full Native (Advanced)

All services native; no Docker. Requires manual PostgreSQL/Qdrant/Redis setup.

---

## Daily Workflow

### 1. Start Development

```bash
make up
# Wait for "healthy" status on all services
```

### 2. Make Changes

- **Backend:** Edit files in `services/backend/app/` — auto-reloads via `uvicorn --reload`
- **Frontend:** Edit files in `apps/web/` — auto-reloads via `next dev`
- **Database:** Create migration → `make migrate-create` → `make migrate`

### 3. Run Tests

```bash
# All tests
make test

# Specific layers
make test-unit           # Fast, no external deps
make test-integration    # Requires running PostgreSQL + Qdrant
make test-contract       # Provider interface contracts
make test-e2e            # Playwright (requires running stack)
```

### 4. Code Quality

```bash
make lint        # Ruff + ESLint
make format      # Auto-fix formatting
make typecheck   # mypy + tsc
```

### 4. Commit

```bash
git add -A
git commit -m "type(scope): description"
# Follow Conventional Commits: feat, fix, docs, refactor, test, chore
```

---

## Makefile Targets Reference

### Infrastructure

| Target | Description |
|--------|-------------|
| `up` | Start all services with health checks |
| `down` | Stop services (preserve volumes) |
| `down-v` | Stop and remove volumes (clean slate) |
| `restart` | Restart all services |
| `logs` | Follow all service logs |
| `logs-api` | Follow API logs |
| `logs-web` | Follow Web logs |
| `logs-db` | Follow PostgreSQL logs |
| `logs-qdrant` | Follow Qdrant logs |

### Database

| Target | Description |
|--------|-------------|
| `migrate` | Run `alembic upgrade head` |
| `migrate-create` | Create new migration (prompts for message) |
| `shell-db` | PostgreSQL `psql` shell |
| `shell-qdrant` | Qdrant shell (curl aliases) |
| `shell-api` | Shell into API container |
| `shell-web` | Shell into Web container |

### Testing

| Target | Description |
|--------|-------------|
| `test` | All tests (unit + integration + contract) |
| `test-unit` | Unit tests only |
| `test-integration` | Integration tests (requires PG + Qdrant) |
| `test-contract` | Contract tests |
| `test-e2e` | Playwright E2E tests |
| `test-all` | All tests including E2E |

### Code Quality

| Target | Description |
|--------|-------------|
| `lint` | Ruff (Python) + ESLint (Frontend) |
| `format` | Ruff format + Prettier |
| `typecheck` | mypy (strict) + tsc --noEmit |

### Evaluation & Benchmarking

| Target | Description |
|--------|-------------|
| `eval` | Run fixture evaluation (Mock providers) |
| `eval-real` | Run real provider evaluation (requires API keys) |
| `benchmark` | All benchmarks |
| `bench-ingestion` | Ingestion throughput |
| `bench-retrieval` | Query latency |
| `bench-generation` | Generation latency |
| `bench-eval` | Evaluation pipeline |

### Backup & Restore

| Target | Description |
|--------|-------------|
| `backup-db` | `pg_dump` to `backups/` |
| `backup-qdrant` | Qdrant snapshot |
| `backup-all` | Both database and Qdrant |
| `restore-db` | Restore PostgreSQL (`FILE=path`) |
| `restore-qdrant` | Restore Qdrant (`SNAPSHOT=name`) |

### Utilities

| Target | Description |
|--------|-------------|
| `clean` | Remove build artifacts, caches |
| `reindex` | Re-index all documents (interactive) |
| `validate` | Validate compose, configs, migrations |
| `compose-validate` | `docker compose config -q` |
| `secret-scan` | TruffleHog scan |
| `ci` | Full CI pipeline locally |

---

## Git Workflow

### Branch Strategy

- **Main branch:** `main` (protected, no direct pushes)
- **Feature branches:** Not required for solo; use for collaboration
- **Commit directly to main** for solo development (with CI checks)

### Commit Convention

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:** `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `security`

**Examples:**
```
feat(ingestion): add PDF page metadata extraction
fix(retrieval): handle empty corpus gracefully
docs(api): update OpenAPI examples
refactor(chunking): extract base Chunker protocol
test(metrics): add nDCG edge case tests
chore(deps): upgrade fastapi to 0.110.1
```

### Pre-commit Hooks (Optional)

```bash
# Install
pre-commit install

# Run manually
pre-commit run --all-files
```

**Configured hooks:**
- `ruff` (lint + format)
- `mypy` (type check)
- `prettier` (frontend format)
- `trufflehog` (secret scan)
- `check-yaml`, `check-json`, `check-toml`
- `end-of-file-fixer`, `trailing-whitespace`

---

## Environment Configuration

### `.env` File (Local, Gitignored)

```bash
# Copy from .env.example and customize
cp .env.example .env
```

### Key Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MOCK_MODE` | `true` | Force Mock providers |
| `DATABASE_URL` | `postgresql+asyncpg://...` | PostgreSQL connection |
| `QDRANT_URL` | `http://qdrant:6333` | Qdrant endpoint |
| `EMBEDDING_PROVIDER` | `mock` | `mock\|ollama\|openai\|cohere` |
| `GENERATION_PROVIDER` | `mock` | `mock\|ollama\|openai\|anthropic` |
| `OLLAMA_EMBEDDING_URL` | `http://host.docker.internal:11434` | Local Ollama |
| `OLLAMA_GENERATION_URL` | `http://host.docker.internal:11434` | Local Ollama |
| `OPENAI_API_KEY` | (empty) | Required for OpenAI |
| `ANTHROPIC_API_KEY` | (empty) | Required for Anthropic |

### Per-Service Override

Create `docker-compose.override.yml` (gitignored) for local customizations:

```yaml
services:
  api:
    environment:
      - LOG_LEVEL=DEBUG
    ports:
      - "8000:8000"  # Expose on all interfaces

  web:
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Testing Strategy

### Test Pyramid

```
                    E2E (Playwright)          ← 5-10 tests, slow
               ┌────────────────────────────┐
               │  Integration (pytest)       │  ← 20-50 tests, moderate
         ┌─────┴────────────────────────────┴─────┐
         │         Unit (pytest)                   │  ← 100+ tests, fast
         └─────────────────────────────────────────┘
```

### Running Specific Tests

```bash
# Backend
cd services/backend
pytest tests/unit/test_chunking.py::test_overlap -v
pytest tests/integration -k "pdf" -v
pytest tests/contract/test_embedding_provider.py -v

# Frontend
cd apps/web
npm run test -- --run src/features/chat/Chat.test.tsx
npx playwright test tests/e2e/chat.spec.ts
```

### Test Markers (pytest)

```bash
pytest -m unit           # Unit tests only
pytest -m integration    # Integration tests only
pytest -m contract       # Contract tests only
pytest -m security       # Security regression tests
pytest -m "not slow"     # Skip slow tests
```

---

## Debugging

### Common Issues

| Symptom | Cause | Resolution |
|---------|-------|------------|
| `connection refused` to PG/Qdrant | Services not healthy | `make logs` → check health; `make restart` |
| `dimension mismatch` | Embedding model changed | Re-index: `make reindex` or delete + re-ingest |
| `CUDA out of memory` | Local model too large | Use smaller model; quantize; CPU only |
| `port already in use` | Another process on 3000/8000 | `lsof -ti:3000,8000 \| xargs kill` |
| Frontend shows "Mock Provider" | `MOCK_MODE=true` | Expected for demo; change `.env` for real |
| Migration fails | Schema conflict | Check `alembic history`; manual fix if needed |

### Debug Commands

```bash
# API logs
make logs-api

# Database shell
make shell-db

# Qdrant shell
make shell-qdrant

# Run single test
cd services/backend && pytest tests/unit/test_chunking.py::test_overlap -v

# Inspect OpenAPI
curl http://127.0.0.1:8000/openapi.json | jq .

# Check database
docker compose exec postgres psql -U ragbench -d ragbench -c "SELECT * FROM documents;"
```

### Profiling

```bash
# Python CPU profiling
cd services/backend
python -m cProfile -o profile.stats -m pytest tests/unit/test_chunking.py
python -m pstats profile.stats

# Python memory profiling
pip install memray
memray run -m pytest tests/unit/test_chunking.py
memray flamegraph profile.bin

# Node.js profiling
cd apps/web
npm run build
NODE_OPTIONS="--inspect" npm run start
# Chrome DevTools → Memory/Performance
```

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

## CI/CD Integration

### Local CI Simulation

```bash
make ci
# Runs: lint → typecheck → test → validate → secret-scan
```

### GitHub Actions Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `ci.yml` | Push, PR | Lint, typecheck, unit, integration, contract, Docker validate, secret scan |
| `ci-e2e.yml` | Manual, schedule | Playwright E2E |
| `ci-eval.yml` | Manual | Real provider evaluation |
| `dependency-review.yml` | PR | License/vulnerability review |

### Required Secrets (GitHub)

| Secret | Purpose |
|--------|---------|
| `OPENAI_API_KEY` | Real provider eval |
| `ANTHROPIC_API_KEY` | Real provider eval |

---

## Troubleshooting Checklist

### Before Reporting Issues

- [ ] `make down-v && make up` (clean restart)
- [ ] `make validate` (config validation)
- [ ] `make test-unit` (unit tests pass)
- [ ] Check `make logs` for error messages
- [ ] Verify `.env` matches `.env.example`
- [ ] Check Docker resources (RAM, disk)

### Getting Help

1. Check `docs/14-deployment-and-development.md` → Troubleshooting
2. Check `make logs-api` for backend errors
3. Check `make logs-web` for frontend errors
4. Search existing GitHub Issues
5. Create new Issue with: `make logs` output, `make validate` output, steps to reproduce

---

## Useful Aliases (Add to `.bashrc`/`.zshrc`)

```bash
# RAGBench shortcuts
alias rb-up='make up'
alias rb-down='make down'
alias rb-logs='make logs'
alias rb-test='make test'
alias rb-lint='make lint'
alias rb-shell-db='make shell-db'
alias rb-migrate='make migrate'
alias rb-eval='make eval'
```