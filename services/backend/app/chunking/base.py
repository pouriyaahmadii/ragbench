from typing import List
import hashlib


def chunk_text(
    text: str,
    chunk_size: int = 1200,
    overlap: int = 150,
) -> List[str]:
    """
    Split text into overlapping chunks of specified size.
    
    Args:
        text: Input text to chunk
        chunk_size: Maximum size of each chunk in characters
        overlap: Number of characters to overlap between chunks
        
    Returns:
        List of text chunks
        
    Raises:
        ValueError: If chunk_size <= 0 or overlap >= chunk_size
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0:
        raise ValueError("overlap must be non-negative")
    if overlap >= chunk_size:
        raise ValueError("overlap must be less than chunk_size")
    
    if not text or not text.strip():
        return []
    
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = min(start + chunk_size, text_len)
        
        # Try to break at a natural boundary (space, newline, punctuation)
        if end < text_len:
            # Look for a good break point within the last 100 characters
            search_start = max(start + chunk_size - 100, start)
            break_point = -1
            
            # Priority: double newline > single newline > space > punctuation
            for delimiter in ['\n\n', '\n', '. ', '! ', '? ', ', ', ' ']:
                pos = text.rfind(delimiter, search_start, end)
                if pos != -1:
                    break_point = pos + len(delimiter)
                    break
            
            if break_point != -1 and break_point > start:
                end = break_point
        
        chunk = text[start:end].strip()
        if chunk:  # Only add non-empty chunks
            chunks.append(chunk)
        
        # If we've reached the end of the text, we're done
        if end >= text_len:
            break
        
        # Move start position for next chunk
        # Only advance if we're making progress
        next_start = end - overlap
        if next_start <= start:
            # Not making progress, move to end to finish
            start = text_len
        else:
            start = next_start
        
        if start >= text_len:
            break
        
        # Safety check to prevent infinite loop
        if start <= 0 and len(chunks) > 0:
            break
    
    return chunks


def compute_text_hash(text: str) -> str:
    """Compute SHA-256 hash of text content."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def compute_chunker_config_hash(chunk_size: int, overlap: int) -> str:
    """Compute hash of chunking configuration for versioning."""
    config_str = f"fixed:{chunk_size}:{overlap}"
    return hashlib.sha256(config_str.encode()).hexdigest()[:16]