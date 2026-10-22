# Local Infrastructure Runbook

**Version:** 1.0  
**Date:** 2026-10-22  
**Status:** Phase 6 deliverable

---

## Overview

This runbook covers the local Docker Compose infrastructure for RAGBench development.

### Services

| Service | Image | Ports (Host) | Internal Port | Purpose |
|---------|-------|--------------|---------------|---------|
| `postgres` | `postgres:16-alpine` | None | 5432 | Metadata database |
| `qdrant` | `qdrant/qdrant:1.10.1` | None | 6333/6334 | Vector database |
| `redis` | `redis:7-alpine` | None | 6379 | Job queue (optional) |
| `api` | `ragbench-api:dev` | 127.0.0.1:8000 | 8000 | FastAPI backend |
| `web` | `ragbench-web:dev` | 127.0.0.1:3000 | 3000 | Next.js frontend |
| `worker` | `ragbench-api:dev` | None | N/A | Celery worker (optional) |

### Network Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Host Machine                           │
│  ┌──────────────┐    ┌──────────────┐                       │
│  │  Browser     │    │  Terminal    │                       │
│  │  localhost:3000     │  localhost:8000     │                       │
│  └──────┬───────┘    └──────┬───────┘                       │
└─────────┼────────────────────┼──────────────────────────────┘
          │                    │
    ┌─────▼─────┐        ┌─────▼─────┐
    │   Web     │◀───────│   API     │
    │  :3000    │        │  :8000    │
    └─────┬─────┘        └─────┬─────┘
          │                    │
          ▼                    ▼
    ┌─────────────────────────────────┐
    │     Docker Network              │
    │  (ragbench-internal)            │
    │  ┌────────┐ ┌────────┐ ┌──────┐ │
    │  │Postgres│ │ Qdrant │ │Redis │ │
    │  │  :5432 │ │ :6333  │ │:6379 │ │
    │  └────────┘ └────────┘ └──────┘ │
    └─────────────────────────────────┘
```

---

## Quick Start

### Prerequisites
- Docker Engine 24+ and Docker Compose v2+
- 4+ GB available RAM
- Ports 3000 and 8000 available on localhost

### Start All Services

```bash
# From repository root
cp .env.example .env
make up
# Or: docker compose up --wait
```

### Start Minimal Services (No Worker)

```bash
make up
# Default profile excludes worker
```

### Start With Worker (Background Jobs)

```bash
docker compose --profile with-workers up --wait
# Or:
make infra-up
docker compose --profile with-workers up -d worker
```

---

## Service Details

### PostgreSQL (`postgres`)

**Configuration:**
- Image: `postgres:16-alpine`
- Database: `ragbench` (from `POSTGRES_DB`)
- User: `ragbench` (from `POSTGRES_USER`)
- Password: from `POSTGRES_PASSWORD` (required in `.env`)
- Volume: `postgres_data` → `/var/lib/postgresql/data`

**Healthcheck:**
```bash
pg_isready -U ragbench -d ragbench
```
- Interval: 5s
- Timeout: 5s
- Retries: 10
- Start period: 10s

**Connection (from API):**
```
postgresql+asyncpg://ragbench:changeme@postgres:5432/ragbench
```

**No public port exposure** — only accessible on internal Docker network.

### Qdrant (`qdrant`)

**Configuration:**
- Image: `qdrant/qdrant:1.10.1`
- Volume: `qdrant_data` → `/qdrant/storage`
- API: HTTP on 6333, gRPC on 6334

**Healthcheck:**
```bash
wget --spider http://localhost:6333/healthz
```
- Interval: 5s
- Timeout: 5s
- Retries: 10
- Start period: 10s

**Connection (from API):**
```
http://qdrant:6333
```

**No public port exposure** — only accessible on internal Docker network.

### Redis (`redis`) — Optional

**Configuration:**
- Image: `redis:7-alpine`
- Command: `redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru`
- Volume: `redis_data` → `/data`
- Profile: `with-workers` (only starts when explicitly requested)

**Healthcheck:**
```bash
redis-cli ping
```
- Interval: 5s
- Timeout: 3s
- Retries: 10
- Start period: 5s

**No public port exposure** — only accessible on internal Docker network.

### API (`api`)

**Build:**
- Context: `./services/backend`
- Dockerfile: `Dockerfile`
- Target: `development`

**Ports:**
- `127.0.0.1:8000:8000` (loopback only)

**Dependencies:**
- Waits for `postgres` and `qdrant` to be `healthy`
- Does NOT wait for `redis` (optional)

**Volumes:**
- `./services/backend:/app` (hot reload)
- `/app/__pycache__` (excluded from host)

### Web (`web`)

**Build:**
- Context: `./apps/web`
- Dockerfile: `Dockerfile`
- Target: `development`

**Ports:**
- `127.0.0.1:3000:3000` (loopback only)

**Dependencies:**
- Waits for `api` to be `started`

**Volumes:**
- `./apps/web:/app` (hot reload)
- `/app/node_modules` (excluded from host)
- `/app/.next` (excluded from host)

### Worker (`worker`) — Optional

**Profile:** `with-workers`

**Command:**
```bash
celery -A app.workers worker -l info --concurrency=2
```

**Dependencies:**
- Waits for `postgres`, `qdrant`, `redis` to be `healthy`

---

## Environment Variables

### Required (in `.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_PASSWORD` | **required** | PostgreSQL password |
| `MOCK_MODE` | `true` | Force Mock providers |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_DB` | `ragbench` | Database name |
| `POSTGRES_USER` | `ragbench` | Database user |
| `QDRANT_API_KEY` | (empty) | Qdrant auth (if enabled) |
| `EMBEDDING_PROVIDER` | `mock` | `mock\|ollama\|openai\|cohere` |
| `GENERATION_PROVIDER` | `mock` | `mock\|ollama\|openai\|anthropic` |
| `OLLAMA_EMBEDDING_URL` | `http://host.docker.internal:11434` | Local Ollama |
| `OLLAMA_GENERATION_URL` | `http://host.docker.internal:11434` | Local Ollama |
| `OPENAI_API_KEY` | (empty) | Required if provider=openai |
| `ANTHROPIC_API_KEY` | (empty) | Required if provider=anthropic |

