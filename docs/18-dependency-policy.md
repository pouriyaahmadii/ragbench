# RAGBench — Dependency Policy

**Version:** 1.0  
**Date:** 2026-10-22  
**Status:** Phase 5 deliverable

---

## Philosophy

> **Minimal, pinned, auditable, and purposeful.**

Every dependency must earn its place. We prefer standard library solutions, then well-maintained libraries with clear licenses, over custom implementations or trendy frameworks.

---

## Python Dependency Management

### Tooling

| Tool | Purpose | Version |
|------|---------|---------|
| `uv` (preferred) / `pip-tools` | Lockfile generation | Latest stable |
| `pip` | Installation | Bundled with Python |
| `pip-audit` | Vulnerability scanning | 2.6.1 |
| `pip-licenses` | License compliance | Latest |

### Lockfile Strategy

1. **Source of truth:** `pyproject.toml` with version constraints (e.g., `==0.110.1`)
2. **Lockfile:** `requirements.txt` (production) + `requirements-dev.txt` (dev)
3. **Generation:** `pip compile pyproject.toml --output-file requirements.txt`
4. **Verification:** `pip install --require-hashes -r requirements.txt`
5. **CI:** Both lockfiles committed; `pip-audit` runs on every PR

### Version Pinning Rules

| Dependency Type | Pinning Strategy | Example |
|-----------------|------------------|---------|
| Core framework (FastAPI, Pydantic, SQLAlchemy) | Exact patch (`==x.y.z`) | `fastapi==0.110.1` |
| Security-sensitive (cryptography, auth) | Exact patch | `python-jose==3.3.0` |
| Transitive dependencies | Pinned via lockfile | In `requirements.txt` |
| Development tools | Exact patch | `ruff==0.4.4` |
| Optional providers | Exact patch (when enabled) | `ollama==0.2.0` |

### Upgrade Policy

| Category | Frequency | Process |
|----------|-----------|---------|
| Security patches | Within 24h of CVE | Auto-PR via Dependabot; auto-merge if tests pass |
| Patch versions | Weekly | Batched PR; full test suite |
| Minor versions | Monthly | Separate PR; review changelog; test integration |
| Major versions | Quarterly | ADR required; migration plan; staged rollout |

### Prohibited Patterns

- ❌ No floating versions (`>=`, `~=`, `*`) in `pyproject.toml`
- ❌ No `latest` or unpinned Git dependencies
- ❌ No direct GitHub tarball URLs without commit hash
- ❌ No `setup.py` / `setup.cfg` — only `pyproject.toml`

---

## Node.js Dependency Management

### Tooling

| Tool | Purpose | Version |
|------|---------|---------|
| `npm` | Package manager | 10.8.1 (pinned in `package.json`) |
| `npm ci` | CI installation | Uses `package-lock.json` |
| `npm audit` | Vulnerability scanning | Built-in |
| `license-checker` | License compliance | CI only |

### Lockfile Strategy

1. **Source of truth:** `package.json` with exact versions
2. **Lockfile:** `package-lock.json` (committed)
3. **Installation:** `npm ci` in CI; `npm install` locally
4. **Verification:** `npm audit` on every PR; `license-checker` in CI

### Version Pinning Rules

| Dependency Type | Pinning Strategy | Example |
|-----------------|------------------|---------|
| Core framework (Next.js, React) | Exact patch (`x.y.z`) | `next: 14.2.3` |
| UI libraries | Exact patch | `lucide-react: 0.400.0` |
| Build tools (TypeScript, ESLint) | Exact patch | `typescript: 5.4.5` |
| Test tools | Exact patch | `vitest: 1.4.0` |

### Upgrade Policy

Same as Python, adapted for npm ecosystem.

---

## Dependency Selection Criteria

### Required for Every New Dependency

