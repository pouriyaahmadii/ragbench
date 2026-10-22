# Infra — Infrastructure Configuration

This directory contains infrastructure-as-code configurations for databases, monitoring, and Docker.

## Structure

```
infra/
├── docker/                   # Docker-related configs
│   ├── Dockerfile.api        # Backend API multi-stage build
│   ├── Dockerfile.web        # Frontend Web multi-stage build
│   ├── .dockerignore         # Docker build context exclusions
│   └── docker-compose.override.yml.example  # Example overrides for local dev
├── postgres/                 # PostgreSQL configuration
│   ├── postgresql.conf       # Custom PostgreSQL settings (if needed)
│   ├── pg_hba.conf           # Authentication config (if needed)
│   └── init/                 # Initialization scripts (run on first startup)
│       └── 01-extensions.sql # Enable required extensions (uuid-ossp, pg_trgm)
└── monitoring/               # Observability stack (Phase 19+)
    ├── prometheus.yml        # Prometheus scrape config
    ├── grafana/              # Grafana dashboards and datasources
    │   ├── dashboards/
    │   └── datasources/
    └── alerting/             # Alert rules (if configured)
```

## PostgreSQL Extensions

The following extensions are enabled for RAGBench:

```sql
-- UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Trigram similarity (for future text search)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Vector operations (if using pgvector as alternative)
-- CREATE EXTENSION IF NOT EXISTS vector;
```

## Docker Compose Override

For local development customizations, create `docker-compose.override.yml` (gitignored):

```yaml
services:
  api:
    environment:
      - LOG_LEVEL=DEBUG
    ports:
      - "8000:8000"  # Expose on all interfaces if needed

  web:
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Monitoring (Future / Phase 19)

When enabled, the monitoring stack provides:
- **Prometheus:** Metrics collection from API (`/metrics` endpoint)
- **Grafana:** Dashboards for latency, throughput, error rates, queue depths
- **Alerting:** Rules for high error rate, latency degradation, disk space

## Usage

Most infrastructure is defined in the root `compose.yaml`. This directory contains supporting configuration files that are mounted or referenced by the compose services.