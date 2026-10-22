# RAGBench — Dependency and Licensing Policy

**Version:** 1.0  
**Date:** 2026-10-22  
**Status:** Initialization baseline

---

## Dependency Management Principles

1. **Minimal Dependencies:** Only add packages that provide clear, measurable value.
2. **Pinned Versions:** All dependencies pinned to exact versions in lockfiles.
3. **License Compliance:** No GPL/AGPL/LGPL in transitive closure without legal review.
4. **Security First:** Regular vulnerability scanning; critical vulns block merge.
5. **Standard Tooling:** Use ecosystem-standard tools (pip/uv, npm, Cargo).

---

## Python Dependencies (Backend)

### Package Manager
- **Tool:** `uv` (preferred) or `pip-tools` for lockfile management
- **Lockfile:** `requirements.lock` (generated from `pyproject.toml` / `requirements.in`)
- **Virtual Env:** `.venv` (ignored) or Docker-only

### Core Dependencies (Planned)

| Package | Purpose | License | Version Pinning |
|---------|---------|---------|-----------------|
| `fastapi` | Web framework | MIT | `==0.110.*` |
| `uvicorn[standard]` | ASGI server | BSD-3 | `==0.29.*` |
| `pydantic` | Validation/settings | MIT | `==2.7.*` |
| `pydantic-settings` | Config management | MIT | `==2.3.*` |
| `sqlalchemy` | ORM | MIT | `==2.0.*` |
| `alembic` | Migrations | MIT | `==1.12.*` |
| `asyncpg` | PostgreSQL driver | Apache-2.0 | `==0.29.*` |
| `qdrant-client` | Vector DB client | Apache-2.0 | `==1.10.*` |
| `pdfplumber` | PDF parsing | MIT | `==0.11.*` |
| `markdown-it-py` | Markdown parsing | MIT | `==3.0.*` |
| `pytest` | Testing | MIT | `==8.2.*` |
| `pytest-asyncio` | Async testing | Apache-2.0 | `==0.23.*` |
| `pytest-cov` | Coverage | MIT | `==4.1.*` |
| `httpx` | HTTP client | BSD-3 | `==0.27.*` |
| `python-multipart` | Form parsing | Apache-2.0 | `==0.0.*` |
| `structlog` | Structured logging | Apache-2.0 | `==24.1.*` |
| `python-json-logger` | JSON logging | BSD-2 | `==2.0.*` |
| `ruff` | Linting/format | MIT | `==0.4.*` |
| `mypy` | Type checking | MIT | `==1.10.*` |
| `tenacity` | Retry logic | Apache-2.0 | `==8.2.*` |

### Optional Dependencies (Provider Adapters)

| Package | Provider | License | Notes |
|---------|----------|---------|-------|
| `ollama` | Ollama local | MIT | `==0.2.*` |
| `openai` | OpenAI API | MIT | `==1.30.*` |
| `anthropic` | Anthropic API | MIT | `==0.25.*` |
| `cohere` | Cohere API | MIT | `==4.4.*` |
| `ragas` | Evaluation | Apache-2.0 | `==0.2.*` (verify version) |
| `celery` | Background jobs | BSD-3 | `==5.3.*` (if ADR-005 approves) |
| `redis` | Celery broker | MIT | `==5.0.*` (if Celery) |

### Development Dependencies
| Package | Purpose |
|---------|---------|
| `pytest-mock` | Mocking |
| `pytest-xdist` | Parallel tests |
| `hypothesis` | Property-based testing |
| `faker` | Test data generation |
| `pre-commit` | Git hooks |
| `bandit` | Security linting |
| `pip-audit` | Vulnerability scanning |

---

## Node.js Dependencies (Frontend)

### Package Manager
- **Tool:** `npm` with `package-lock.json` (committed)
- **Node Version:** 20 LTS (pinned in `.nvmrc` and Dockerfile)

### Core Dependencies (Planned)

