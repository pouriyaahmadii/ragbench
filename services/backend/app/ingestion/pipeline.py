import hashlib
import uuid
import asyncio
from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import (
    Document, DocumentVersion, IngestionJob, Chunk, IndexVersion,
    DocumentStatus, IngestionStatus, IngestionJobState, IngestionJobStage
)
from app.ingestion.validator import (
    validate_upload_file, get_mime_type_from_content, validate_filename_safety
)
from app.ingestion.parsers import parse_document, ParsedDocument
from app.ingestion.schemas import (
    IngestionStatus as SchemaIngestionStatus,
    IngestionJobResponse, DocumentUploadResponse, ErrorCategory
)
from app.config import Settings
from app.providers.factory import get_embedding_provider, get_provider_factory
from app.providers.protocols import EmbeddingProvider
from app.chunking.base import chunk_text
from app.chunking.metadata import create_chunk_metadata
from app.vectorstore.client import get_qdrant_client
from app.vectorstore.collections import ensure_collection_exists, upsert_vectors
from app.db.session import get_session
from app.ingestion.schemas import (
    IngestionStatus as SchemaIngestionStatus,
    IngestionJobResponse, DocumentUploadResponse, ErrorCategory
)
from app.config import Settings
from app.providers.factory import get_embedding_provider, get_provider_factory
from app.providers.protocols import EmbeddingProvider
from app.vectorstore.client import get_qdrant_client
from app.vectorstore.collections import ensure_collection_exists, upsert_vectors
import logging

logger = logging.getLogger(__name__)


