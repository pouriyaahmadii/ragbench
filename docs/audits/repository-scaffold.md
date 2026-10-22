# Repository Scaffold Audit

**Date:** 2026-10-22  
**Auditor:** Architecture Team  
**Phase:** 4 — Repository Scaffold and Markdown Documentation Map

---

## Expected vs Actual Tree Comparison

### Root Level

| Path | Expected | Actual | Status |
|------|----------|--------|--------|
| `.github/workflows/` | ✅ | ✅ | Match |
| `apps/` | ✅ | ✅ | Match |
| `services/` | ✅ | ✅ | Match |
| `evals/` | ✅ | ✅ | Match |
| `data/` | ✅ | ✅ | Match |
| `infra/` | ✅ | ✅ | Match |
| `scripts/` | ✅ | ✅ | Match |
| `docs/` | ✅ | ✅ | Match |
| `compose.yaml` | ✅ | ✅ | Match |
| `Makefile` | ✅ | ✅ | Match |
| `.env.example` | ✅ | ✅ | Match |
| `.gitignore` | ✅ | ✅ | Match |
| `.dockerignore` | ✅ | ✅ | Match |
| `.editorconfig` | ✅ | ✅ | Match |
| `README.md` | ✅ | ✅ | Match |
| `LICENSE` / `LICENSE_DECISION.md` | ✅ | ✅ (DECISION) | Match |

### Apps/Web

| Path | Expected | Actual | Status |
|------|----------|--------|--------|
| `apps/web/app/` | ✅ | ✅ | Match |
| `apps/web/components/ui/` | ✅ | ✅ | Match |
| `apps/web/features/documents/` | ✅ | ✅ | Match |
| `apps/web/features/chat/` | ✅ | ✅ | Match |
| `apps/web/features/evaluations/` | ✅ | ✅ | Match |
| `apps/web/features/experiments/` | ✅ | ✅ | Match |
| `apps/web/lib/` | ✅ | ✅ | Match |
| `apps/web/hooks/` | ✅ | ✅ | Match |
| `apps/web/public/` | ✅ | ✅ | Match |
| `apps/web/tests/e2e/` | ✅ | ✅ | Match |

### Services/Backend

| Path | Expected | Actual | Status |
|------|----------|--------|--------|
| `services/backend/app/api/v1/routes/` | ✅ | ✅ | Match |
| `services/backend/app/core/` | ✅ | ✅ | Match |
| `services/backend/app/config/` | ✅ | ✅ | Match |
| `services/backend/app/db/` | ✅ | ✅ | Match |
| `services/backend/app/models/` | ✅ | ✅ | Match |
| `services/backend/app/schemas/` | ✅ | ✅ | Match |
| `services/backend/app/repositories/` | ✅ | ✅ | Match |
| `services/backend/app/services/` | ✅ | ✅ | Match |
| `services/backend/app/ingestion/` | ✅ | ✅ | Match |
| `services/backend/app/chunking/` | ✅ | ✅ | Match |
| `services/backend/app/embeddings/` | ✅ | ✅ | Match |
| `services/backend/app/vectorstore/` | ✅ | ✅ | Match |
| `services/backend/app/retrieval/` | ✅ | ✅ | Match |
| `services/backend/app/generation/` | ✅ | ✅ | Match |
| `services/backend/app/citations/` | ✅ | ✅ | Match |
| `services/backend/app/evaluation/` | ✅ | ✅ | Match |
| `services/backend/app/providers/` | ✅ | ✅ | Match |
| `services/backend/app/workers/` | ✅ | ✅ | Match |
| `services/backend/app/observability/` | ✅ | ✅ | Match |
| `services/backend/migrations/` | ✅ | ✅ | Match |
| `services/backend/tests/unit/` | ✅ | ✅ | Match |
| `services/backend/tests/integration/` | ✅ | ✅ | Match |
| `services/backend/tests/contract/` | ✅ | ✅ | Match |

### Evals

| Path | Expected | Actual | Status |
|------|----------|--------|--------|
| `evals/datasets/` | ✅ | ✅ | Match |
| `evals/cases/` | ✅ | ✅ | Match |
| `evals/baselines/` | ✅ | ✅ | Match |
| `evals/reports/` | ✅ | ✅ | Match |

### Data

| Path | Expected | Actual | Status |
|------|----------|--------|--------|
| `data/samples/` | ✅ | ✅ | Match |
| `data/expected/` | ✅ | ✅ | Match |
| `data/README.md` | ✅ | ✅ | Match |

### Infra

| Path | Expected | Actual | Status |
|------|----------|--------|--------|
| `infra/docker/` | ✅ | ✅ | Match |
| `infra/postgres/` | ✅ | ✅ | Match |
| `infra/monitoring/` | ✅ | ✅ | Match |

### Scripts

| Path | Expected | Actual | Status |
|------|----------|--------|--------|
| `scripts/` | ✅ | ✅ | Match |

### Docs

| Path | Expected | Actual | Status |
|------|----------|--------|--------|
| `docs/adr/` | ✅ | ✅ | Match |
| `docs/audits/` | ✅ | ✅ | Match |
| `docs/diagrams/` | ✅ | ✅ | Match |
| `docs/runbooks/` | ✅ | ✅ | Match |

---

## Additional Directories Created (Not in Original Spec)