| Package | Purpose | License | Version |
|---------|---------|---------|---------|
| `next` | React framework | MIT | `14.2.*` |
| `react` | UI library | MIT | `18.3.*` |
| `react-dom` | DOM rendering | MIT | `18.3.*` |
| `typescript` | Type safety | Apache-2.0 | `5.4.*` |
| `@tanstack/react-query` | Server state | MIT | `5.17.*` |
| `zod` | Schema validation | MIT | `3.22.*` |
| `axios` | HTTP client | MIT | `1.7.*` |
| `clsx` | Classnames utility | MIT | `2.1.*` |
| `tailwindcss` | Styling | MIT | `3.4.*` |
| `lucide-react` | Icons | ISC | `0.300.*` |
| `date-fns` | Date formatting | MIT | `3.3.*` |

### UI Component Libraries (Choose One)
| Option | License | Notes |
|--------|---------|-------|
| `shadcn/ui` + `radix-ui` | MIT | Copy-paste components; no runtime dependency |
| `@headlessui/react` | MIT | Unstyled accessible components |
| `@radix-ui/*` | MIT | Primitives for custom components |
| Custom | - | Build from scratch (more work) |

**Decision:** `shadcn/ui` pattern (copy-paste) preferred for full control and minimal deps.

### Development Dependencies
| Package | Purpose |
|---------|---------|
| `eslint` | Linting |
| `prettier` | Formatting |
| `@typescript-eslint/*` | TS linting |
| `eslint-plugin-react-hooks` | React hooks rules |
| `eslint-plugin-tailwindcss` | Tailwind linting |
| `playwright` | E2E testing |
| `@playwright/test` | Test runner |
| `vitest` | Unit testing |
| `@testing-library/react` | Component testing |

---

## Docker Base Images

| Service | Base Image | Pinned Tag |
|---------|------------|------------|
| API | `python` | `3.11-slim-bookworm` |
| Web | `node` | `20-alpine` |
| PostgreSQL | `postgres` | `16-alpine` |
| Qdrant | `qdrant/qdrant` | `1.10.1` |
| Redis | `redis` | `7-alpine` |

**Policy:** Update base images monthly for security patches; test full suite before merging.

---

## Licensing Policy

### Project License
**Status:** Unresolved — documented in `docs/02-scope-and-mvp.md`

**Options:**
| License | Pros | Cons |
|---------|------|------|
| MIT | Simple, permissive, widely recognized | No patent grant |
| Apache-2.0 | Patent grant, explicit contributions | Slightly longer |
| BSD-3-Clause | Permissive, no endorsement | No patent grant |

**Decision Process:** Finalize before Phase 23 (README/Licensing). Record in `LICENSE` file.

### Third-Party License Compliance

#### Requirements
1. **No GPL/AGPL/LGPL** in production dependencies (runtime).
2. **Copyleft check** in CI: `pip-licenses` / `npm ls --all --json` → scan for viral licenses.
3. **Attribution** for all third-party code (including copied snippets).
4. **License files** collected in `THIRD_PARTY_LICENSES.md` (generated at release).

#### Allowed License Families
- MIT, BSD-2/3/4, Apache-2.0, ISC, Unicode-DFS-2016, Python-2.0, MPL-2.0 (file-level)
- Public domain (CC0, Unlicense)

#### Requires Review
- MPL-2.0 (if statically linked)
- LGPL-2.1/3.0 (dynamic linking only; legal review)
- Custom/Proprietary (explicit permission required)

#### Prohibited
- GPL-2.0/3.0, AGPL-3.0
- Any license requiring source distribution of combined work

### License Compliance in CI
```yaml
# .github/workflows/license-check.yml
jobs:
  license-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Python license scan
        run: |
          pip install pip-licenses
          pip-licenses --format=json --with-urls > python-licenses.json
          python scripts/check_licenses.py python-licenses.json
      - name: Node license scan
        run: |
          cd apps/web
          npm install -g license-checker
          license-checker --json --out ../../node-licenses.json
          python ../scripts/check_licenses.py ../../node-licenses.json
```

