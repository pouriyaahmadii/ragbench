import asyncio
import time
import uuid
from typing import List, Optional, Dict, Any
from uuid import UUID

from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue

from app.config import Settings
from app.retrieval.schemas import (
    RetrievalResult,
    RetrievalConfig,
    RetrievalRequest,
    RetrievalResponse,
    RetrievalError,
    DimensionMismatchError,
    CollectionNotFoundError,
    InvalidFilterError,
)
from app.vectorstore.client import get_qdrant_client
from app.vectorstore.collections import ensure_collection_exists, search_vectors


class RetrievalService:
    """Service for dense vector retrieval with validation."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self._client: Optional[QdrantClient] = None
        self._collection_cache: Dict[str, Dict] = {}
    
    @property
    def client(self) -> QdrantClient:
        """Lazy initialization of Qdrant client."""
        if self._client is None:
            self._client = get_qdrant_client(self.settings)
        return self._client
    
    async def initialize(self):
        """Initialize the retrieval service."""
        # Client will be initialized on first use
        pass
    
    def _get_collection_name(self, corpus_id: UUID) -> str:
        """Get collection name for corpus."""
        return f"corpus_{corpus_id}"
    
    async def _validate_collection(self, corpus_id: UUID, expected_dimension: int) -> str:
        """Validate collection exists and has correct dimension."""
        collection_name = self._get_collection_name(corpus_id)
        
        try:
            # Get collections once and cache the result
            collections_response = self.client.get_collections()
            existing_names = [c.name for c in collections_response.collections]
            
            if collection_name not in existing_names:
                raise CollectionNotFoundError(collection_name)
            
            # Verify dimension
            collection_info = self.client.get_collection(collection_name)
            existing_dim = collection_info.config.params.vectors.size
            if existing_dim != self.settings.EMBEDDING_DIMENSION:
                raise DimensionMismatchError(
                    expected=self.settings.EMBEDDING_DIMENSION,
                    actual=existing_dim
                )
            
            return collection_name
        except Exception as e:
            if isinstance(e, (CollectionNotFoundError, DimensionMismatchError)):
                raise
            raise
    
    def _build_filter(self, filters: Dict[str, Any]) -> Optional[Any]:
        """Build Qdrant filter from conditions."""
        if not filters:
            return None
        
        from qdrant_client.http.models import Filter, FieldCondition, MatchValue, MatchAny
        
        must_conditions = []
        for key, value in filters.items():
            if isinstance(value, list):
                # For list values, create should conditions
                must_conditions.append(
                    Filter(
                        must=[FieldCondition(key=key, match=MatchAny(any=value))]
                    )
                )
            else:
                must_conditions.append(
                    Filter(
                        must=[FieldCondition(key=key, match=MatchValue(value=value))]
                    )
                )
        
        if not must_conditions:
            return None
        
        return Filter(must=must_conditions)
    
    async def retrieve(self, request: RetrievalRequest) -> RetrievalResponse:
        """
        Perform dense vector retrieval with validation.
        
        This is the main entry point for dense retrieval.
        """
        start_time = time.time()
        
        # Validate collection and dimension
        collection_name = await self._validate_collection(
            request.corpus_id, 
            len(request.query_vector)
        )
        
        # Build filter if provided
        query_filter = self._build_filter(request.config.filters)
        
        # Perform search
        search_start = time.time()
        results = self.client.search(
            collection_name=collection_name,
            query_vector=request.query_vector,
            limit=request.config.top_k,
            query_filter=self._build_filter(request.config.filters),
            with_payload=True,
            with_vectors=False,
        )
        search_time_ms = int((time.time() - search_start) * 1000)
        
        # Convert results to RetrievalResult
        results_list = []
        for rank, hit in enumerate(results, 1):
            payload = hit.payload or {}
            
            # Validate payload has required fields
            required_fields = ["chunk_id", "document_id", "document_version_id", "corpus_id"]
            for field in required_fields:
                if field not in payload:
                    # Skip results with missing required fields
                    continue
            
            # Build retrieval result
            result = RetrievalResult(
                rank=rank,
                score=hit.score,
                chunk_id=uuid.UUID(payload["chunk_id"]),
                document_id=uuid.UUID(payload["document_id"]),
                document_version_id=uuid.UUID(payload["document_version_id"]),
                corpus_id=uuid.UUID(payload["corpus_id"]),
                page_number=payload.get("page_number"),
                source_title=payload.get("source_title", "Unknown"),
                text=payload.get("text_excerpt", ""),
                metadata=payload,
            )
            results_list.append(result)
        
        query_time_ms = int((time.time() - start_time) * 1000)
        
        return RetrievalResponse(
            results=results_list,
            query_time_ms=query_time_ms,
            total_candidates=len(results_list),
            config=request.config,
        )
    
    async def retrieve_batch(
        self, 
        requests: List[RetrievalRequest]
    ) -> List[RetrievalResponse]:
        """Perform multiple retrievals concurrently."""
        tasks = [self.retrieve(req) for req in requests]
        return await asyncio.gather(*tasks)
    
    async def validate_citation(
        self, 
        citation_chunk_id: UUID, 
        corpus_id: UUID
    ) -> bool:
        """Validate that a cited chunk exists in the collection."""
        try:
            collection_name = await self._validate_collection(corpus_id, self.settings.EMBEDDING_DIMENSION)
            
            # Try to retrieve the point
            result = self.client.retrieve(
                collection_name=self._get_collection_name(corpus_id),
                ids=[str(citation_chunk_id)],
                with_payload=True,
                with_vectors=False,
            )
            
            return len(result) > 0
        except Exception:
            return False
    
    async def get_chunk_metadata(self, chunk_id: UUID, corpus_id: UUID) -> Optional[Dict]:
        """Retrieve full metadata for a chunk."""
        try:
            collection_name = self._get_collection_name(corpus_id)
            
            result = self.client.retrieve(
                collection_name=collection_name,
                ids=[str(chunk_id)],
                with_payload=True,
                with_vectors=False,
            )
            
            if not result:
                return None
            
            hit = result[0]
            return {
                "id": str(hit.id),
                "payload": hit.payload,
                "score": None,
            }
        except Exception:
            return None


def get_retrieval_service(settings: Settings) -> RetrievalService:
    """Factory function to create retrieval service."""
    return RetrievalService(settings)