from typing import Optional, List, Dict, Any
from uuid import UUID
import asyncio
import time
import uuid
import logging

from app.config import Settings
from app.schemas.answer import Answer, Citation, AnswerStatus
from app.retrieval.schemas import RetrievalResult, RetrievalRequest, RetrievalConfig
from app.retrieval.service import RetrievalService
from app.generation.prompt import build_rag_prompt, parse_generation_response
from app.providers.protocols import ChatGenerationProvider
from app.citations.validation import validate_and_build_citations, adjust_answer_status
from app.providers.factory import get_provider_factory
from app.providers.protocols import ChatGenerationProvider
from app.schemas.answer import Answer
from app.config import Settings

logger = logging.getLogger(__name__)


class RAGOrchestrator:
    """
    Orchestrates the end-to-end RAG pipeline:
    1. Validate question and corpus scope
    2. Build query representation
    3. Retrieve top-k chunks
    4. Build bounded context
    6. Call generation provider
    7. Parse response
    8. Validate citations
    9. Persist answer
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.retrieval_service = RetrievalService(settings)
        self.provider_factory = get_provider_factory(settings)
    
    async def initialize(self):
        """Initialize the orchestrator and its dependencies."""
        await self.retrieval_service.initialize()
    
    async def answer_question(
        self,
        question: str,
        corpus_id: str,
        top_k: Optional[int] = None,
        generation_config: Optional[dict] = None,
        retrieval_config: Optional[dict] = None,
    ) -> dict:
        """
        Execute the complete RAG pipeline for a question.
        
        Args:
            question: User's question
            corpus_id: Target corpus/collection ID
            top_k: Number of chunks to retrieve (overrides default)
            generation_config: Optional generation configuration
            retrieval_config: Optional retrieval configuration
            
        Returns:
            Dict with answer, citations, status, and metadata
        """
        start_time = time.time()
        answer_id = uuid.uuid4()
        
        try:
            # Stage 1: Validate question and corpus scope
            if not question or not question.strip():
                return self._build_error_answer(
                    answer_id, question, "Question cannot be empty", "failed"
                )
            
            if not corpus_id:
                return self._build_error_answer(
                    answer_id, question, "Corpus ID is required", "failed"
                )
            
            # Stage 2: Build query representation (embedding)
            query_vector = await self._embed_query(question)
            
            # Stage 3: Retrieve top-k chunks
            retrieval_config_obj = RetrievalConfig(
                top_k=top_k or 5,
                **(retrieval_config or {})
            )
            retrieval_request = RetrievalRequest(
                query_vector=query_vector,
                corpus_id=UUID(corpus_id),
                config=retrieval_config_obj
            )
            
            retrieval_start = time.time()
            retrieval_response = await self.retrieval_service.retrieve(retrieval_request)
            retrieval_time_ms = int((time.time() - retrieval_start) * 1000)
            
            if not retrieval_response.results:
                return self._build_insufficient_evidence_answer(
                    answer_id, question, corpus_id, retrieval_time_ms
                )
            
            # Stage 4: Build bounded context
            retrieval_results = retrieval_response.results
            context = self._build_context(retrieval_results)
            
            # Stage 5: Call generation provider
            generation_provider = self._get_generation_provider(generation_config)
            
            generation_start = time.time()
            prompt = self._build_generation_prompt(question, retrieval_results)
            generation_response = await generation_provider.generate(
                messages=[{"role": "user", "content": prompt}],
                config=generation_config
            )
            generation_time_ms = int((time.time() - generation_start) * 1000)
            
            # Stage 6: Parse response
            parsed = parse_generation_response(generation_response.text)
            answer_text = parsed.get("answer_text", "")
            parsed_citations = parsed.get("citations", [])
            limitations = parsed.get("limitations", [])
            
            # Stage 7: Validate citations against retrieved chunks
            valid_citations, invalid_citations, citation_objects = validate_and_build_citations(
                parsed.get("citations", []),
                retrieval_results
            )
            
            # Stage 8: Adjust answer status based on citation validation
            if not retrieval_results:
                status = AnswerStatus.insufficient_evidence
                answer_text = "The provided documents do not contain sufficient evidence to answer this question."
                citations = []
                limitations = ["No relevant evidence found in selected corpus."]
            elif not retrieval_results and not valid_citations:
                status = AnswerStatus.insufficient_evidence
                answer_text = "The provided documents do not contain sufficient evidence to answer this question."
                citations = []
                limitations = ["No valid citations could be generated from retrieved evidence."]
            else:
                # Valid citations exist
                if not retrieval_results:
                    status = AnswerStatus.insufficient_evidence
                    answer_text = "The provided documents do not contain sufficient evidence to answer this question."
                    citations = []
                    limitations = ["No relevant evidence found in selected corpus."]
                elif not valid_citations:
                    status = AnswerStatus.insufficient_evidence
                    answer_text = "The provided documents do not contain sufficient evidence to answer this question."
                    citations = []
                    limitations = ["No valid citations could be generated from retrieved evidence."]
                else:
                    status = "answered"
                    answer_text = answer_text or "Answer generated."
                    citations = [c for c in valid_citations]
                    limitations = []
            
            # Build final answer
            total_time_ms = int((time.time() - start_time) * 1000)
            retrieval_time_ms = int((time.time() - retrieval_start) * 1000) if 'retrieval_start' in locals() else 0
            generation_time_ms = int((time.time() - generation_start) * 1000) if 'generation_start' in locals() else 0
            
            answer = Answer(
                answer_id=answer_id,
                question=question,
                answer_text=answer_text,
                status=status,
                citations=citations,
                limitations=limitations,
                provider_metadata={
                    "provider": "mock" if self.settings.MOCK_MODE else "real",
                    "model": "mock" if self.settings.MOCK_MODE else "real",
                    "version": "1.0",
                    "prompt_version": PROMPT_VERSION
                },
                latency_metadata={
                    "retrieval_ms": retrieval_time_ms,
                    "generation_ms": generation_time_ms,
                    "total_ms": total_time_ms
                }
            )
            
            return answer
            
        except Exception as e:
            logger.exception(f"RAG pipeline failed for question: {question}")
            total_time_ms = int((time.time() - start_time) * 1000)
            return self._build_error_answer(
                answer_id, question, str(e), "failed", total_time_ms
            )
    
    def _build_error_answer(self, answer_id: UUID, question: str, error: str, status: str, total_time_ms: int = 0) -> Answer:
        """Build an error answer."""
        return Answer(
            answer_id=answer_id,
            question=question,
            answer_text="An error occurred while processing your question.",
            status=AnswerStatus.failed,
            citations=[],
            limitations=[f"Error: {error}"],
            provider_metadata={},
            latency_metadata={"total_ms": total_time_ms}
        )
    
    def _build_insufficient_evidence_answer(self, answer_id: UUID, question: str, corpus_id: str, retrieval_time_ms: int) -> Answer:
        """Build answer for insufficient evidence case."""
        total_time_ms = retrieval_time_ms
        return Answer(
            answer_id=answer_id,
            question=question,
            answer_text="The provided documents do not contain sufficient evidence to answer this question.",
            status=AnswerStatus.insufficient_evidence,
            citations=[],
            limitations=["No relevant evidence found in selected corpus."],
            provider_metadata={
                "provider": "mock" if self.settings.MOCK_MODE else "real",
                "model": "mock" if self.settings.MOCK_MODE else "real",
                "version": "1.0",
                "prompt_version": PROMPT_VERSION
            },
            latency_metadata={
                "retrieval_ms": retrieval_time_ms,
                "generation_ms": 0,
                "total_ms": retrieval_time_ms
            }
        )
    
    async def _embed_query(self, question: str) -> List[float]:
        """Generate embedding for the query."""
        embedding_provider = self.provider_factory.get_embedding_provider()
        result = await embedding_provider.embed([question])
        return result.vectors[0]
    
    def _get_generation_provider(self, generation_config: Optional[dict]) -> ChatGenerationProvider:
        """Get the generation provider based on configuration."""
        if generation_config and generation_config.get("provider"):
            config = {
                "provider": generation_config.get("provider", "mock"),
                "model": generation_config.get("model", "mock"),
                "temperature": generation_config.get("temperature", 0.0),
                "max_tokens": generation_config.get("max_tokens", 1024),
            }
        else:
            config = {
                "provider": "mock" if self.settings.MOCK_MODE else "openai",
                "model": "mock" if self.settings.MOCK_MODE else "gpt-4o-mini",
            }
        return self.provider_factory.get_generation_provider(config)
    
    def _build_generation_prompt(self, question: str, retrieval_results: List) -> str:
        """Build the generation prompt with retrieved context."""
        from app.generation.prompt import build_rag_prompt
        from app.config import Settings
        
        settings = Settings()
        return build_rag_prompt(question, [r for r in retrieval_results], Settings())
    
    def _build_context(self, retrieval_results: List) -> str:
        """Build context string from retrieval results."""
        context_parts = []
        for result in retrieval_results:
            source_info = f"[DOC: {result.source_title}"
            if result.page_number:
                source_info += f" | PAGE: {result.page_number}"
            source_info += f" | CHUNK: {result.chunk_id}]"
            context_parts.append(f"{source_info}\n{result.text}")
        return "\n\n---\n\n".join(context_parts)