1. **Clear justification:** What problem does it solve that stdlib/existing deps cannot?
2. **License check:** Must be in allowed list (see below)
3. **Maintenance status:** Active (commit within 6 months, releases within 12 months)
4. **Popularity signal:** >1k stars OR used by major projects
5. **Bundle size impact:** <50KB gzipped for frontend (unless critical)
5. **Alternatives evaluated:** Document 2+ alternatives considered
6. **ADR if architectural:** New provider, framework, or data layer

### Allowed Licenses

| License Family | Examples | Status |
|----------------|----------|--------|
| MIT | MIT, BSD-2, BSD-3, ISC | ✅ Preferred |
| Apache-2.0 | Apache-2.0 | ✅ Preferred (patent grant) |
| Public Domain | CC0, Unlicense | ✅ |
| MPL-2.0 | MPL-2.0 | ⚠️ File-level copyleft; review needed |

### Prohibited Licenses

| License | Reason |
|---------|--------|
| GPL-2.0 / GPL-3.0 | Viral copyleft; incompatible with proprietary use |
| AGPL-3.0 | Network copyleft; SaaS risk |
| LGPL-2.1 / LGPL-3.0 | Dynamic linking only; legal review required |
| Custom / Proprietary | Explicit legal approval required |
| No license | Unclear rights; cannot use |

---

## License Compliance Automation

### CI Checks

```yaml
# Python
- pip-licenses --format=json --with-urls > python-licenses.json
- python scripts/check_licenses.py python-licenses.json

# Node.js
- license-checker --json --out node-licenses.json
- python scripts/check_licenses.py node-licenses.json
```

### `scripts/check_licenses.py` Logic

```python
ALLOWED = {"MIT", "BSD-2-Clause", "BSD-3-Clause", "Apache-2.0", "ISC", "CC0-1.0", "Unlicense", "Python-2.0"}
REVIEW_REQUIRED = {"MPL-2.0"}
BLOCKED = {"GPL-2.0", "GPL-3.0", "AGPL-3.0", "LGPL-2.1", "LGPL-3.0"}

for dep in licenses:
    if dep.license in BLOCKED:
        fail(f"Blocked license: {dep.name} ({dep.license})")
    elif dep.license in REVIEW_REQUIRED:
        warn(f"Review required: {dep.name} ({dep.license})")
```

---

## Supply Chain Security

### Verification

| Ecosystem | Method |
|-----------|--------|
| Python | `pip install --require-hashes -r requirements.txt` |
| Node.js | `npm ci` (uses `package-lock.json` integrity hashes) |
| Docker | `docker pull --platform` with digest pinning in Compose |

### Signing (Future)

- `cosign` for container image signing
- `sigstore` for artifact signing
- SLSA Level 2 compliance target

---

## Container Base Images

| Service | Base Image | Pinned Tag | Update Cadence |
|---------|------------|------------|----------------|
| API (Python) | `python` | `3.11-slim-bookworm` | Monthly |
| Web (Node) | `node` | `20-alpine` | Monthly |
| PostgreSQL | `postgres` | `16-alpine` | Monthly |
| Qdrant | `qdrant/qdrant` | `1.10.1` | Per release |
| Redis | `redis` | `7-alpine` | Monthly |

### Image Policy

- **No `latest` tags** — ever
- **Digest pinning** in Compose for production (`image@sha256:...`)
- **Multi-stage builds** — separate dev/prod targets
- **Non-root user** — `UID 1000` in all custom images
- **Read-only rootfs** — where possible
- **Minimal layers** — combine RUN commands; clean caches

---

## Dependency Inventory (Living Document)

Maintained in `DEPENDENCIES.md` (generated from lockfiles at release).

### Current Core Dependencies

#### Python (Production)
```
fastapi==0.110.1 (MIT)
uvicorn==0.29.0 (BSD-3)
pydantic==2.7.4 (MIT)
pydantic-settings==2.3.4 (MIT)
sqlalchemy==2.0.30 (MIT)
alembic==1.12.1 (MIT)
asyncpg==0.29.0 (Apache-2.0)
qdrant-client==1.10.1 (Apache-2.0)
pdfplumber==0.11.0 (MIT)
markdown-it-py==3.0.0 (MIT)
httpx==0.27.0 (BSD-3)
python-multipart==0.0.9 (Apache-2.0)
structlog==24.1.0 (Apache-2.0)
python-json-logger==2.0.7 (BSD-2)
tenacity==8.2.3 (Apache-2.0)
python-dotenv==1.0.1 (BSD-3)
```

