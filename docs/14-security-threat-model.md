# RAGBench — Security and Threat Model

**Version:** 1.0  
**Date:** 2026-10-22  
**Status:** Initialization baseline

---

## Threat Model Overview

RAGBench is a **local-first, single-user development application**. The MVP does not implement authentication, authorization, or TLS. Public deployment is explicitly blocked until those controls are implemented and verified.

This threat model identifies risks, mitigations, and residual risks for the MVP scope.

---

## System Boundaries

```
┌─────────────────────────────────────────────────────────────┐
│                    TRUST BOUNDARY                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │  User    │  │  Web UI  │  │  API     │  │  PG/Qdrant│   │
│  │ Browser  │──▶│ (Next.js)│──▶│ (FastAPI)│──▶│           │   │
│  └──────────┘  └──────────┘  └────┬─────┘  └──────────┘    │
│                                   │                          │
│                    ┌──────────────┴──────────────┐          │
│                    │   PROVIDER ADAPTERS         │          │
│                    │  (Mock/Ollama/External)     │          │
│                    └─────────────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
                           │
                    ┌──────┴──────┐
                    │  EXTERNAL   │
                    │  (Optional) │
                    └─────────────┘
```

**Trust Assumptions:**
- User browser: Trusted (local user)
- Web UI: Trusted (served by API)
- API: Trusted (business logic)
- PostgreSQL/Qdrant: Trusted (internal, not exposed)
- Provider Adapters: **Semi-trusted** — validated at interface boundary
- External Providers: **Untrusted** — network boundary, secrets managed separately
- Uploaded Documents: **Untrusted data** — never executed, always validated
- Model Outputs: **Untrusted** — schema-validated, citations server-resolved

---

## STRIDE Analysis

### Spoofing
| Threat | Scenario | Mitigation | Residual Risk |
|--------|----------|------------|---------------|
| Impersonate API | Attacker runs fake API on same port | Loopback binding; no network exposure in MVP | Low (local only) |
| Impersonate User | N/A (no auth in MVP) | N/A | Accepted (MVP scope) |

### Tampering
| Threat | Scenario | Mitigation | Residual Risk |
|--------|----------|------------|---------------|
| Modify uploaded file | Malicious PDF with exploit | Parser sandbox (if possible); size/page limits; type validation | Medium (parser vulns) |
| Modify database | Direct PG access | Internal network only; no exposed port | Low |
| Modify vectors | Direct Qdrant access | Internal network only; no exposed port | Low |
| Modify model output | Adversarial generation | Schema validation; citation server-resolution | Low |
| Modify config | `.env` manipulation | `.env` ignored; validated at startup | Low |

### Repudiation
| Threat | Scenario | Mitigation | Residual Risk |
|--------|----------|------------|---------------|
| Deny ingestion | User claims document not uploaded | Audit events (if enabled); ingestion job logs | Medium (audit optional in MVP) |
| Deny query | User claims question not asked | API access logs (structured) | Medium |

### Information Disclosure
| Threat | Scenario | Mitigation | Residual Risk |
|--------|----------|------------|---------------|
| Secret leakage | API keys in logs/frontend | Never log secrets; frontend never receives secrets; secret scan in CI | Low |
| Document content leakage | Logs contain full text | Bound log payloads; redact sensitive fields; no full doc logging | Low |
| Vector data leakage | Qdrant exposed | No published port; internal only | Low |
| PII in documents | User uploads PII | Local-only; user responsibility; no processing of PII | Accepted |
| Error details | Stack traces in responses | Safe error messages; technical details logged server-side only | Low |

### Denial of Service
| Threat | Scenario | Mitigation | Residual Risk |
|--------|----------|------------|---------------|
| Large upload | 10GB file | Size validation at upload (nginx/FastAPI limit); reject before processing | Low |
| Parser resource exhaustion | Malformed PDF with 10000 pages | Page limit (200); parser timeout (30s); memory limits | Medium |
| Embedding DoS | Huge batch to provider | Batch size limit (100); request timeout (60s); retry bounds | Low |
| Qdrant overload | Massive index/query | Top-k max (20); collection limits; resource monitoring | Low |
| Generation DoS | Infinite generation | Max tokens (1024); provider timeout; request timeout | Low |