### Attribution for Copied Code
- `shadcn/ui` components: Include original license notice in component file header
- Algorithm implementations: Comment with source URL and license
- Configuration snippets: Comment with source

---

## Dependency Review Process

### Adding a New Dependency
1. **Justify:** Document why existing code/std lib can't solve the problem
2. **Evaluate:** License, maintenance status, popularity, bundle size impact
3. **Alternatives:** List 2+ alternatives considered
4. **Test:** Add to branch; run full test suite; check bundle size
5. **Document:** Update `DEPENDENCIES.md` (or this doc) with rationale
6. **Review:** PR requires approval from maintainer

### Updating Dependencies
- **Security updates:** Auto-merge if tests pass (Dependabot/Renovate)
- **Minor updates:** Monthly batch; test full suite
- **Major updates:** Separate PR; migration guide; ADR if breaking

### Removing Dependencies
- Dead code elimination via `ruff` / `eslint` unused import detection
- Bundle size analysis before/after
- Verify no transitive dependency gaps

---

## Supply Chain Security

### Verification
- **Python:** `pip install --require-hashes` (hashes in lockfile)
- **Node:** `npm ci` (uses `package-lock.json` integrity hashes)
- **Docker:** `docker pull --platform` with digest pinning in Compose

### Signing (Future)
- `cosign` for container image signing
- `sigstore` for artifact signing
- SLSA Level 2 compliance target

---

## Dependency Inventory (Living Document)

Maintained in `DEPENDENCIES.md` (generated from lockfiles at release):

```
# Python Production
fastapi==0.110.1 (MIT)
uvicorn==0.29.0 (BSD-3)
pydantic==2.7.4 (MIT)
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

# Python Dev
pytest==8.2.2 (MIT)
pytest-asyncio==0.23.3 (Apache-2.0)
pytest-cov==4.1.0 (MIT)
pytest-mock==3.14.0 (MIT)
hypothesis==6.89.0 (MPL-2.0)
ruff==0.4.4 (MIT)
mypy==1.10.0 (MIT)
bandit==1.7.5 (Apache-2.0)
pip-audit==2.6.1 (MIT)

# Node Production
next==14.2.3 (MIT)
react==18.3.1 (MIT)
react-dom==18.3.1 (MIT)
@tanstack/react-query==5.17.0 (MIT)
zod==3.22.4 (MIT)
axios==1.7.2 (MIT)
clsx==2.1.1 (MIT)
tailwindcss==3.4.3 (MIT)
lucide-react==0.400.0 (ISC)
date-fns==3.6.0 (MIT)

# Node Dev
typescript==5.4.5 (Apache-2.0)
eslint==8.57.0 (MIT)
prettier==3.2.5 (MIT)
@typescript-eslint/*==7.1.0 (MIT)
playwright==1.42.0 (Apache-2.0)
vitest==1.4.0 (MIT)
```

---

## Vulnerability Response

| Severity | Response Time | Action |
|----------|---------------|--------|
| Critical | 24 hours | Patch/upgrade immediately; emergency release |
| High | 72 hours | Patch/upgrade; scheduled release |
| Medium | 2 weeks | Plan upgrade in sprint |
| Low | Next release | Include in routine updates |

**Process:**
1. CI detects vulnerability (`pip-audit`, `npm audit`, `trivy`)
2. Block merge if Critical/High
3. Create PR with fix/upgrade
4. Run full test suite
5. Merge and release

---

## Open Questions

1. **Dependency Pinning Strategy:** Exact versions (`==`) vs compatible (`~=`)? Current: exact for reproducibility.
2. **Monorepo Tooling:** `uv` workspaces vs separate lockfiles? Current: separate per service.
3. **Private Registry:** Need for internal packages? (Not currently)
4. **SBOM Generation:** `syft` for Software Bill of Materials at release? (Recommended)
5. **License Exception Process:** Formal process for LGPL/MPL if needed?