from fastapi import APIRouter, HTTPException, Depends, Body
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel

from app.config import Settings, get_settings
from app.services.rag_orchestrator import RAGOrchestrator

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


class QueryRequest(BaseModel):
    """Request model for RAG query."""
    question: str
    corpus_id: str
    top_k: Optional[int] = None
    generation_config: Optional[Dict[str, Any]] = None
    retrieval_config: Optional[Dict[str, Any]] = None


class QueryResponse(BaseModel):
    """Response model for RAG query."""
    answer_id: str
    question: str
    answer_text: str
    status: str
    citations: List[dict]
    limitations: List[str]
    provider_metadata: dict
    latency_metadata: dict


@router.post(
    "/query",
    response_model=QueryResponse,
    status_code=200,
    summary="Ask a question using RAG",
)
async def query_rag(
    request: QueryRequest,
    settings: Settings = Depends(get_settings),
):
    """
    Ask a question using RAG over the specified corpus.
    
    The system will:
    1. Embed the question
    2. Retrieve top-k relevant chunks from the corpus
    3. Build context from retrieved chunks
    4. Generate answer using the configured generation provider
    4. Validate citations against retrieved chunks
    5. Return structured answer with citations and metadata
    """
    # Initialize RAG orchestrator
    orchestrator = RAGOrchestrator(settings)
    await orchestrator.initialize()
    
    try:
        result = await orchestrator.answer_question(
            question=request.question,
            corpus_id=request.corpus_id,
            top_k=request.top_k,
            generation_config=request.generation_config,
            retrieval_config=request.retrieval_config,
        )
        
        return QueryResponse(
            answer_id=result.answer_id,
            question=result.question,
            answer_text=result.answer_text,
            status=result.status.value if hasattr(result.status, 'value') else result.status,
            citations=[
                {
                    "chunk_id": str(c.chunk_id),
                    "document_id": str(c.document_id),
                    "document_version_id": str(c.document_version_id),
                    "page_number": c.page_number,
                    "source_title": c.source_title,
                    "excerpt": c.excerpt
                }
                for c in result.citations
            ],
            limitations=result.limitations,
            provider_metadata=result.provider_metadata,
            latency_metadata=result.latency_metadata,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/history",
    response_model=List[dict],
    summary="Get query history",
)
async def get_query_history(
    skip: int = 0,
    limit: int = 20,
    corpus_id: Optional[str] = None,
):
    """Get query history for a corpus."""
    # This would query the database for past queries
    return []


@router.get(
    "/history/{query_id}",
    response_model=dict,
    summary="Get query details",
)
async def get_query_details(
    query_id: str,
):
    """Get details of a specific query."""
    raise HTTPException(status_code=404, detail="Query not found")