# RAGBench — Glossary

**Version:** 1.0  
**Date:** 2026-10-22  
**Status:** Phase 1 deliverable

---

## Core Concepts

| Term | Definition |
|------|------------|
| **RAG (Retrieval-Augmented Generation)** | A pattern where an LLM answers questions by first retrieving relevant document chunks, then generating an answer grounded in those chunks. |
| **Grounded Answer** | An answer where every factual claim is supported by a citation to a retrieved source chunk. |
| **Citation** | A reference from the generated answer to a specific source chunk, including chunk ID, document ID, page number (when available), and excerpt. |
| **Abstention / Insufficient Evidence** | The system explicitly states it cannot answer because the retrieved documents don't contain sufficient information. Not a failure — a correct behavior. |
| **Hallucination** | Model generating plausible but unsupported claims. RAGBench mitigates via citation validation and abstention, but does not eliminate. |

---

## Pipeline Stages

| Term | Definition |
|------|------------|
| **Ingestion** | End-to-end process: upload → validation → parsing → chunking → embedding → indexing → ready. |
| **Parsing** | Extracting text and structural metadata (page numbers, headings) from PDF/TXT/Markdown files. |
| **Chunking** | Splitting normalized text into overlapping segments with preserved provenance metadata. |
| **Embedding** | Converting chunk text into dense vectors via an embedding provider (Mock, Ollama, OpenAI, etc.). |
| **Indexing** | Upserting vectors to Qdrant with stable point IDs and payload metadata for retrieval. |
| **Retrieval** | Querying the vector index with an embedded question to get top-k relevant chunks. |
| **Context Construction** | Building a bounded prompt context from retrieved chunks, preserving source metadata. |
| **Generation** | Calling the LLM provider with the constructed prompt to produce an answer. |
| **Citation Validation** | Server-side verification that every cited chunk ID exists in retrieval results and PostgreSQL. |

---

## Data Model

| Term | Definition |
|------|------------|
| **Document** | Logical identity of an uploaded file (display name, media type, status). |
| **Document Version** | Immutable snapshot of a document at ingestion time (parser metadata, content hash, page count). |
| **Chunk** | A text segment with metadata: chunk_id, document_version_id, chunk_index, page_number, text_hash, chunker_config_hash, embedding config. |
| **Index Version** | Immutable identity of a vector collection, defined by corpus + chunking config + embedding provider/model/dimension. |
| **Corpus** | Logical grouping of documents for scoped retrieval (corpus_id). |

---

## Evaluation

| Term | Definition |
|------|------------|
| **Dataset** | Logical collection of evaluation samples (e.g., "ragbench-demo"). |
| **Dataset Version** | Immutable snapshot of a dataset with a content hash (e.g., "v1.0.0"). |
| **Sample** | Single evaluation case: question, corpus_id, relevant_chunk_ids, relevance_grades, reference_answer, answerable flag, tags. |
| **Ground Truth** | Explicit relevance labels (relevant_chunk_ids, relevance_grades) for deterministic metric calculation. |
| **Deterministic Metrics** | Precision@k, Recall@k, MRR, nDCG@k, Citation Validity — computed from ground truth without LLMs. |
| **Judge-Based Metrics** | Faithfulness, Answer Relevance, etc. — estimated by an LLM judge (Ragas or custom), clearly labeled as estimates. |
| **Experiment** | Immutable configuration manifest: dataset version, index version, chunking, embedding, retrieval, generation, judge config. |
| **Experiment Run** | Single execution of an experiment against a dataset/index, producing per-sample results and aggregate metrics. |
| **Comparison** | Side-by-side metric deltas between two experiment runs on the same dataset version. |

---

## Providers & Modes

| Term | Definition |
|------|------------|
| **Provider Interface** | Abstract protocol (EmbeddingProvider, ChatGenerationProvider) that decouples pipeline from specific model SDKs. |
| **Mock Provider** | Deterministic implementation for CI/demo: fixed embeddings, fixture-based answers. No external calls. |
| **Local Provider** | Adapter for models running locally (e.g., Ollama on macOS). Optional, no API costs. |
| **External Provider** | Adapter for cloud APIs (OpenAI, Anthropic, Cohere). Optional, requires credentials. |
| **Mock Mode** | Global flag (`MOCK_MODE=true`) forcing all providers to Mock implementations. Default for CI and local demo. |

---

## Metrics