#### Python (Dev)
```
pytest==8.2.2 (MIT)
pytest-asyncio==0.23.3 (Apache-2.0)
pytest-cov==4.1.0 (MIT)
pytest-mock==3.14.0 (MIT)
hypothesis==6.89.0 (MPL-2.0) ⚠️ Review required
ruff==0.4.4 (MIT)
mypy==1.10.0 (MIT)
bandit==1.7.5 (Apache-2.0)
pip-audit==2.6.1 (MIT)
pre-commit==3.6.0 (MIT)
faker==25.2.0 (MIT)
```

#### Node.js (Production)
```
next==14.2.3 (MIT)
react==18.3.1 (MIT)
react-dom==18.3.1 (MIT)
@tanstack/react-query==5.17.0 (MIT)
zod==3.22.4 (MIT)
axios==1.7.2 (MIT)
clsx==2.1.1 (MIT)
lucide-react==0.400.0 (ISC)
date-fns==3.6.0 (MIT)
```

#### Node.js (Dev)
```
typescript==5.4.5 (Apache-2.0)
eslint==8.57.0 (MIT)
prettier==3.2.5 (MIT)
@typescript-eslint/*==7.1.0 (MIT)
playwright==1.42.0 (Apache-2.0)
vitest==1.4.0 (MIT)
tailwindcss==3.4.3 (MIT)
```

---

## Compatibility Matrix (Verified)

| Component | Version | Compatible With | Verified |
|-----------|---------|-----------------|----------|
| Python | 3.11+ | All deps | ✅ 2026-10-22 |
| FastAPI | 0.110.1 | Pydantic 2.7+, Starlette 0.37+ | ✅ |
| Pydantic | 2.7.4 | FastAPI 0.110+, SQLAlchemy 2.0+ | ✅ |
| SQLAlchemy | 2.0.30 | asyncpg 0.29+, Alembic 1.12+ | ✅ |
| Qdrant Client | 1.10.1 | Qdrant Server 1.10+ | ✅ |
| asyncpg | 0.29.0 | PostgreSQL 14+ | ✅ |
| Node.js | 20 LTS | Next.js 14.2+, React 18.3+ | ✅ |
| Next.js | 14.2.3 | React 18.3, Tailwind 3.4+ | ✅ |
| React | 18.3.1 | TanStack Query 5.x | ✅ |
| TypeScript | 5.4.5 | Next.js 14.2+, ESLint 8.57+ | ✅ |

---

## Conflicts & Resolutions

| Conflict | Resolution |
|----------|------------|
| `hypothesis` (MPL-2.0) in dev deps | ⚠️ Allowed for testing only; not in production |
| `python-json-logger` 2.x vs 1.x | Pinned to 2.0.7 (breaking changes from 1.x) |
| `pydantic` v1 vs v2 | **v2 only**; all code uses v2 APIs |
| `sqlalchemy` 1.4 vs 2.0 | **2.0 only**; async patterns require 2.0 |
| `next.js` 13 vs 14 | **14.x (App Router)**; 13 not supported |

---

## Adding a New Dependency (Checklist)

- [ ] Justification documented in PR description
- [ ] License verified (allowed list)
- [ ] Alternatives evaluated (2+ documented)
- [ ] Version pinned exactly in `pyproject.toml` / `package.json`
- [ ] Lockfiles regenerated (`pip compile` / `npm install`)
- [ ] `pip-audit` / `npm audit` passes
- [ ] License check passes
- [ ] Tests updated/added for new functionality
- [ ] ADR created if architectural impact
- [ ] Documentation updated (this file + `DEPENDENCIES.md`)