from typing import List, Tuple
from uuid import UUID
from app.schemas.answer import Citation
from app.retrieval.schemas import RetrievalResult
from app.generation.prompt import validate_citations_against_retrieval, build_citation_objects


def validate_and_build_citations(
    parsed_citations: List[str],
    retrieval_results: List[RetrievalResult]
) -> Tuple[List[str], List[str], List]:
    """
    Validate citations against retrieval results and build Citation objects.
    
    Returns:
        Tuple of (valid_citation_ids, invalid_citation_ids, citation_objects)
    """
    # Validate citations against retrieval results
    retrieved_chunk_ids = {str(r.chunk_id) for r in retrieval_results}
    
    valid = []
    invalid = []
    
    for citation in parsed_citations:
        if citation in retrieved_chunk_ids:
            valid.append(citation)
        else:
            invalid.append(citation)
    
    # Build Citation objects for valid citations
    result_by_chunk_id = {str(r.chunk_id): r for r in retrieval_results}
    
    citation_objects = []
    for chunk_id in valid:
        if chunk_id in result_by_chunk_id:
            result = result_by_chunk_id[chunk_id]
            excerpt = result.text[:200] + "..." if len(result.text) > 200 else result.text
            
            citation = Citation(
                chunk_id=UUID(chunk_id),
                document_id=result.document_id,
                document_version_id=result.document_version_id,
                page_number=result.page_number,
                source_title=result.source_title,
                excerpt=excerpt
            )
            citation_objects.append(citation)
    
    return valid, invalid, citation_objects


def adjust_answer_status(
    answer_text: str,
    valid_citations: List[str],
    retrieval_results: List
) -> tuple[str, str, List[str]]:
    """
    Adjust answer text and status based on citation validation.
    
    Returns:
        Tuple of (adjusted_answer_text, status, limitations)
    """
    limitations = []
    
    if not retrieval_results:
        return (
            "The provided documents do not contain sufficient evidence to answer this question.",
            "insufficient_evidence",
            ["No relevant evidence found in selected corpus."]
        )
    
    if not valid_citations:
        return (
            "The provided documents do not contain sufficient evidence to answer this question.",
            "insufficient_evidence",
            ["No valid citations could be generated from retrieved evidence."]
        )
    
    # Check if answer claims facts but has no valid citations
    # This is a simple heuristic - in production you might use NLP to detect factual claims
    if valid_citations and "sufficient evidence" not in answer_text.lower():
        # If there are valid citations but the answer doesn't mention them,
        # the model may have forgotten to cite - this is a warning
        pass
    
    return None, "answered", []