---

## Commands

### Start/Stop

```bash
# Start all (default profile)
make up

# Start with worker
docker compose --profile with-workers up --wait

# Stop (keep volumes)
make down

# Stop and remove volumes (CLEAN SLATE)
make down-v

# Restart
make restart
```

### Logs

```bash
make logs           # All services
make logs-api       # API only
make logs-web       # Web only
make logs-db        # PostgreSQL only
make logs-qdrant    # Qdrant only
```

### Database

```bash
make migrate              # Run migrations
make migrate-create       # Create new migration
make shell-db             # psql shell
```

### Health Checks

```bash
# Check service status
docker compose ps

# Manual health checks
curl http://127.0.0.1:8000/health/ready
curl http://127.0.0.1:8000/health/live
curl http://127.0.0.1:3000
```

---

## Persistence

### Volumes

| Volume | Mount Point | Contents |
|--------|-------------|----------|
| `postgres_data` | `/var/lib/postgresql/data` | PostgreSQL data files |
| `qdrant_data` | `/qdrant/storage` | Qdrant collections, vectors, snapshots |
| `redis_data` | `/data` | Redis AOF/RDB files |

### Survival

- `make down` → **volumes preserved** → data survives
- `make down-v` → **volumes removed** → clean slate
- `docker compose down -v` → same as `make down-v`

### Backup

```bash
# PostgreSQL
make backup-db
# Output: backups/pg_YYYY-MM-DD_HHMMSS.sql

# Qdrant
make backup-qdrant
# Creates Qdrant snapshot via API

# Both
make backup-all
```

### Restore

```bash
# PostgreSQL
make restore-db FILE=backups/pg_2026-10-22_120000.sql

# Qdrant
make restore-qdrant SNAPSHOT=snapshot_name
```

---

## Troubleshooting

### Services Won't Start

```bash
# Check status
docker compose ps

# Check logs
make logs

# Common issues:
# 1. Port conflicts on 3000/8000
lsof -ti:3000,8000 | xargs kill

# 2. Docker resources insufficient
# Increase Docker Desktop memory to 4GB+

# 3. Volume permissions
docker compose down -v && make up
```

### Health Check Failures

```bash
# Check specific service logs
docker compose logs postgres
docker compose logs qdrant

# Manual health check
docker compose exec postgres pg_isready -U ragbench -d ragbench
docker compose exec qdrant wget --spider http://localhost:6333/healthz
```

### Database Connection Issues

```bash
# Verify PostgreSQL is accepting connections
make shell-db
# Inside container: \l, \dt

# Check connection string
docker compose exec api env | grep DATABASE_URL
```

### Qdrant Connection Issues

```bash
# Verify Qdrant API
curl http://127.0.0.1:6333/healthz  # Won't work (not published)
docker compose exec qdrant wget --spider http://localhost:6333/healthz

# Check collections
docker compose exec qdrant curl http://localhost:6333/collections
```

### Volume Issues

```bash
# List volumes
docker volume ls | grep ragbench

# Inspect volume
docker volume inspect ragbench-postgres-data

# Remove all volumes (DESTRUCTIVE)
docker compose down -v
docker volume prune
```

---

## Resource Limits

| Service | Memory Limit | Memory Reservation | CPU |
|---------|--------------|-------------------|-----|
| postgres | 512M | 128M | Default |
| qdrant | 1G | 256M | Default |
| redis | 256M | 64M | Default |
| api | 1G | 256M | Default |
| web | 1G | 256M | Default |
| worker | 1G | 256M | Default |

**Adjust in `compose.yaml` if needed.**

---

## Security

### Network Isolation
- All services on internal `ragbench-internal` bridge network
- **No database/vector store ports published** to host
- Only `api` (8000) and `web` (3000) bound to `127.0.0.1`

### Secrets
- **Never** commit `.env` to Git
- `.env.example` contains placeholders only
- Secrets loaded from `.env` (gitignored)
- CI uses GitHub Secrets

### Ollama (Optional)
- Runs **natively on host macOS** (not in Docker)
- Accessible via `host.docker.internal:11434`
- Not managed by Docker Compose

---

## Validation

```bash
# Validate compose syntax
make compose-validate

# Validate full configuration
make validate

# Expected output:
# docker compose config valid
# Checking .env.example exists... OK
# Checking Python syntax... OK
# Checking TypeScript... OK
# All validations passed
```

---

## Cleanup

```bash
# Stop and remove containers (keep volumes)
make down

# Stop and remove everything (CLEAN SLATE)
make down-v

# Remove build cache
make clean

# Remove all Docker resources (nuclear option)
docker system prune -a --volumes
```