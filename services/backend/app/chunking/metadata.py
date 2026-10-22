import uuid
from dataclasses import dataclass
from typing import Optional
from app.chunking.base import compute_text_hash, compute_chunker_config_hash
from app.config import Settings


@dataclass
class ChunkMetadata:
    id: uuid.UUID
    document_version_id: uuid.UUID
    corpus_id: uuid.UUID
    chunk_index: int
    text: str
    text_hash: str
    page_number: Optional[int]
    start_offset: Optional[int]
    end_offset: Optional[int]
    chunker_config_hash: str
    embedding_provider: str = ""
    embedding_model: str = ""
    embedding_version: str = ""
    embedding_dimension: int = 0
    index_version: uuid.UUID = None


def create_chunk_metadata(
    chunk_text: str,
    document_version_id: uuid.UUID,
    corpus_id: uuid.UUID,
    chunk_index: int,
    page_number: Optional[int] = None,
    start_offset: Optional[int] = None,
    end_offset: Optional[int] = None,
    chunker_config_hash: str = "",
    embedding_config_hash: str = "",
) -> tuple:
    """
    Create chunk metadata and return (chunk_text, ChunkMetadata).
    
    Returns:
        Tuple of (chunk_text, ChunkMetadata)
    """
    chunk_id = uuid.uuid5(
        uuid.NAMESPACE_DNS,
        f"{document_version_id}:{chunk_index}:{chunker_config_hash}"
    )
    
    text_hash = hashlib.sha256(chunk_text.encode('utf-8')).hexdigest()
    
    chunk_meta = ChunkMetadata(
        id=chunk_id,
        document_version_id=document_version_id,
        corpus_id=corpus_id,
        chunk_index=chunk_index,
        text=chunk_text,
        text_hash=text_hash,
        page_number=page_number,
        start_offset=start_offset,
        end_offset=end_offset,
        chunker_config_hash=chunker_config_hash,
        embedding_provider="",
        embedding_model="",
        embedding_version="",
        embedding_dimension=0,
        index_version=None,
    )
    
    return chunk_text, chunk_meta


def compute_chunker_config_hash(chunk_size: int, overlap: int) -> str:
    """Compute hash of chunking configuration for versioning."""
    import hashlib
    config_str = f"fixed:{chunk_size}:{overlap}"
    return hashlib.sha256(config_str.encode()).hexdigest()[:16]


def compute_embedding_config_hash(
    provider: str,
    model: str,
    version: str,
    dimension: int,
) -> str:
    """Compute hash of embedding configuration for versioning."""
    import hashlib
    config_str = f"{provider}:{model}:{version}:{dimension}"
    return hashlib.sha256(config_str.encode()).hexdigest()[:16]