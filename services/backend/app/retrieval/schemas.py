from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID


class RetrievalResult(BaseModel):
    """Result of a retrieval operation with all metadata needed for citation."""
    rank: int = Field(ge=1, description="Rank in retrieval results (1-indexed)")
    score: float = Field(description="Similarity score (cosine/dot); NOT a probability")
    chunk_id: UUID = Field(description="Unique identifier of the chunk")
    document_id: UUID = Field(description="Document identifier")
    document_version_id: UUID = Field(description="Document version identifier")
    corpus_id: UUID = Field(description="Corpus/collection identifier")
    page_number: Optional[int] = Field(default=None, description="Page number when available")
    source_title: str = Field(description="Source document title")
    text: str = Field(description="Full chunk text for context building")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class RetrievalConfig(BaseModel):
    """Configuration for retrieval operation."""
    method: str = Field(default="dense", description="Retrieval method (dense, hybrid, etc.)")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results to retrieve")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Metadata filters")
    score_threshold: Optional[float] = Field(default=None, description="Minimum similarity score")


class RetrievalRequest(BaseModel):
    """Request for retrieval operation."""
    query_vector: List[float] = Field(description="Query embedding vector")
    config: RetrievalConfig = Field(default_factory=RetrievalConfig)
    corpus_id: UUID = Field(description="Corpus/collection to search")


class RetrievalResponse(BaseModel):
    """Response from retrieval operation."""
    results: List[RetrievalResult] = Field(description="Ranked retrieval results")
    query_time_ms: int = Field(description="Query execution time in milliseconds")
    total_candidates: int = Field(description="Total candidates considered")
    config: RetrievalConfig = Field(description="Configuration used for retrieval")


class RetrievalError(Exception):
    """Base exception for retrieval errors."""
    def __init__(self, message: str, error_code: str = "RETRIEVAL_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class DimensionMismatchError(RetrievalError):
    """Raised when query vector dimension doesn't match collection."""
    def __init__(self, expected: int, actual: int):
        super().__init__(
            f"Vector dimension mismatch: expected {expected}, got {actual}",
            error_code="DIMENSION_MISMATCH"
        )
        self.expected = expected
        self.actual = actual


class CollectionNotFoundError(RetrievalError):
    """Raised when collection doesn't exist."""
    def __init__(self, collection_name: str):
        super().__init__(
            f"Collection not found: {collection_name}",
            error_code="COLLECTION_NOT_FOUND"
        )
        self.collection_name = collection_name


class InvalidFilterError(RetrievalError):
    """Raised when filter conditions are invalid."""
    def __init__(self, message: str):
        super().__init__(message, error_code="INVALID_FILTER")


class RetrievalResultWithMetadata(BaseModel):
    """Extended retrieval result with validation status."""
    result: RetrievalResult
    validated: bool = Field(description="Whether citation was validated against source metadata")
    validation_error: Optional[str] = Field(default=None, description="Validation error if any")


class RetrievalBatchResult(BaseModel):
    """Result of batch retrieval operation."""
    results: List[RetrievalResultWithMetadata]
    query_time_ms: int
    failed_count: int = 0