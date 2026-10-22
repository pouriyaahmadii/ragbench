# RAGBench — Product Vision

**Version:** 1.0  
**Date:** 2026-10-22  
**Status:** Initialization baseline

---

## Vision Statement

RAGBench is a **portfolio-grade, self-hostable RAG evaluation platform** that demonstrates how to build a grounded document assistant and, critically, how to measure whether changes to the RAG pipeline actually improve outcomes.

It is not merely a chat interface over a vector database. Its distinctive value is making the quality and behavior of every RAG stage—chunking, embedding, retrieval, generation, citation—inspectable, measurable, and comparable through reproducible experiments.

---

## Core Value Proposition

| For AI/LLM Engineering Hiring Managers | For Engineers and Researchers |
|----------------------------------------|-------------------------------|
| Evidence of production-grade RAG architecture | Reference implementation for chunking, embedding, retrieval, evaluation |
| Demonstration of evaluation rigor (not just "it works") | Reproducible experiment framework with versioned datasets |
| Security awareness (local-first, threat modeled) | Provider abstraction pattern for embeddings/LLMs |
| Honest reporting of limitations | Deterministic Mock mode for CI and demos |

---

## Primary Demonstration (MVP)

A technical reviewer can:

1. **Clone and start** the repository with `docker compose up` (no paid APIs, no model downloads)
2. **Upload** a small corpus of synthetic/openly licensed documents
3. **Inspect** ingestion: parsed pages, chunks, index metadata, embedding model identity
4. **Ask** an answerable question → receive structured answer with citations that resolve to stored chunks and page numbers
5. **Ask** an unanswerable question → system explicitly states "insufficient evidence" (no hallucinated citations)
6. **Run** a versioned evaluation dataset against the corpus
7. **Compare** two pipeline configurations (e.g., different chunk sizes or embedding models) on the same dataset
8. **Export** a metrics report showing retrieval metrics (Precision@k, Recall@k, MRR, nDCG) and, optionally, judge-based answer quality estimates clearly labeled as estimates

---

## Target Audience

| Audience | What They Evaluate |
|----------|-------------------|
| AI/LLM Engineering Hiring Managers | Architecture quality, evaluation rigor, security posture, reproducibility |
| Backend/Platform Engineers | API design, data model, provider abstractions, containerization, CI/CD |
| Applied ML Engineers | Chunking strategies, embedding models, retrieval parameters, experiment comparison |
| Technical Reviewers | Ability to run locally, understand code, verify claims without secrets |

---

## MVP Boundaries (Explicit)

### IN SCOPE (MVP)
- ✅ Document ingestion: PDF, TXT, Markdown
- ✅ Metadata preservation: document ID, version, page numbers, content hash
- ✅ Configurable chunking: fixed-size with overlap (baseline), structure-aware (experiment)
- ✅ Embedding provider interface: Mock, optional local (Ollama), optional external API
- ✅ Qdrant vector indexing with stable point IDs and versioned collections
- ✅ Dense retrieval with configurable top-k, explicit corpus/document scope
- ✅ Context construction with size limits and metadata preservation
- ✅ Generation provider interface: Mock, optional local, optional external API
- ✅ Citation validation: server-side resolution against retrieved/stored chunks
- ✅ Abstention: explicit "insufficient evidence" when retrieval lacks support
- ✅ Versioned evaluation datasets with explicit ground truth
- ✅ Deterministic retrieval metrics: Precision@k, Recall@k, MRR, nDCG, citation validity
- ✅ Experiment configuration versioning and comparison
- ✅ Docker Compose local deployment with loopback-only binding
- ✅ Deterministic Mock mode for all required demos and CI
- ✅ pytest + Playwright tests, GitHub Actions CI (no paid credentials)

### OUT OF SCOPE (MVP)
- ❌ Public multi-tenant SaaS deployment
- ❌ Unrestricted public URL crawling
- ❌ Executing instructions/code from uploaded documents
- ❌ Guaranteeing factual correctness of all generated answers
- ❌ Complete protection against prompt injection
- ❌ Fine-tuning or training foundation models
- ❌ Large-scale distributed indexing
- ❌ Mandatory paid model/embedding/evaluator APIs
- ❌ Multimodal (image/audio/video) RAG
- ❌ Complex agentic research workflows
- ❌ Arbitrary document archive ingestion (zip, tar, etc.)
- ❌ Automatic publication/external actions from generated answers
- ❌ Authentication/authorization (single-user local MVP)
- ❌ Hybrid search, reranking, query expansion (dense baseline only)

