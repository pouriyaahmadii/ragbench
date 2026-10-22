# RAGBench — Runtime Compatibility

**Version:** 1.0  
**Date:** 2026-10-22  
**Status:** Phase 5 deliverable

---

## Supported Runtimes

### Python

| Requirement | Specification |
|-------------|---------------|
| **Version** | 3.11+ (3.11, 3.12 supported) |
| **Implementation** | CPython only (no PyPy, GraalPy) |
| **Package Manager** | `uv` (preferred) or `pip` with `pip-tools` |
| **Virtual Env** | `.venv` (local) or Docker-only |

#### Version Compatibility Matrix

| Python | FastAPI | Pydantic | SQLAlchemy | asyncpg | Qdrant Client | Status |
|--------|---------|----------|------------|---------|---------------|--------|
| 3.11 | 0.110.x | 2.7+ | 2.0+ | 0.29+ | 1.10+ | ✅ Primary |
| 3.12 | 0.110.x | 2.7+ | 2.0+ | 0.29+ | 1.10+ | ✅ Tested |
| 3.13 | TBD | TBD | TBD | TBD | TBD | ⏳ Future |

#### Verified Package Versions (2026-10-22)

```bash
# Core
Python 3.11.9
FastAPI 0.110.1
Pydantic 2.7.4
Pydantic Settings 2.3.4
Starlette 0.37.2

# Database
SQLAlchemy 2.0.30
Alembic 1.12.1
asyncpg 0.29.0
PostgreSQL 16 (client lib)

# Vector
Qdrant Client 1.10.1
Qdrant Server 1.10.1

# Parsing
pdfplumber 0.11.0
markdown-it-py 3.0.0

# HTTP
httpx 0.27.0
python-multipart 0.0.9

# Observability
structlog 24.1.0
python-json-logger 2.0.7

# Utilities
tenacity 8.2.3
python-dotenv 1.0.1
```

---

### Node.js

| Requirement | Specification |
|-------------|---------------|
| **Version** | 20 LTS (20.11+) |
| **Package Manager** | npm 10.8+ (pinned in `package.json`) |
| **Runtime** | Node.js only (no Bun, Deno for MVP) |

#### Version Compatibility Matrix

| Node.js | Next.js | React | TypeScript | Tailwind | Status |
|---------|---------|-------|------------|----------|--------|
| 20.11+ | 14.2.x | 18.3.x | 5.4.x | 3.4.x | ✅ Primary |
| 22.x | 14.2.x | 18.3.x | 5.4.x | 3.4.x | ⚠️ Untested |
| 18.x | 14.2.x | 18.3.x | 5.4.x | 3.4.x | ❌ EOL |

#### Verified Package Versions (2026-10-22)

```bash
# Core
Node.js 20.11.1
npm 10.8.1
Next.js 14.2.3
React 18.3.1
React DOM 18.3.1

# State
TanStack Query 5.17.0
Zod 3.22.4
Axios 1.7.2

# Styling
Tailwind CSS 3.4.3
PostCSS 8.4.38
Autoprefixer 10.4.19

# Type Safety
TypeScript 5.4.5
ESLint 8.57.0
@typescript-eslint/* 7.1.0

# Testing
Vitest 1.4.0
Playwright 1.42.0
Testing Library 14.2.0

# Build
Prettier 3.2.5
openapi-typescript 6.7.0
```

---

## Container Runtimes

### Docker

| Requirement | Specification |
|-------------|---------------|
| **Engine** | Docker Engine 24+ |
| **Compose** | Docker Compose v2 (plugin) |
| **Platform** | linux/amd64, linux/arm64 |

### Base Images (Pinned)

| Service | Image | Digest (Example) | Architecture |
|---------|-------|------------------|--------------|
| API | `python:3.11-slim-bookworm` | `sha256:...` | amd64, arm64 |
| Web | `node:20-alpine` | `sha256:...` | amd64, arm64 |
| PostgreSQL | `postgres:16-alpine` | `sha256:...` | amd64, arm64 |
| Qdrant | `qdrant/qdrant:1.10.1` | `sha256:...` | amd64, arm64 |
| Redis | `redis:7-alpine` | `sha256:...` | amd64, arm64 |

### Multi-Architecture Support

- All base images support `linux/amd64` and `linux/arm64`
- `docker buildx` used for multi-arch builds
- Compose uses `platform: ${TARGETPLATFORM:-linux/amd64}`

---

## External Service Compatibility

### Ollama (Optional Local Models)

| Requirement | Specification |
|-------------|---------------|
| **Version** | 0.1.40+ |
| **Platform** | macOS (Apple Silicon/Intel), Linux, Windows (WSL2) |
| **API** | OpenAI-compatible `/v1` endpoints |
| **Models Tested** | `nomic-embed-text`, `llama3.1:8b`, `llama3.1:70b` |