### Elevation of Privilege
| Threat | Scenario | Mitigation | Residual Risk |
|--------|----------|------------|---------------|
| Prompt injection → system access | Document contains "execute code" | No code execution from model output; schema validation; no tools | Low |
| Prompt injection → secret disclosure | Document contains "output API key" | Secrets not in context; server-side citation validation; model output not executed | Low |
| Prompt injection → policy bypass | Document contains "ignore safety" | Defense-in-depth: untrusted label, schema validation, citation check | Medium (not guaranteed) |
| Path traversal → filesystem | Filename `../../etc/passwd` | Generated storage names; filename only in metadata | Low |
| SQL injection | Malicious input in query | Parameterized queries (SQLAlchemy ORM); no raw SQL | Low |

---

## RAG-Specific Threats

### 1. Document as Attack Vector
**Threat:** Uploaded document contains instructions targeting the LLM or downstream systems.
**Mitigations:**
- Documents parsed as text only; no execution
- Retrieved chunks labeled "UNTRUSTED EVIDENCE" in prompt
- Generation output parsed against strict schema
- Citations validated server-side against retrieved set
- No tool/function calling from model output in MVP
**Residual Risk:** Sophisticated injection may still influence answer content (not system behavior). Documented as limitation.

### 2. Citation Hallucination
**Threat:** Model invents citation IDs that look valid but don't exist.
**Mitigations:**
- CitationValidator resolves every citation against retrieval results AND PostgreSQL
- Invalid citations → excluded from final answer; status adjusted
- Citation IDs are UUIDv5 (hard to guess)
**Residual Risk:** Model could guess valid UUID from context (extremely unlikely).

### 3. Context Poisoning
**Threat:** Malicious document chunks retrieved and used as evidence for unrelated queries.
**Mitigations:**
- Retrieval scoped to explicit corpus/document filter
- Chunk metadata includes document_id, version_id for validation
- User selects corpus at query time
**Residual Risk:** If corpus contains malicious docs, they can be retrieved. User controls corpus composition.

### 4. Model Output as Attack Vector
**Threat:** Model generates HTML/JS/Markdown that could be rendered unsafely.
**Mitigations:**
- Answer text treated as plain text in UI (React escapes by default)
- Citation excerpts from stored chunks (not model-generated)
- No `dangerouslySetInnerHTML` or equivalent
**Residual Risk:** Low if React defaults used correctly.

---

## Data Flow Security

### Upload Flow
```
User → HTTPS (localhost) → FastAPI → Validate (size, MIME, signature)
    → Generate safe storage name (UUID) → Store file
    → Compute SHA-256 → Parse (sandboxed, limits) → Extract text
    → Normalize → Chunk → Embed (provider) → Validate vectors
    → Upsert Qdrant (stable IDs) → Persist metadata (PG)
```
**Security Controls at Each Step:**
1. Size/MIME/signature validation BEFORE processing
2. Generated storage names (no user-controlled paths)
3. Parser limits (pages, chars, time, memory)
4. Provider timeouts and retry bounds
5. Vector dimension validation BEFORE indexing
6. Structured logging with correlation ID; no secrets

### Query Flow
```
User → HTTPS → FastAPI → Validate (question, corpus, top_k)
    → Embed question (provider) → Validate dimension
    → Qdrant query (corpus filter) → RetrievalResults
    → Validate chunk_ids in PG → Build context (budget)
    → Prompt with UNTRUSTED label → Generate (provider)
    → Parse response → Validate citations (server-side)
    → Assemble AnswerResponse → Return
```
**Security Controls:**
1. Corpus scope enforced at retrieval
2. Chunk validation against PG (source of truth)
3. Context budget prevents overflow
4. Prompt labels evidence as untrusted
5. Citations server-resolved (not model-trusted)
6. Answer schema validated before return

---

## Secrets Management

| Secret Type | Storage | Access | Rotation |
|-------------|---------|--------|----------|
| External API Keys | `.env` (ignored) / GitHub Secrets (CI) | Server-side only (Pydantic Settings) | Manual |
| Database Password | `.env` (ignored) / Docker secret | API service only | Manual |
| Qdrant API Key | `.env` (ignored) | API service only | Manual |
| **Frontend** | **NEVER** | **NEVER** | **N/A** |

**Rules:**
- No secrets in Docker images (build args only for non-secrets)
- No secrets in frontend bundle (verified by build scan)
- No secrets in logs (redaction middleware)
- `.env.example` contains placeholders only

---

## Network Security (MVP)