| Term | Definition |
|------|------------|
| **Precision@k** | \|TopK ∩ Relevant\| / k — fraction of top-k retrieved that are relevant. Denominator always k. |
| **Recall@k** | \|TopK ∩ Relevant\| / \|Relevant\| — fraction of all relevant chunks found in top-k. Undefined if no relevant. |
| **MRR (Mean Reciprocal Rank)** | Mean of 1/rank of first relevant result across queries. 0 if none found. |
| **nDCG@k** | Normalized Discounted Cumulative Gain at k — ranking quality with graded relevance (gain 2^rel-1, discount log2(rank+1)). |
| **Citation Validity** | Fraction of generated citations that resolve to actual retrieved chunks in the correct corpus scope. |
| **Faithfulness** | Judge-based estimate: does the answer only claim what the evidence supports? |
| **Answer Relevance** | Judge-based estimate: does the answer address the question? |

---

## Infrastructure

| Term | Definition |
|------|------------|
| **Docker Compose** | Local orchestration: PostgreSQL, Qdrant, API, Web, optional Redis/Worker. |
| **Loopback Binding** | Developer ports (3000, 8000) bound to 127.0.0.1 only — not publicly exposed. |
| **Healthcheck** | Container-level readiness probe (pg_isready, Qdrant /healthz, redis-cli ping). |
| **Named Volume** | Persistent Docker volume (postgres_data, qdrant_data, redis_data) surviving container restarts. |
| **Mock Mode** | Environment where all providers are Mock — no paid APIs, no model downloads required. |

---

## Security

| Term | Definition |
|------|------------|
| **Trust Boundary** | Line separating untrusted data (uploads, retrieved chunks, model output) from trusted logic (validation, citation resolution, schema enforcement). |
| **Prompt Injection** | Malicious instructions embedded in documents or retrieved chunks attempting to hijack model behavior. |
| **Defense-in-Depth** | Multiple mitigations: untrusted labeling in prompt, schema validation, server-side citation resolution, no tool execution. |
| **Citation Validation** | Server-side check: every cited chunk_id must exist in retrieval results AND in PostgreSQL with matching document/version. |
| **Secret Redaction** | Automatic removal of API keys, tokens, passwords from logs. |

---

## Operations

| Term | Definition |
|------|------------|
| **Immutability** | Once created, dataset versions, experiment configs, index versions, document versions cannot be modified. Changes create new versions. |
| **Config Hash** | SHA-256 of canonical JSON serialization (sorted keys, no whitespace) — used for experiment/index identity. |
| **Reproducibility** | Same experiment config + dataset version + index version → bit-identical deterministic metrics. |
| **Idempotent Ingestion** | Re-ingesting same document version with same config produces same chunk IDs and vectors (upsert). |
| **Cascade Delete** | Deleting a document removes versions, chunks, vectors, ingestion jobs per documented retention policy. |

---

## File Formats

| Term | Definition |
|------|------------|
| **PDF** | Portable Document Format — parsed with pdfplumber/pymupdf, page metadata preserved. |
| **TXT** | Plain text (UTF-8) — treated as single page. |
| **Markdown** | CommonMark — parsed with markdown-it-py, heading structure as pseudo-pages. |
| **JSONL** | JSON Lines — used for evaluation dataset samples (one sample per line). |

---

## Acronyms

| Acronym | Expansion |
|---------|-----------|
| RAG | Retrieval-Augmented Generation |
| LLM | Large Language Model |
| MRR | Mean Reciprocal Rank |
| nDCG | Normalized Discounted Cumulative Gain |
| PII | Personally Identifiable Information |
| SSRF | Server-Side Request Forgery |
| MVP | Minimum Viable Product |
| CI | Continuous Integration |
| CD | Continuous Deployment |
| ORM | Object-Relational Mapping |
| gRPC | Google Remote Procedure Call |
| SHA | Secure Hash Algorithm |
| UUID | Universally Unique Identifier |
| NFC | Normalization Form Canonical Composition |
| API | Application Programming Interface |
| UI | User Interface |
| UX | User Experience |

---

## Persian Translations (for User-Facing Progress)

| English | Persian |
|---------|---------|
| Document Ingestion | پردازش و_INDEX‌سازی سند |
| Chunking | تکه‌تکه کردن متن |
| Embedding | بردارگذاری (تبدیل به بردار) |
| Retrieval | بازیابی اطلاعات |
| Generation | تولید پاسخ |
| Citation | استناد / منبع |
| Abstention | امتناع از پاسخ (دلیل: مدارک ناکافی) |
| Ground Truth | برچسب‌های واقعی / حقیقت میدان |
| Deterministic Metrics | معیارهای قطعی/مشخص |
| Judge-based Metrics | معیارهای برآوردشده توسط قاضی (LLM) |
| Mock Mode | حالت نمایشی/تست (بدون API واقعی) |
| Experiment | آزمایش / مقایسه پیکربندی‌ها |
| Index Version | نسخه ایندکس برداری |
| Provider Interface | واسط ارائه‌دهنده (مدل) |