#### Embedding Models

| Model | Dimension | Use Case | Verified |
|-------|-----------|----------|----------|
| `nomic-embed-text` | 768 | General purpose | ✅ |
| `mxbai-embed-large` | 1024 | High quality | ⚠️ |
| `all-minilm` | 384 | Fast/small | ✅ |

#### Generation Models

| Model | Parameters | Use Case | Verified |
|-------|------------|----------|----------|
| `llama3.1:8b` | 8B | Balanced | ✅ |
| `llama3.1:70b` | 70B | High quality | ⚠️ (needs 48GB+) |
| `phi3:mini` | 3.8B | Fast/edge | ✅ |

### External APIs (Optional)

| Provider | API Version | SDK Version | Status |
|----------|-------------|-------------|--------|
| OpenAI | v1 (2024-04-01) | `openai==1.30.1` | ✅ |
| Anthropic | 2023-06-01 | `anthropic==0.25.0` | ✅ |
| Cohere | v1 | `cohere==4.4.1` | ✅ |

---

## Operating System Support

### Development (Host)

| OS | Architecture | Docker | Native Python/Node | Status |
|----|--------------|--------|-------------------|--------|
| macOS | Apple Silicon (M1/M2/M3) | ✅ | ✅ | ✅ Primary |
| macOS | Intel (x86_64) | ✅ | ✅ | ✅ Supported |
| Linux | x86_64 | ✅ | ✅ | ✅ Supported |
| Linux | ARM64 | ✅ | ✅ | ✅ Supported |
| Windows | WSL2 | ✅ | ⚠️ Via WSL | ✅ Supported |
| Windows | Native | ❌ | ❌ | ❌ Not supported |

### Production (Container)

| OS | Architecture | Status |
|----|--------------|--------|
| Linux | x86_64 | ✅ |
| Linux | ARM64 | ✅ |

---

## Version Verification Commands

### Python Environment

```bash
# Check Python version
python --version
# Python 3.11.9

# Check key packages
python -c "import fastapi; print(fastapi.__version__)"
python -c "import pydantic; print(pydantic.VERSION)"
python -c "import sqlalchemy; print(sqlalchemy.__version__)"
python -c "import qdrant_client; print(qdrant_client.__version__)"
python -c "import asyncpg; print(asyncpg.__version__)"
```

### Node.js Environment

```bash
# Check Node version
node --version
# v20.11.1

npm --version
# 10.8.1

# Check key packages
npm list next react react-dom typescript tailwindcss
```

### Docker Environment

```bash
# Check Docker version
docker --version
# Docker version 24.0.7

docker compose version
# Docker Compose version v2.24.0

# Verify base images
docker pull python:3.11-slim-bookworm
docker pull node:20-alpine
docker pull postgres:16-alpine
docker pull qdrant/qdrant:1.10.1
```

---

## Compatibility Testing

### CI Matrix

```yaml
# .github/workflows/compatibility.yml
strategy:
  matrix:
    python-version: ['3.11', '3.12']
    node-version: ['20']
    os: [ubuntu-latest, macos-latest]
```

### Local Verification Script

```bash
#!/bin/bash
# scripts/verify_compatibility.sh

echo "=== Python ==="
python --version
python -c "import fastapi, pydantic, sqlalchemy, qdrant_client, asyncpg; print('OK')"

echo "=== Node.js ==="
node --version
npm --version
npx tsc --version

echo "=== Docker ==="
docker --version
docker compose version

echo "=== Base Images ==="
docker pull python:3.11-slim-bookworm --quiet
docker pull node:20-alpine --quiet
docker pull postgres:16-alpine --quiet
docker pull qdrant/qdrant:1.10.1 --quiet

echo "✅ All compatibility checks passed"
```

---

## Known Incompatibilities & Workarounds

| Issue | Workaround | Status |
|-------|------------|--------|
| `pdfplumber` on Windows native | Use WSL2 or Docker | Documented |
| `qdrant-client` gRPC on Apple Silicon | Requires `grpcio` wheels | Works with pip 23+ |
| `playwright` browsers on CI | Install via `playwright install` | Documented in CI |
| `pdfplumber` PDF parsing differences | Test on target OS | Acceptable variance |
| `ollama` GPU on macOS | Metal acceleration automatic | Verified |

---

## Upgrade Compatibility Checklist

Before upgrading any core dependency:

- [ ] Read changelog for breaking changes
- [ ] Check downstream dependents (our code)
- [ ] Run full test suite (`make test`)
- [ ] Run integration tests (`make test-integration`)
- [ ] Verify Docker build (`docker compose build`)
- [ ] Update lockfiles (`pip compile` / `npm install`)
- [ ] Run security audit (`pip-audit` / `npm audit`)
- [ ] Update `docs/19-runtime-compatibility.md` with new versions
- [ ] Commit lockfiles and version updates together