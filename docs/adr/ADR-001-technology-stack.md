# ADR-001: Initial Technology Stack

**Status:** Accepted  
**Date:** 2026-10-22  
**Deciders:** Architecture Team  
**Technical Story:** RAGBench initialization

## Context

RAGBench needs a technology stack that supports:
- Local-first development with Docker Compose
- Type-safe API contracts between frontend and backend
- Modular, testable RAG pipeline implementation
- Provider abstraction for embeddings and generation
- Professional frontend with good DX
- Reproducible CI/CD without paid services
- Portfolio-quality codebase for technical review

## Decision

| Layer | Technology | Version Constraint |
|-------|------------|-------------------|
| Frontend Framework | Next.js (App Router) + React | 14.x / 18.x |
| Frontend Language | TypeScript | 5.x (strict mode) |
| Frontend Styling | Tailwind CSS + shadcn/ui pattern | 3.x |
| Backend Framework | FastAPI | 0.110.x |
| Backend Language | Python | 3.11+ |
| Validation/Settings | Pydantic v2 | 2.7+ |
| Metadata Database | PostgreSQL | 16 |
| ORM/Migrations | SQLAlchemy 2.0 + Alembic | 2.0 / 1.12 |
| Vector Database | Qdrant | 1.10+ |
| Vector Client | qdrant-client (gRPC) | 1.10+ |
| Document Parsing | pdfplumber, markdown-it-py | Latest stable |
| Embedding Providers | Interface + Mock/Ollama/OpenAI | - |
| Generation Providers | Interface + Mock/Ollama/OpenAI/Anthropic | - |
| Evaluation | Deterministic metrics + optional Ragas | - |
| Background Jobs | In-process (MVP); Celery+Redis if justified | - |
| Containerization | Docker Compose | v2 |
| CI/CD | GitHub Actions | - |
| Testing (Python) | pytest, pytest-asyncio | - |
| Testing (Frontend) | Vitest, Playwright | - |
| Linting (Python) | Ruff | - |
| Linting (Frontend) | ESLint + Prettier | - |
| Type Checking (Python) | mypy (strict) | - |
| Type Checking (Frontend) | tsc --noEmit | - |

## Alternatives Considered

| Alternative | Rejected Because |
|-------------|------------------|
| Django/DRF | Heavier; less explicit async; ORM less flexible for vector metadata |
| Flask | Less built-in validation/OpenAPI; more boilerplate |
| Express.js/Node backend | Single-language appeal but weaker ML ecosystem; type safety harder |
| GraphQL | Overkill for this API surface; REST + OpenAPI sufficient |
| pgvector (PostgreSQL) | Qdrant purpose-built for vector search; better performance/features |
| Weaviate/Milvus | Heavier; more complex deployment; Qdrant simpler for local |
| LangChain/LlamaIndex | Framework lock-in; obscures pipeline internals; against "explicit interfaces" principle |
| Streamlit/Gradio | Not professional portfolio frontend; limited customization |
| Vue/Svelte | Team expertise in React; Next.js ecosystem maturity |
| Plain CSS/CSS Modules | Tailwind faster for consistent design system; shadcn/ui accessible components |
| Poetry/PDM | uv faster; pip-tools standard; no strong preference |
| Celery from start | YAGNI; in-process simpler for MVP; add only if ingestion/evaluation exceed sync limits |

## Consequences

### Positive
- **Type safety end-to-end:** Pydantic ↔ TypeScript via OpenAPI
- **Explicit pipeline:** No framework magic; every stage inspectable
- **Provider flexibility:** Swap embedding/generation without pipeline changes
- **Local reproducibility:** Docker Compose + Mock mode = zero-config demo
- **Professional tooling:** Ruff, mypy, ESLint, TypeScript strict mode
- **Portfolio appeal:** Modern, recognized stack; demonstrates engineering judgment

### Negative
- **Two languages:** Python + TypeScript (mitigated by generated types)
- **Docker complexity:** Multi-service compose (mitigated by healthchecks, dev mounts)
- **Qdrant learning curve:** Newer than pgvector (mitigated by good docs, simple API)
- **Next.js App Router:** Newer paradigm (mitigated by sticking to stable features)

### Risks
| Risk | Mitigation |
|------|------------|
| FastAPI/Pydantic v2 breaking changes | Pin versions; test upgrades in isolation |
| Qdrant API changes | Pin client/server versions; integration tests |
| Next.js 15 breaking changes | Stay on 14.x for MVP; upgrade post-MVP |
| Ragas API instability | Hide behind evaluator interface; optional profile |
| Celery addition complexity | ADR-005 gates this decision |

## Implementation Notes

1. **API Contract Generation:** FastAPI → OpenAPI JSON → `openapi-typescript` → TypeScript types in `apps/web/lib/api/`
2. **Shared Config:** `.env.example` documents all variables; Pydantic Settings validates
3. **Mock Providers:** Implement `EmbeddingProvider` and `ChatGenerationProvider` protocols with deterministic implementations
3. **Dev Mounts:** Source code mounted in containers for hot-reload (API: `uvicorn --reload`, Web: `next dev`)
4. **Healthchecks:** PostgreSQL (`pg_isready`), Qdrant (`/healthz`), Redis (`redis-cli ping`)
5. **Loopback Binding:** `ports: ["127.0.0.1:8000:8000"]` for API and Web

## Related ADRs
- ADR-002: Vector Store Selection (Qdrant)
- ADR-003: Provider Abstraction
- ADR-004: Evaluation Metrics Strategy
- ADR-005: Background Processing