---

## User Pain Points Addressed

| Pain Point | RAGBench Approach |
|------------|-------------------|
| "RAG demos work but I can't tell if changes help" | Versioned experiments, deterministic metrics, fixed datasets |
| "Citations look real but resolve to nothing" | Server-side citation validation against actual retrieved chunks |
| "Evaluation uses LLM judges as ground truth" | Deterministic metrics first; judge estimates clearly labeled and optional |
| "Can't reproduce results from a blog post" | Immutable experiment configs, dataset versions, provider/model versions recorded |
| "Local demo needs OpenAI key and GPU" | Deterministic Mock mode works offline; local models optional |
| "Security is an afterthought" | Local-first boundary, threat model documented, untrusted content handling |
| "Repository is a mess of notebooks" | Modular architecture, explicit interfaces, professional repo structure |

---

## Business/Engineering Value

1. **Hiring Portfolio:** Tangible evidence of LLM engineering competence beyond "I built a chatbot"
2. **Reference Architecture:** Clean provider abstraction pattern applicable to production systems
3. **Evaluation Discipline:** Framework for honest, reproducible RAG measurement
4. **Security Baseline:** Local-first threat model extensible to production hardening
5. **Learning Platform:** Inspectable pipeline stages for understanding RAG failure modes

---

## Success Metrics (Target vs. Measured)

| Metric Category | Target (Planned) | Measured (Actual) |
|-----------------|------------------|-------------------|
| Setup time (clean clone → running demo) | < 5 minutes | TBD |
| Mock E2E runtime (tiny corpus) | < 10 seconds | TBD |
| Ingestion success rate (valid fixtures) | 100% | TBD |
| Citation validity rate (Mock mode) | 100% | TBD |
| Abstention rate (unanswerable questions) | 100% correct | TBD |
| Deterministic metric reproducibility | Bit-identical across runs | TBD |
| CI pass rate (required workflow) | 100% | TBD |
| Secret scan findings | 0 | TBD |

> **Note:** Measured values will be populated after implementation. No fabricated benchmarks.

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Mock mode too trivial to demonstrate real RAG behavior | Medium | High | Design Mock providers to exercise full pipeline contracts; document limitations |
| Qdrant/PostgreSQL version incompatibility in Compose | Low | Medium | Pin explicit compatible image tags; test startup order |
| Embedding dimension mismatch between providers | Medium | High | Validate dimension at ingestion and query time; version index by embedding config |
| LLM judge bias invalidates answer quality comparison | High | Medium | Never present judge scores as ground truth; always separate from deterministic metrics |
| Scope creep beyond MVP | High | High | Strict P0/P1/P2 prioritization; ADR required for architecture changes |
| Fabricated metrics/screenshots in portfolio | Low | Critical | Strict policy: only real implementation outputs; label unimplemented as "planned" |

---

## Assumptions

1. Reviewer has Docker and Docker Compose installed
2. Reviewer can allocate ~2-4 GB RAM for containers
3. Local macOS/Linux/WSL2 environment (Windows native Docker Desktop supported)
4. No paid API keys required for required demo path
5. Synthetic/openly licensed fixture documents sufficient for demonstration
6. Deterministic Mock providers sufficient for CI and core pipeline validation
7. Optional local models (Ollama) run natively on host, not in containers
8. Single-user local deployment; no authentication in MVP
9. English-only documents and queries for MVP
10. Left-to-right text; RTL support tested but not primary

---

## Non-Goals (Reiterated for Clarity)

RAGBench does **not** aim to:
- Replace production RAG frameworks (LangChain, LlamaIndex, Haystack) — it demonstrates the engineering patterns they use
- Provide a better chat UX than commercial products — UX is functional, not competitive
- Solve hallucination — it detects and abstains, with honest limitation reporting
- Be a benchmark suite — it includes a fixture dataset; real benchmarks require larger curated corpora
- Support every document format — MVP is PDF/TXT/MD only