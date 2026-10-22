from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import Optional, List
from uuid import UUID
import asyncio

from app.ingestion.service import create_document
from app.ingestion.schemas import (
    DocumentUploadResponse, IngestionJobResponse,
    IngestionStatus as SchemaIngestionStatus
)
from app.config import Settings, get_settings

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


@router.post(
    "/",
    response_model=DocumentUploadResponse,
    status_code=202,
    summary="Upload a document for ingestion",
)
async def upload_document(
    file: UploadFile = File(...),
    corpus_id: Optional[str] = Form(None),
    settings: Settings = Depends(get_settings),
):
    """
    Upload a document for ingestion.
    
    Accepts PDF, TXT, and Markdown files.
    Returns immediately with ingestion job ID for status polling.
    """
    # Read file content
    file_content = await file.read()
    
    # Validate file is not empty
    if not file_content:
        raise HTTPException(
            status_code=400,
            detail="Empty file uploaded"
        )
    
    # Create document and start ingestion
    response = await create_document(
        file_content=file_content,
        filename=file.filename or "unknown",
        content_type=file.content_type,
        settings=settings,
        corpus_id=corpus_id,
    )
    
    return response


@router.get(
    "/",
    response_model=List[dict],
    summary="List documents",
)
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    corpus_id: Optional[str] = Query(None),
    settings: Settings = Depends(get_settings),
):
    """List documents with pagination and filtering."""
    # This would query the database for documents
    # For now, return empty list
    return []


@router.get(
    "/{document_id}",
    response_model=dict,
    summary="Get document details",
)
async def get_document(
    document_id: UUID,
    settings: Settings = Depends(get_settings),
):
    """Get document metadata and versions."""
    # This would query the database for document details
    raise HTTPException(status_code=404, detail="Document not found")


@router.get(
    "/{document_id}/chunks",
    response_model=List[dict],
    summary="Get document chunks",
)
async def get_document_chunks(
    document_id: UUID,
    version_id: Optional[UUID] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    settings: Settings = Depends(get_settings),
):
    """Get chunk metadata for a document."""
    raise HTTPException(status_code=404, detail="Document not found")


@router.delete(
    "/{document_id}",
    status_code=204,
    summary="Delete a document",
)
async def delete_document(
    document_id: UUID,
    settings: Settings = Depends(get_settings),
):
    """Delete a document and all associated data."""
    raise HTTPException(status_code=404, detail="Document not found")


@router.post(
    "/{document_id}/reindex",
    status_code=202,
    summary="Re-index a document",
)
async def reindex_document(
    document_id: UUID,
    settings: Settings = Depends(get_settings),
):
    """Re-index a document with new configuration."""
    raise HTTPException(status_code=404, detail="Document not found")


# Ingestion job status endpoints
@router.get(
    "/jobs/{job_id}",
    response_model=IngestionJobResponse,
    summary="Get ingestion job status",
)
async def get_ingestion_job(
    job_id: UUID,
    settings: Settings = Depends(get_settings),
):
    """Get ingestion job status and progress."""
    raise HTTPException(status_code=404, detail="Job not found")


@router.get(
    "/jobs",
    response_model=List[IngestionJobResponse],
    summary="List ingestion jobs",
)
async def list_ingestion_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    settings: Settings = Depends(get_settings),
):
    """List ingestion jobs with filtering."""
    return []