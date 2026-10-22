# Docker Infrastructure Documentation

**Version:** 1.0  
**Date:** 2026-10-22  
**Status:** Phase 6 deliverable

---

## Dockerfile: API Service

**Location:** `services/backend/Dockerfile`

### Multi-Stage Build

```dockerfile
# =============================================================================
# Base Stage - Common dependencies
# =============================================================================
FROM python:3.11-slim-bookworm AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
WORKDIR /app

# =============================================================================
# Development Stage - With hot reload
# =============================================================================
FROM base AS development

# Install dev dependencies
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy source code
COPY --chown=appuser:appuser . .

USER appuser

# Expose port
EXPOSE 8000

# Default command (overridden by docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# =============================================================================
# Production Stage - Optimized
# =============================================================================
FROM base AS production

# Install only production dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY --chown=appuser:appuser . .

# Run as non-root
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8000/health/ready || exit 1

# Default command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### Build Commands

```bash
# Development (used by docker-compose)
docker build --target development -t ragbench-api:dev ./services/backend

# Production
docker build --target production -t ragbench-api:prod ./services/backend

# With build args
docker build --target production \
  --build-arg PYTHON_VERSION=3.11 \
  -t ragbench-api:prod ./services/backend
```

---

## Dockerfile: Web Service

**Location:** `apps/web/Dockerfile`

### Multi-Stage Build

```dockerfile
# =============================================================================
# Base Stage
# =============================================================================
FROM node:20-alpine AS base

ENV NODE_ENV=development \
    NEXT_TELEMETRY_DISABLED=1

# Install dependencies for native modules
RUN apk add --no-cache libc6-compat

WORKDIR /app

# =============================================================================
# Dependencies Stage
# =============================================================================
FROM base AS deps

COPY package.json package-lock.json* ./
RUN npm ci

# =============================================================================
# Development Stage
# =============================================================================
FROM base AS development

COPY --from=deps /app/node_modules ./node_modules
COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]

# =============================================================================
# Builder Stage (Production)
# =============================================================================
FROM base AS builder

COPY --from=deps /app/node_modules ./node_modules
COPY . .

ENV NODE_ENV=production
RUN npm run build

# =============================================================================
# Production Stage
# =============================================================================
FROM base AS production

ENV NODE_ENV=production

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000

CMD ["node", "server.js"]
```

### Next.js Standalone Output

Add to `next.config.js`:

```javascript
const nextConfig = {
  // ... other config
  output: 'standalone',
};
```

### Build Commands

```bash
# Development (used by docker-compose)
docker build --target development -t ragbench-web:dev ./apps/web

# Production
docker build --target production -t ragbench-web:prod ./apps/web
```

---

## Docker Compose Architecture

### File Structure

```
.
├── compose.yaml              # Main compose file (this repo)
├── docker-compose.override.yml  # Local overrides (gitignored)
├── services/backend/
│   └── Dockerfile
├── apps/web/
│   └── Dockerfile
└── infra/docker/
    ├── Dockerfile.api        # Symlink or copy of services/backend/Dockerfile
    ├── Dockerfile.web        # Symlink or copy of apps/web/Dockerfile
    └── docker-compose.override.yml.example
```

### Service Dependency Graph

```
                    ┌─────────────┐
                    │   postgres  │
                    │  (healthy)  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   qdrant    │
                    │  (healthy)  │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
         ┌─────────┐  ┌─────────┐  ┌─────────┐
         │   api   │  │ worker* │  │  redis* │
         │(healthy)│  │(healthy)│  │(healthy)│
         └────┬────┘  └─────────┘  └─────────┘
              │
              ▼
         ┌─────────┐
         │   web   │
         │(started)│
         └─────────┘

* = profile: with-workers
```

### Health Check Flow

```
docker compose up --wait
    │
    ├── postgres: pg_isready → healthy
    │
    ├── qdrant: wget /healthz → healthy
    │
    ├── redis: redis-cli ping → healthy (if with-workers)
    │
    ├── api: depends_on postgres+qdrant healthy → starts → uvicorn → healthy
    │
    └── web: depends_on api started → starts → next dev → ready
```

---

## Configuration

### Environment Variables

All configurable via `.env` (see `.env.example`):

```bash
# Database
POSTGRES_DB=ragbench
POSTGRES_USER=ragbench
POSTGRES_PASSWORD=changeme  # CHANGE IN PRODUCTION!

# Vector Store
QDRANT_URL=http://qdrant:6333
QDRANT_API_KEY=  # Optional

# Cache/Queue
REDIS_URL=redis://redis:6379/0

# Providers
MOCK_MODE=true
EMBEDDING_PROVIDER=mock
GENERATION_PROVIDER=mock

# Limits
MAX_UPLOAD_SIZE_MB=20
MAX_PDF_PAGES=200
CHUNK_SIZE_CHARS=1200
CHUNK_OVERLAP_CHARS=150
```

### Profiles

| Profile | Services | Use Case |
|---------|----------|----------|
| (default) | postgres, qdrant, api, web | Standard development |
| `with-workers` | +redis, +worker | Background job processing |

```bash
# Default
docker compose up

