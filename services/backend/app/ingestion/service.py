from typing import Optional
from app.ingestion.pipeline import IngestionService
from app.config import Settings
from app.ingestion.schemas import DocumentUploadResponse


async def create_document(
    file_content: bytes,
    filename: str,
    content_type: str,
    settings: Settings,
    corpus_id: Optional[str] = None,
) -> DocumentUploadResponse:
    """Convenience function to create a document."""
    service = IngestionService(settings)
    await service.initialize()
    return await service.create_document(file_content, filename, content_type, corpus_id)