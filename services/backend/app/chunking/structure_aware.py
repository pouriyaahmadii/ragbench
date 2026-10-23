import re
from typing import List, Tuple
from dataclasses import dataclass

@dataclass
class TextSegment:
    """Represents a logical segment of text (paragraph, heading, list item, code block, etc.)"""
    text: str
    segment_type: str  # 'heading', 'paragraph', 'list_item', 'code_block', 'table'
    level: int = 0  # For headings: 1-6; for list items: nesting level
    start_char: int = 0
    end_char: int = 0
    raw_text: str = ""  # Original text with markdown markers


def segment_text(text: str) -> List[TextSegment]:
    """
    Segment text into logical units (paragraphs, headings, list items, code blocks).
    
    Args:
        text: Input text to segment
        
    Returns:
        List of TextSegment objects
    """
    if not text or not text.strip():
        return []
    
    segments = []
    lines = text.split('\n')
    char_pos = 0
    
    i = 0
    while i < len(lines):
        line = lines[i]
        line_start = char_pos
        char_pos += len(line) + 1  # +1 for newline
        
        if not line.strip():
            # Empty line - skip but track position
            i += 1
            continue
        
        # Check for headings (markdown style)
        heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if heading_match:
            level = len(heading_match.group(1))
            text = heading_match.group(2).strip()
            segments.append(TextSegment(
                text=text,
                segment_type='heading',
                level=level,
                start_char=line_start,
                end_char=char_pos,
                raw_text=line  # Preserve original with markdown
            ))
            i += 1
            continue
        
        # Check for list items
        list_match = re.match(r'^(\s*)([-*+]|\d+\.)\s+(.+)$', line)
        if list_match:
            indent = len(list_match.group(1))
            marker = list_match.group(2)
            text = list_match.group(3).strip()
            level = indent // 2  # Assuming 2 spaces per indent level
            segments.append(TextSegment(
                text=text,
                segment_type='list_item',
                level=level,
                start_char=line_start,
                end_char=char_pos,
                raw_text=line
            ))
            i += 1
            continue
        
        # Check for code blocks
        if line.strip().startswith('```'):
            # Find end of code block
            code_lines = [line]
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith('```'):
                code_lines.append(lines[j])
                j += 1
            if j < len(lines):
                code_lines.append(lines[j])
                j += 1  # Move past closing ```
            
            code_text = '\n'.join(code_lines)
            segments.append(TextSegment(
                text=code_text,
                segment_type='code_block',
                start_char=line_start,
                end_char=char_pos + sum(len(l) + 1 for l in lines[i:j]) if j <= len(lines) else char_pos,
                raw_text='\n'.join(lines[i:j])
            ))
            i = j
            continue
        
        # Regular paragraph
        # Collect consecutive non-empty, non-special lines
        paragraph_lines = [line]
        j = i + 1
        while j < len(lines) and lines[j].strip() and not is_special_line(lines[j]):
            paragraph_lines.append(lines[j])
            j += 1
        
        paragraph_text = '\n'.join(paragraph_lines).strip()
        if paragraph_text:
            segments.append(TextSegment(
                text=paragraph_text,
                segment_type='paragraph',
                start_char=line_start,
                end_char=char_pos + sum(len(l) + 1 for l in lines[i:j]),
                raw_text='\n'.join(lines[i:j])
            ))
        
        i = j
    
    return segments


def is_special_line(line: str) -> bool:
    """Check if a line is a special markdown element."""
    stripped = line.strip()
    return (
        re.match(r'^#{1,6}\s+', stripped) is not None or  # Heading
        re.match(r'^(\s*)([-*+]|\d+\.)\s+', stripped) is not None or  # List item
        stripped.startswith('```')  # Code block
    )


def chunk_segments(
    segments: List[TextSegment],
    chunk_size: int = 1200,
    overlap: int = 150,
) -> List[Tuple[str, dict]]:
    """
    Chunk text segments into overlapping chunks while preserving segment boundaries where possible.
    
    Args:
        segments: List of TextSegment objects
        chunk_size: Maximum size of each chunk in characters
        overlap: Number of characters to overlap between chunks
        
    Returns:
        List of (chunk_text, metadata) tuples
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0:
        raise ValueError("overlap must be non-negative")
    if overlap >= chunk_size:
        raise ValueError("overlap must be less than chunk_size")
    
    # First, flatten segments into text with metadata mapping
    # Use raw_text (with markdown) for chunking to preserve structure
    full_text_parts = []
    segment_boundaries = []  # (start_char, end_char, segment_info)
    current_pos = 0
    
    for seg in segments:
        seg_text = seg.raw_text if seg.raw_text else seg.text
        start = current_pos
        end = current_pos + len(seg_text)
        full_text_parts.append(seg_text)
        segment_boundaries.append({
            'start': start,
            'end': end,
            'type': seg.segment_type,
            'level': seg.level,
        })
        current_pos = end
    
    full_text = '\n\n'.join(full_text_parts)
    
    if not full_text.strip():
        return []
    
    # Use the fixed-size chunker on the full text, but track positions
    from app.chunking.base import chunk_text
    
    # Custom chunker that returns positions
    chunks_with_pos = _chunk_text_with_positions(full_text, chunk_size, overlap)
    
    # Add segment metadata to each chunk
    result = []
    for chunk_text, chunk_start, chunk_end in chunks_with_pos:
        overlapping_segments = []
        for boundary in segment_boundaries:
            if boundary['start'] < chunk_end and boundary['end'] > chunk_start:
                overlapping_segments.append(boundary)
        
        metadata = {
            'segment_types': [s['type'] for s in overlapping_segments],
            'heading_levels': [s['level'] for s in overlapping_segments if s['type'] == 'heading'],
            'has_code_block': any(s['type'] == 'code_block' for s in overlapping_segments),
            'has_list': any(s['type'] == 'list_item' for s in overlapping_segments),
        }
        
        result.append((chunk_text, metadata))
    
    return result


def _chunk_text_with_positions(text: str, chunk_size: int, overlap: int):
    """
    Chunk text and return (chunk_text, start_pos, end_pos) tuples.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0:
        raise ValueError("overlap must be non-negative")
    if overlap >= chunk_size:
        raise ValueError("overlap must be less than chunk_size")
    
    if not text or not text.strip():
        return []
    
    result = []
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
            result.append((chunk, start, end))
        
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
        if start <= 0 and len(result) > 0:
            break
    
    return result


def structure_aware_chunk(
    text: str,
    chunk_size: int = 1200,
    overlap: int = 150,
) -> List[str]:
    """
    Structure-aware chunking that preserves document structure.
    
    This is a higher-level function that combines segmentation and chunking.
    
    Args:
        text: Input text to chunk
        chunk_size: Maximum size of each chunk in characters
        overlap: Number of characters to overlap between chunks
        
    Returns:
        List of text chunks
    """
    segments = segment_text(text)
    chunked = chunk_segments(segments, chunk_size, overlap)
    return [chunk for chunk, _ in chunked]