| Service | Port | Binding | Exposure |
|---------|------|---------|----------|
| Web UI | 3000 | 127.0.0.1:3000 | Localhost only |
| API | 8000 | 127.0.0.1:8000 | Localhost only |
| PostgreSQL | 5432 | Internal (Docker network) | Not published |
| Qdrant | 6333/6334 | Internal (Docker network) | Not published |
| Redis (if used) | 6379 | Internal (Docker network) | Not published |
| Ollama (optional) | 11434 | Host network (native) | Localhost only |

**Production Hardening Required Before Public Deployment:**
- [ ] Authentication (OIDC/JWT)
- [ ] Authorization (RBAC per corpus)
- [ ] TLS termination (certificates)
- [ ] Rate limiting (per user/IP)
- [ ] WAF / request validation
- [ ] Network policies (k8s) or firewall rules
- [ ] Audit logging to immutable store
- [ ] Secret manager integration (Vault, AWS Secrets Manager, etc.)

---

## Secure Coding Practices

### Python (Backend)
- Use Pydantic for all input/output validation
- SQLAlchemy ORM only (no raw SQL)
- `secrets.compare_digest` for token comparison
- `pathlib` for paths (no string concatenation)
- `tempfile` for temporary files (auto-cleanup)
- `asyncio.timeout` for all external calls
- Structured logging with `structlog`; redaction middleware

### TypeScript (Frontend)
- Strict TypeScript (`strict: true`)
- No `any` in production code
- React defaults (auto-escape) for all user content
- No `dangerouslySetInnerHTML`
- API client generated from OpenAPI (type-safe)
- Environment variables only for public config (no secrets)

### Infrastructure
- Pinned base images (`python:3.11-slim`, `node:20-alpine`, `postgres:16`, `qdrant/qdrant:1.10`)
- Non-root user in containers
- Read-only root filesystem where possible
- Drop capabilities (`CAP_DROP_ALL`)
- Health checks for all services
- Resource limits (CPU, memory) in Compose

---

## Vulnerability Management

| Process | Tool | Frequency |
|---------|------|-----------|
| Python dependencies | `pip-audit` / `safety` | CI + weekly scheduled |
| Node dependencies | `npm audit` / `snyk` | CI + weekly scheduled |
| Container images | `trivy` / `grype` | CI + on image update |
| Secret scanning | `trufflehog` / `git-secrets` | CI + pre-commit |
| SAST | `bandit` (Python) / `semgrep` | CI |

**Policy:** Critical/High vulnerabilities block merge unless documented exception with mitigation.

---

## Incident Response (Local MVP)

| Incident | Detection | Response |
|----------|-----------|----------|
| Secret committed | Pre-commit / CI scan | `git filter-repo` to purge; rotate secret |
| Malicious document uploaded | User report / log anomaly | Delete document; review parser logs |
| Provider API key leaked | Provider alert / billing anomaly | Rotate key immediately; audit access |
| Container compromise | Unusual process/network | `docker compose down -v`; rebuild from clean |
| Data corruption | Query errors / metric anomalies | Restore from backup; re-index |

---

## Security Test Requirements

| Test | Frequency | Automation |
|------|-----------|------------|
| Oversized upload rejection | Every PR | Integration test |
| Path traversal filename | Every PR | Security test |
| Prompt injection in docs | Every PR | Security test |
| Citation hallucination rejection | Every PR | Unit + Integration test |
| Secret scan | Every PR | CI job |
| Dependency audit | Weekly | Scheduled CI |
| Container scan | On image change | CI job |

---

## Residual Risks (Accepted for MVP)

| Risk | Justification | Monitoring |
|------|---------------|------------|
| No authentication | Single-user local tool | Loopback binding; docs warn against public exposure |
| No TLS | Local development only | Loopback; docs warn |
| Prompt injection not fully prevented | Defense-in-depth only | Adversarial tests document limits |
| Parser vulnerabilities (PDF) | Third-party library | Size/page limits; timeout; monitor CVEs |
| Model hallucination | Inherent to LLMs | Citation validation; abstention; honest labeling |
| No audit trail for all actions | MVP scope | Structured logs; optional audit events |

---

## Security Documentation for Reviewers

When reviewing RAGBench, verify:
1. [ ] No secrets in repository history
2. [ ] `.gitignore` covers all sensitive patterns
3. [ ] Docker Compose binds to loopback
4. [ ] No published DB/vector ports
5. [ ] Upload validation before processing
6. [ ] Citation validation server-side
7. [ ] Prompt labels evidence as untrusted
8. [ ] Structured logs with redaction
9. [ ] Adversarial tests in test suite
10. [ ] CI runs secret scan
11. [ ] README documents security boundaries
12. [ ] No "production ready" claims without hardening