from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from uuid import UUID


class Citation(BaseModel):
    """A citation linking an answer claim to a source chunk."""
    chunk_id: UUID = Field(description="Unique identifier of the cited chunk")
    document_id: UUID = Field(description="Document identifier")
    document_version_id: UUID = Field(description="Document version identifier")
    page_number: Optional[int] = Field(default=None, description="Page number when available")
    source_title: str = Field(description="Source document title")
    excerpt: str = Field(description="Short supporting excerpt from the chunk")


# Answer status as a Literal type
AnswerStatus = Literal["answered", "insufficient_evidence", "failed"]


class Answer(BaseModel):
    """Structured answer with citations and metadata."""
    answer_id: UUID = Field(description="Unique identifier for this answer")
    question: str = Field(description="The original question")
    answer_text: str = Field(description="Generated answer text")
    status: AnswerStatus = Field(description="Answer status")
    citations: List["Citation"] = Field(default_factory=list, description="Validated citations")
    limitations: List[str] = Field(default_factory=list, description="Limitations or uncertainty notes")
    provider_metadata: dict = Field(default_factory=dict, description="Provider metadata (provider, model, version, prompt_version)")
    latency_metadata: dict = Field(default_factory=dict, description="Latency metadata (retrieval_ms, generation_ms, total_ms)")