| Path | Reason |
|------|--------|
| `services/backend/app/api/` | Parent for `api/v1/` — organizational |
| `services/backend/app/api/v1/` | Parent for `routes/` — organizational |
| `state/` | **Removed** — was test artifact, now cleaned up |

---

## Folder-Level README Files Created

| Path | Purpose |
|------|---------|
| `apps/web/README.md` | Frontend structure, conventions, development |
| `services/backend/README.md` | Backend structure, conventions, development |
| `evals/README.md` | Dataset format, immutability, fixtures |
| `data/README.md` | Fixture documents, expected outputs, licensing |
| `infra/README.md` | PostgreSQL extensions, Docker override, monitoring |
| `scripts/README.md` | Benchmark, data, maintenance, CI scripts |

---

## .gitignore Coverage Verification

| Pattern | Covered |
|---------|---------|
| `.env` / `.env.*` (except `.env.example`) | ✅ |
| `uploads/` | ✅ |
| `qdrant_data/` / `postgres_data/` / `redis_data/` | ✅ |
| `*.model` / `models/` / `checkpoints/` / `weights/` | ✅ |
| `__pycache__/` / `*.pyc` / `.pytest_cache/` / `.mypy_cache/` / `.ruff_cache/` | ✅ |
| `.coverage` / `htmlcov/` / `.tox/` | ✅ |
| `.venv/` / `venv/` / `env/` | ✅ |
| `node_modules/` / `.npm/` / `.yarn/` / `.pnp.*` | ✅ |
| `.next/` / `.out/` / `dist/` / `build/` / `*.tsbuildinfo` | ✅ |
| `.eslintcache` / `.stylelintcache` | ✅ |
| `.vscode/` / `.idea/` / `*.swp` / `*.swo` / `*~` | ✅ |
| `.DS_Store` / `Thumbs.db` / `ehthumbs.db` / `Desktop.ini` | ✅ |
| `*.log` / `logs/` | ✅ |
| `tmp/` / `temp/` / `*.tmp` / `*.bak` | ✅ |
| `playwright-report/` / `test-results/` / `.screenshots/` | ✅ |
| `evals/reports/` / `benchmarks/results/` | ✅ |
| `docs/_build/` / `site/` | ✅ |

---

## .dockerignore Coverage Verification

| Pattern | Covered |
|---------|---------|
| `.git` / `.gitignore` / `.gitattributes` / `.github` | ✅ |
| `docs/` / `*.md` (except `README.md`) | ✅ |
| `.venv` / `venv/` / `env/` / `__pycache__/` / `*.py[cod]` | ✅ |
| `.pytest_cache/` / `.mypy_cache/` / `.ruff_cache/` | ✅ |
| `.coverage` / `htmlcov/` / `.tox/` | ✅ |
| `node_modules/` / `.npm/` / `.yarn/` / `.next/` / `.out/` | ✅ |
| `dist/` / `build/` / `*.tsbuildinfo` / `.eslintcache` | ✅ |
| `.env` / `.env.*` (except `.env.example`) | ✅ |
| `*.pem` / `*.key` / `*.crt` / `secrets/` | ✅ |
| `uploads/` / `qdrant_data/` / `postgres_data/` / `redis_data/` | ✅ |
| `*.db` / `*.sqlite` / `evals/reports/` / `benchmarks/results/` | ✅ |
| `.vscode/` / `.idea/` / `*.swp` / `*.swo` / `*~` / `.DS_Store` / `Thumbs.db` | ✅ |
| `*.log` / `logs/` / `tmp/` / `temp/` / `*.tmp` / `*.bak` | ✅ |
| `playwright-report/` / `test-results/` / `.screenshots/` | ✅ |
| `*.model` / `*.bin` / `*.safetensors` / `models/` / `checkpoints/` / `weights/` | ✅ |
| CI configs (`.gitlab-ci.yml`, `.azure-pipelines.yml`, `Jenkinsfile`) | ✅ |

---

## No Nested Duplicate Repository

✅ Verified: No `ragbench/ragbench/` nested structure. Workspace root = repository root.

## No Competing Package Managers

✅ Verified:
- Python: `pyproject.toml` + `requirements.txt` (uv/pip-tools compatible)
- Node.js: `package.json` + `package-lock.json` (npm)
- No `poetry.lock`, `yarn.lock`, `pnpm-lock.yaml` conflicts

## No Accidental User-File Deletion

✅ Verified: Original user files preserved:
- `RAGBench_Product_SPEC.md`
- `RAGBench_Antigravity_Roadmap.md`
- `RAGBench_START_HERE.md`
- `RAGBench_Evaluation_Sample.json`
- `.gitattributes`

## All Documented Paths Consistent

✅ Verified: All paths in documentation (PRD, Architecture, ADRs) match actual repository structure.

---

## Summary

| Check | Result |
|-------|--------|
| Expected directories present | ✅ All 50+ directories match |
| Root configuration files present | ✅ All 7 files present |
| Folder-level READMEs created | ✅ 6 READMEs added |
| .gitignore comprehensive | ✅ All patterns covered |
| .dockerignore comprehensive | ✅ All patterns covered |
| No nested repo | ✅ Clean |
| No competing package managers | ✅ Clean |
| User files preserved | ✅ Clean |
| Paths consistent with docs | ✅ Clean |

**Status: PASS** — Repository scaffold matches approved architecture and Phase 4 requirements.