# With workers
docker compose --profile with-workers up
```

---

## Volumes

### Named Volumes (Persistent)

| Volume | Service | Mount Point | Purpose |
|--------|---------|-------------|---------|
| `ragbench-postgres-data` | postgres | `/var/lib/postgresql/data` | PostgreSQL data |
| `ragbench-qdrant-data` | qdrant | `/qdrant/storage` | Collections, vectors |
| `ragbench-redis-data` | redis | `/data` | AOF/RDB files |

### Volume Management

```bash
# List
docker volume ls | grep ragbench

# Inspect
docker volume inspect ragbench-postgres-data

# Backup (manual)
docker run --rm -v ragbench-postgres-data:/data -v $(pwd):/backup alpine tar czf /backup/pg_data.tar.gz -C /data .

# Restore (manual)
docker run --rm -v ragbench-postgres-data:/data -v $(pwd):/backup alpine tar xzf /backup/pg_data.tar.gz -C /data

# Remove all (DESTRUCTIVE)
docker compose down -v
docker volume prune
```

---

## Networks

### Internal Network

```yaml
networks:
  ragbench-internal:
    driver: bridge
    name: ragbench-internal
```

- All services connected
- No external access
- Service discovery via container names

### Port Bindings

| Service | Container Port | Host Binding | Purpose |
|---------|----------------|--------------|---------|
| api | 8000 | 127.0.0.1:8000 | API + Docs |
| web | 3000 | 127.0.0.1:3000 | Frontend |
| postgres | 5432 | None | Internal only |
| qdrant | 6333/6334 | None | Internal only |
| redis | 6379 | None | Internal only |

---

## Resource Management

### Memory Limits

```yaml
deploy:
  resources:
    limits:
      memory: 1G      # Hard limit
    reservations:
      memory: 256M    # Guaranteed
```

| Service | Limit | Reservation |
|---------|-------|-------------|
| postgres | 512M | 128M |
| qdrant | 1G | 256M |
| redis | 256M | 64M |
| api | 1G | 256M |
| web | 1G | 256M |
| worker | 1G | 256M |

### CPU Limits (Optional)

```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
    reservations:
      cpus: '0.5'
```

---

## Security

### Non-Root Users

Both Dockerfiles create `appuser` (UID 1000) and run as non-root.

### Read-Only Root Filesystem (Production)

```yaml
# In compose.yaml for production profile
services:
  api:
    read_only: true
    tmpfs:
      - /tmp
      - /var/cache
```

### Capability Dropping

```yaml
services:
  api:
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE  # If binding to privileged ports
```

### Secrets (Production)

```yaml
services:
  api:
    secrets:
      - openai_api_key
      - anthropic_api_key

secrets:
  openai_api_key:
    external: true
  anthropic_api_key:
    external: true
```

---

## Development vs Production

### Development (Current)

- Volume mounts for hot reload
- `--reload` / `npm run dev`
- No resource limits
- Debug logging
- All ports on loopback

### Production (Future)

```yaml
# compose.prod.yaml
services:
  api:
    build:
      target: production
    environment:
      - LOG_LEVEL=INFO
      - LOG_FORMAT=json
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 2G
    read_only: true
    cap_drop:
      - ALL

  web:
    build:
      target: production
    environment:
      - NODE_ENV=production
    deploy:
      replicas: 2

  postgres:
    deploy:
      resources:
        limits:
          memory: 2G

  qdrant:
    deploy:
      resources:
        limits:
          memory: 4G
```

---

## Troubleshooting Docker

### Build Issues

```bash
# Clean build (no cache)
docker compose build --no-cache

# Build specific service
docker compose build api

# Build with progress
docker compose build --progress=plain
```

### Container Issues

```bash
# View container logs
docker compose logs -f api

# Execute in container
docker compose exec api bash
docker compose exec postgres psql -U ragbench

# Inspect container
docker inspect ragbench-api

# Resource usage
docker stats
```

### Network Issues

```bash
# Test connectivity between containers
docker compose exec api ping postgres
docker compose exec api wget -qO- http://qdrant:6333/healthz

# DNS resolution
docker compose exec api nslookup postgres
```

### Volume Issues

```bash
# Permission issues
docker compose exec api ls -la /app

# Volume not mounting
docker compose down -v && docker compose up

# Disk space
docker system df
docker system prune -a --volumes
```

---

## Validation Checklist

Before committing compose changes:

- [ ] `docker compose config -q` passes
- [ ] `docker compose up --wait` starts all services healthy
- [ ] `docker compose ps` shows all services running
- [ ] Health endpoints respond: `/health/live`, `/health/ready`
- [ ] Volumes persist after `docker compose down && docker compose up`
- [ ] No sensitive data in image layers (`docker history`)
- [ ] Base images pinned to specific tags (not `latest`)
- [ ] Non-root user in all custom images
- [ ] Resource limits reasonable for target hardware