# ADR-002: Vector Store Selection (Qdrant)

**Status:** Accepted  
**Date:** 2026-10-22  
**Deciders:** Architecture Team  
**Technical Story:** RAGBench initialization

## Context

RAGBench requires a vector database for storing chunk embeddings and performing similarity search during retrieval. The vector store must:
- Support efficient dense vector similarity search (cosine/dot product)
- Provide stable point IDs for citation resolution
- Support metadata payloads for filtering and citation display
- Run locally via Docker Compose with persistent volumes
- Have a well-maintained Python client (gRPC preferred)
- Support collection versioning for experiment reproducibility
- Be suitable for single-node local development (MVP scale: ~50k vectors)

## Decision

**Choose Qdrant 1.10+ as the vector database.**

### Configuration
- **Image:** `qdrant/qdrant:1.10.1` (pinned)
- **Protocol:** gRPC (primary) / HTTP (fallback)
- **Storage:** Named Docker volume `qdrant_data` at `/qdrant/storage`
- **Ports:** Internal only (6333, 6334) — not published to host
- **Healthcheck:** `wget --spider http://localhost:6333/healthz`

### Collection Strategy
- One collection per `IndexVersion` (corpus + chunking config + embedding model + dimension)
- Collection name format: `corpus_{corpus_id}_idx_{index_version_short}`
- Vector params: dimension from embedding config, distance = Cosine
- HNSW index: default parameters (ef_construct=100, m=16)

### Point ID Strategy
- **Format:** UUIDv5 with namespace `ragbench.chunk`
- **Name:** `{corpus_id}:{document_version_id}:{chunk_index}:{chunker_config_hash}`
- **Rationale:** Deterministic, stable, collision-resistant, encodes identity

### Payload Schema
```json
{
  "chunk_id": "uuid",
  "document_id": "uuid",
  "document_version_id": "uuid",
  "corpus_id": "uuid",
  "page_number": 3,
  "source_title": "Policy Document v1",
  "text_excerpt": "First 200 chars...",
  "chunk_index": 5
}
```

### Versioning & Re-indexing
- Changing embedding model/dimension/chunking → new `IndexVersion` → new Qdrant collection
- Old collections retained until explicitly cleaned up
- Re-index API creates new collection, upserts all vectors, then atomically switches

## Alternatives Considered

| Alternative | Rejected Because |
|-------------|------------------|
| **pgvector (PostgreSQL extension)** | Less optimized for vector search; no native HNSW; combined metadata/vector storage complicates scaling; Qdrant purpose-built |
| **Weaviate** | Heavier resource usage; more complex deployment; GraphQL API adds complexity; overkill for local MVP |
| **Milvus** | Requires separate etcd/MinIO; heavy for single-node; operational complexity |
| **Chroma** | Less mature; limited filtering; no gRPC; better suited for prototyping |
| **FAISS (embedded)** | No persistence/server mode; not suitable for multi-process access; no metadata filtering |
| **Redis + Redis Stack** | Vector search less mature; memory-only unless Redis Enterprise; limited filtering |

## Consequences

### Positive
- **Purpose-built for vectors:** Optimized HNSW, filtering, payload storage
- **Docker-native:** Simple Compose integration, healthchecks, volumes
- **gRPC client:** High-performance Python client (`qdrant-client`)
- **Collection versioning:** Natural fit for `IndexVersion` concept
- **Local-first:** Runs entirely in-container, no external dependencies
- **Active maintenance:** Regular releases, good documentation

### Negative
- **Additional service:** Extra container vs. pgvector in PostgreSQL
- **Learning curve:** Team must learn Qdrant-specific APIs
- **Resource usage:** Separate memory allocation from PostgreSQL

### Risks
| Risk | Mitigation |
|------|------------|
| Version incompatibility | Pin image tag (1.10.1); test upgrades in isolation |
| Collection management complexity | Encapsulate in `VectorStore` service; automated versioning |
| gRPC vs HTTP client issues | Use gRPC primary; fallback to HTTP if needed |

## Implementation Notes

1. **Service Module:** `services/backend/app/vectorstore/` — encapsulates all Qdrant operations
2. **Client Config:** `QdrantClient(url="http://qdrant:6333", prefer_grpc=True)`
3. **Healthcheck Dependency:** API service waits for Qdrant `healthy` via Compose `condition: service_healthy`
4. **No Public Ports:** Qdrant ports (6333, 6334) only on internal Docker network
5. **Payload Validation:** Always verify payload metadata against PostgreSQL before trusting for citations

## Verification Against Official Documentation

- **Qdrant 1.10 Quickstart:** https://qdrant.tech/documentation/quickstart/
- **Python Client:** https://github.com/qdrant/qdrant-client
- **Collection API:** Verified `create_collection`, `upsert`, `search`, `delete` methods
- **Point IDs:** UUID strings supported natively
- **Payload Filtering:** Verified `Filter` / `FieldCondition` syntax
- **Snapshots:** `POST /collections/{name}/snapshots` for backup/restore

## Related ADRs
- ADR-001: Initial Technology Stack
- ADR-003: Provider Abstraction (embedding providers write to Qdrant)
- ADR-004: Evaluation Metrics (retrieval runs against Qdrant)
- ADR-005: Background Processing (re-indexing jobs)