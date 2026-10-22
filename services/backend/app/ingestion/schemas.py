import enum
from typing import Optional
from pydantic import BaseModel, Field


class IngestionStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    VALIDATING = "validating"
    PARSING = "parsing"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    INDEXING = "indexing"
    READY = "ready"
    REJECTED = "rejected"
    FAILED = "failed"
    CANCELLED = "cancelled"
    READY_WITH_WARNINGS = "ready_with_warnings"


class ErrorCategory(str, enum.Enum):
    VALIDATION = "validation"
    PARSING = "parsing"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    INDEXING = "indexing"
    INTERNAL = "internal"
    TIMEOUT = "timeout"
    RESOURCE = "resource"


class IngestionJobCreate(BaseModel):
    document_version_id: str
    attempt: int = 1


class IngestionJobUpdate(BaseModel):
    state: Optional[str] = None
    stage: Optional[str] = None
    error_category: Optional[ErrorCategory] = None
    user_message: Optional[str] = None
    technical_details: dict = Field(default_factory=dict)


class IngestionJobResponse(BaseModel):
    id: str
    document_version_id: str
    attempt: int
    state: str
    stage: Optional[str] = None
    started_at: str
    ended_at: Optional[str] = None
    error_category: Optional[str] = None
    user_message: Optional[str] = None
    technical_details: dict = Field(default_factory=dict)


class DocumentUploadResponse(BaseModel):
    document_id: str
    document_version_id: str
    ingestion_job_id: str
    status: IngestionStatus
    message: str