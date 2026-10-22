# ADR-002: RAG Pipeline Boundaries

**Status:** Accepted  
**Date:** 2026-10-22  
**Deciders:** Architecture Team  
**Technical Story:** RAGBench initialization

## Context

The RAG pipeline consists of multiple stages: ingestion, parsing, chunking, embedding, indexing, retrieval, context construction, generation, citation validation. The architecture must define clear boundaries between these stages to enable:
- Independent testing and development
- Provider swapping without pipeline changes
- Experiment configuration versioning
- Observability per stage
- Security validation at trust boundaries

## Decision

### Pipeline Stage Modules (Independent Packages)

```
services/backend/app/
├── ingestion/       # Upload → validation → parsing → text extraction
├── chunking/        # Text normalization → chunking strategies → metadata
├── embeddings/      # Provider orchestration → batching → validation
├── vectorstore/     # Qdrant collections → upsert/query/delete
├── retrieval/       # Scoped search → result mapping → metadata validation
├── generation/      # Prompt construction → provider call → response parsing
├── citations/       # Citation validation → metadata resolution
├── evaluation/      # Dataset runner → metrics → experiment orchestration
└── providers/       # Mock/Ollama/External implementations
```

### Stage Interfaces (Contracts)

Each stage exposes a **typed interface** (Protocol or ABC) with explicit inputs/outputs:

```python
# Example: Chunker Protocol
class Chunker(Protocol):
    def chunk(self, text: str, config: ChunkingConfig) -> list[Chunk]: ...

# Example: Embedding Provider Protocol
class EmbeddingProvider(Protocol):
    async def embed(self, texts: list[str]) -> EmbeddingResult: ...
    @property
    def dimension(self) -> int: ...
```

### Data Flow (No Shared State)

Stages communicate **only through return values** — no global state, no shared mutable objects:

```
IngestionResult → ChunkingResult → EmbeddingResult → IndexingResult
                                                      ↓
Query → RetrievalResult → Context → GenerationResult → CitationValidationResult
                                                      ↓
                                              AnswerResponse
```

### Configuration Versioning

Each stage's configuration is **hashed and recorded** with its outputs:
- `ChunkingConfig` → `chunker_config_hash` (stored on every chunk)
- `EmbeddingConfig` → part of `IndexVersion` identity
- `RetrievalConfig` → part of `Experiment` config
- `GenerationConfig` → part of `Experiment` config + `Answer.provider_metadata`
- `PromptTemplate` → `prompt_version` hash

### Trust Boundaries

| Boundary | Untrusted Side | Trusted Side | Validation |
|----------|----------------|--------------|------------|
| Upload | User file | Ingestion | Size, MIME, signature, parser limits |
| Parsed Text | Document content | Chunking | Size limits, no execution |
| Retrieved Chunks | Vector payload | Generation | Labeled "UNTRUSTED" in prompt |
| Model Output | Generation | Citations | Schema validation + server-side resolution |
| Citations | Model claims | Storage | Resolved against PG + Qdrant |

## Alternatives Considered

| Alternative | Rejected Because |
|-------------|------------------|
| Single `RAGPipeline` class | Violates single responsibility; hard to test stages independently |
| LangChain/LlamaIndex pipelines | Framework lock-in; obscures internals; against portfolio goals |
| Event-driven (Kafka/Redis streams) | Over-engineering for local MVP; adds infrastructure |
| Database-backed stage queue | Unnecessary complexity; in-process sufficient for MVP |
| Shared `PipelineContext` object | Implicit coupling; makes testing harder; hidden dependencies |

## Consequences

### Positive
- **Testability:** Each stage unit-testable with mocked dependencies
- **Observability:** Per-stage timing, logging, error categorization
- **Swappability:** Change chunking strategy without touching embedding code
- **Experiment Integrity:** Config hashes prevent silent mismatches
- **Security:** Explicit trust boundaries with validation

### Negative
- **More boilerplate:** Interface definitions, data classes for each stage
- **Serialization overhead:** Passing data between stages (negligible for MVP scale)
- **Learning curve:** Developers must understand stage contracts

### Risks
| Risk | Mitigation |
|------|------------|
| Interface proliferation | Keep interfaces minimal; use Protocols for structural typing |
| Version drift between stages | Config hashes recorded at every boundary; CI validates compatibility |
| Performance overhead | Profile; optimize hot paths (embedding batching, Qdrant queries) |

## Implementation Notes

1. **Protocols over ABCs:** Use `typing.Protocol` for structural subtyping; no inheritance required
2. **Pydantic for Data Classes:** All stage inputs/outputs are Pydantic models (validation + serialization)
3. **Dependency Injection:** Stages receive providers via constructor (not global imports)
4. **Error Handling:** Each stage raises typed exceptions (`IngestionError`, `ChunkingError`, etc.) caught at orchestration layer
5. **Orchestration Service:** `services/app/services/rag_orchestrator.py` coordinates stages for query flow

## Related ADRs
- ADR-001: Initial Technology Stack
- ADR-003: Provider Abstraction
- ADR-004: Evaluation Metrics Strategy