class IngestionService:
    """Service for handling document ingestion pipeline."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.embedding_provider: Optional[EmbeddingProvider] = None
    
    async def initialize(self):
        """Initialize the ingestion service."""
        factory = get_provider_factory(self.settings)
        self.embedding_provider = factory.get_embedding_provider()
    
    async def create_document(
        self,
        file_content: bytes,
        filename: str,
        content_type: str,
        corpus_id: Optional[str] = None,
    ):
        """
        Create a new document and start ingestion pipeline.
        
        This is the main entry point for document upload.
        """
        # Generate IDs
        document_id = str(uuid.uuid4())
        document_version_id = str(uuid.uuid4())
        ingestion_job_id = str(uuid.uuid4())
        
        # Generate safe storage name
        safe_filename = validate_filename_safety(filename)
        storage_name = f"{document_version_id}_{safe_filename}"
        storage_path = f"uploads/{corpus_id or 'default'}/{storage_name}"
        
        # Compute content hash
        content_hash = hashlib.sha256(file_content).hexdigest()
        
        # Determine MIME type
        mime_type = content_type or get_mime_type_from_content(file_content[:8192], filename)
        
        # Create document record
        from app.db.session import get_session
        from app.models import (
            Document, DocumentVersion, IngestionJob,
            DocumentStatus, IngestionStatus, IngestionJobState, IngestionJobStage
        )
        from app.ingestion.schemas import (
            IngestionStatus as SchemaIngestionStatus,
            DocumentUploadResponse
        )
        
        async with get_session() as session:
            # Check for duplicate content
            existing = await session.execute(
                select(Document).where(Document.content_hash == content_hash)
            )
            existing_doc = existing.scalar_one_or_none()
            
            if existing_doc:
                # Return existing document info
                from app.ingestion.schemas import DocumentUploadResponse, IngestionStatus as SchemaIngestionStatus
                return DocumentUploadResponse(
                    document_id=str(existing_doc.id),
                    document_version_id=str(existing_doc.versions[0].id) if existing_doc.versions else "",
                    ingestion_job_id="",
                    status=SchemaIngestionStatus.READY,
                    message="Document with identical content already exists"
                )
            
            # Create document
            document = Document(
                id=uuid.UUID(document_id),
                display_name=filename,
                media_type=mime_type,
                status=DocumentStatus.ACTIVE,
                content_hash=content_hash,
                size_bytes=len(file_content),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            
            # Create document version
            document_version = DocumentVersion(
                id=uuid.UUID(document_version_id),
                document_id=uuid.UUID(document_id),
                version_number=1,
                parser_version="1.0",
                parser_metadata={},
                content_hash=content_hash,
                storage_ref=storage_path,
                page_count=0,
                ingestion_status=IngestionStatus.UPLOADED,
                created_at=datetime.utcnow(),
            )
            
            # Create ingestion job
            ingestion_job = IngestionJob(
                id=uuid.UUID(ingestion_job_id),
                document_version_id=uuid.UUID(document_version_id),
                attempt=1,
                state=IngestionJobState.PENDING,
                started_at=datetime.utcnow(),
            )
            
            session.add_all([document, document_version, ingestion_job])
            await session.commit()
        
        # Start async ingestion pipeline
        asyncio.create_task(self._run_ingestion_pipeline(
            ingestion_job_id=ingestion_job_id,
            document_version_id=document_version_id,
            file_content=file_content,
            filename=filename,
            mime_type=mime_type,
            storage_path=storage_path,
            corpus_id=corpus_id,
        ))
        
        from app.ingestion.schemas import DocumentUploadResponse, IngestionStatus as SchemaIngestionStatus
        return DocumentUploadResponse(
            document_id=document_id,
            document_version_id=document_version_id,
            ingestion_job_id=ingestion_job_id,
            status=SchemaIngestionStatus.VALIDATING,
            message="Document accepted for processing"
        )
    
    async def _run_ingestion_pipeline(
        self,
        ingestion_job_id: str,
        document_version_id: str,
        file_content: bytes,
        filename: str,
        mime_type: str,
        storage_path: str,
        corpus_id: Optional[str],
    ):
        """Run the complete ingestion pipeline asynchronously."""
        from app.db.session import get_session
        from app.models import (
            Document, DocumentVersion, IngestionJob, Chunk, IndexVersion,
            DocumentStatus, IngestionStatus, IngestionJobState, IngestionJobStage
        )
        from app.ingestion.schemas import (
            IngestionStatus as SchemaIngestionStatus,
            IngestionJobResponse, DocumentUploadResponse, ErrorCategory
        )
        
        async with get_session() as session:
            try:
                # Get ingestion job
                job = await session.get(IngestionJob, uuid.UUID(ingestion_job_id))
                if not job:
                    logger.error(f"Ingestion job {ingestion_job_id} not found")
                    return
                
                # Stage 1: Validating
                await self._update_job_status(session, job, IngestionJobState.RUNNING, IngestionJobStage.VALIDATING)
                
                # Stage 2: Parsing
                await self._update_job_status(session, job, IngestionJobState.RUNNING, IngestionJobStage.PARSING)
                
                parsed_doc = parse_document(file_content, mime_type, self.settings)
                
                # Update document version with parsing results
                doc_version = await session.get(DocumentVersion, uuid.UUID(document_version_id))
                if doc_version:
                    doc_version.page_count = parsed_doc.page_count
                    doc_version.parser_metadata = parsed_doc.parser_metadata
                    doc_version.ingestion_status = IngestionStatus.PARSING
                    await session.commit()
                
                # Stage 3: Chunking
                await self._update_job_status(session, job, IngestionJobState.RUNNING, IngestionJobStage.CHUNKING)
                
                from app.chunking.base import chunk_text
                from app.chunking.metadata import create_chunk_metadata
                
                all_chunks = []
                for page in parsed_doc.pages:
                    if page.text.strip():
                        chunks = chunk_text(
                            page.text,
                            chunk_size=self.settings.CHUNK_SIZE_CHARS,
                            overlap=self.settings.CHUNK_OVERLAP_CHARS,
                        )
                        
                        for i, chunk_text in enumerate(chunks):
                            chunk_meta = create_chunk_metadata(
                                chunk_text=chunk_text,
                                document_version_id=uuid.UUID(document_version_id),
                                corpus_id=uuid.UUID(corpus_id) if corpus_id else uuid.uuid4(),
                                chunk_index=len(all_chunks),
                                page_number=page.page_number,
                                chunker_config_hash="",
                                embedding_config_hash="",
                            )
                            all_chunks.append((chunk_text, chunk_meta))
                
                if not all_chunks:
                    # No chunks created - document might be empty or all whitespace
                    await self._mark_job_failed(
                        session, job,
                        "No text content could be extracted from document",
                        ErrorCategory.PARSING
                    )
                    return
                
                # Stage 4: Embedding
                await self._update_job_status(session, job, IngestionJobState.RUNNING, IngestionJobStage.EMBEDDING)
                
                # Generate embeddings
                chunk_texts = [chunk[0] for chunk in all_chunks]
                embedding_result = await self.embedding_provider.embed(chunk_texts)
                
                # Validate embedding dimensions
                if len(embedding_result.vectors) != len(chunk_texts):
                    raise ValueError("Embedding count mismatch")
                
                for vector in embedding_result.vectors:
                    if len(vector) != self.embedding_provider.dimension:
                        raise ValueError(f"Embedding dimension mismatch: expected {self.embedding_provider.dimension}, got {len(vector)}")
                
                # Stage 5: Indexing
                await self._update_job_status(session, job, IngestionJobState.RUNNING, IngestionJobStage.INDEXING)
                
                # Get or create index version
                index_version = await self._get_or_create_index_version(
                    session, corpus_id, embedding_result.metadata
                )
                
                # Upsert vectors to Qdrant
                qdrant_client = get_qdrant_client()
                await ensure_collection_exists(qdrant_client, index_version.vector_collection, self.embedding_provider.dimension)
                
                # Prepare vectors for upsert
                vectors_to_upsert = []
                for i, (chunk_text, chunk_meta) in enumerate(all_chunks):
                    vector = embedding_result.vectors[i]
                    vectors_to_upsert.append({
                        "id": str(chunk_meta.id),
                        "vector": vector,
                        "payload": {
                            "chunk_id": str(chunk_meta.id),
                            "document_id": str(chunk_meta.document_version_id),
                            "document_version_id": str(chunk_meta.document_version_id),
                            "corpus_id": str(chunk_meta.corpus_id),
                            "page_number": chunk_meta.page_number,
                            "source_title": filename,
                            "text_excerpt": chunk_text[:200],
                            "chunk_index": chunk_meta.chunk_index,
                        }
                    })
                
                await upsert_vectors(qdrant_client, index_version.vector_collection, vectors_to_upsert)
                
                # Store chunk metadata in PostgreSQL
                from app.models import Chunk
                for chunk_text, chunk_meta in all_chunks:
                    chunk_meta.index_version = index_version.id
                    chunk_meta.embedding_provider = embedding_result.metadata.provider
                    chunk_meta.embedding_model = embedding_result.metadata.model
                    chunk_meta.embedding_version = embedding_result.metadata.version
                    chunk_meta.embedding_dimension = embedding_result.metadata.dimension
                    
                    chunk = Chunk(
                        id=chunk_meta.id,
                        document_version_id=chunk_meta.document_version_id,
                        corpus_id=chunk_meta.corpus_id,
                        chunk_index=chunk_meta.chunk_index,
                        text_hash=chunk_meta.text_hash,
                        page_number=chunk_meta.page_number,
                        start_offset=chunk_meta.start_offset,
                        end_offset=chunk_meta.end_offset,
                        chunker_config_hash=chunk_meta.chunker_config_hash,
                        embedding_provider=chunk_meta.embedding_provider,
                        embedding_model=chunk_meta.embedding_model,
                        embedding_version=chunk_meta.embedding_version,
                        embedding_dimension=chunk_meta.embedding_dimension,
                        index_version=chunk_meta.index_version,
                    )
                    session.add(chunk)
                
                # Stage 6: Finalizing
                await self._update_job_status(session, job, IngestionJobState.RUNNING, IngestionJobStage.INDEXING)
                
                # Update document version to ready
                if doc_version:
                    doc_version.ingestion_status = IngestionStatus.READY
                    doc_version.page_count = parsed_doc.page_count
                    await session.commit()
                
                # Mark job as succeeded
                await self._update_job_status(
                    session, job, IngestionJobState.SUCCEEDED, IngestionJobStage.FINALIZING
                )
                job.ended_at = datetime.utcnow()
                await session.commit()
                
                logger.info(f"Ingestion job {ingestion_job_id} completed successfully")
                
            except Exception as e:
                logger.exception(f"Ingestion job {ingestion_job_id} failed: {e}")
                await self._mark_job_failed(
                    session, job if 'job' in locals() else None,
                    str(e),
                    ErrorCategory.INTERNAL
                )
    
    async def _update_job_status(
        self,
        session: AsyncSession,
        job: IngestionJob,
        state: IngestionJobState,
        stage: Optional[IngestionJobStage] = None,
    ):
        """Update ingestion job status."""
        job.state = state
        if stage:
            job.stage = stage
        if state in (IngestionJobState.SUCCEEDED, IngestionJobState.FAILED, IngestionJobState.CANCELLED):
            job.ended_at = datetime.utcnow()
        await session.commit()
    
    async def _mark_job_failed(
        self,
        session: AsyncSession,
        job: Optional[IngestionJob],
        error_message: str,
        error_category: ErrorCategory,
    ):
        """Mark ingestion job as failed."""
        if not job:
            return
        
        job.state = IngestionJobState.FAILED
        job.ended_at = datetime.utcnow()
        job.error_category = error_category
        job.user_message = f"Ingestion failed: {error_message}"
        await session.commit()
        logger.error(f"Ingestion job failed: {error_message}")
    
    async def _get_or_create_index_version(
        self,
        session: AsyncSession,
        corpus_id: Optional[str],
        embedding_metadata: dict,
    ):
        """Get or create index version for the given configuration."""
        from app.models import IndexVersion, IndexStatus
        import uuid
        
        index_version = IndexVersion(
            id=uuid.uuid4(),
            corpus_id=uuid.UUID(corpus_id) if corpus_id else uuid.uuid4(),
            chunking_config_hash="",
            embedding_provider=embedding_metadata.get("provider", "mock"),
            embedding_model=embedding_metadata.get("model", "mock"),
            embedding_version=embedding_metadata.get("version", "1.0"),
            embedding_dimension=embedding_metadata.get("dimension", 384),
            vector_collection=f"corpus_{corpus_id or 'default'}",
            status=IndexStatus.READY,
            created_at=datetime.utcnow(),
        )
        session.add(index_version)
        await session.commit()
        return index_version