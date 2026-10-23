import pytest
import hashlib
from app.chunking.base import (
    chunk_text,
    compute_text_hash,
    compute_chunker_config_hash,
)
from app.chunking.structure_aware import (
    segment_text,
    chunk_segments,
    structure_aware_chunk,
    TextSegment,
)


class TestFixedSizeChunking:
    """Tests for fixed-size chunking with overlap."""

    def test_basic_chunking(self):
        """Test basic chunking of a simple text."""
        text = "A" * 2500  # 2500 chars
        chunks = chunk_text(text, chunk_size=1000, overlap=100)
        
        assert len(chunks) == 3  # 2500 / (1000-100) ≈ 2.78 -> 3 chunks
        assert all(len(c) <= 1000 for c in chunks)
        assert all(len(c) > 0 for c in chunks)

    def test_short_text_single_chunk(self):
        """Test that short text produces a single chunk."""
        text = "Hello world!"
        chunks = chunk_text(text, chunk_size=1000, overlap=100)
        
        assert len(chunks) == 1
        assert chunks[0] == "Hello world!"

    def test_exact_chunk_size(self):
        """Test text that exactly matches chunk size."""
        text = "A" * 1000
        chunks = chunk_text(text, chunk_size=1000, overlap=100)
        
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_empty_text(self):
        """Test empty text returns empty list."""
        chunks = chunk_text("", chunk_size=1000, overlap=100)
        assert chunks == []

    def test_whitespace_only(self):
        """Test whitespace-only text returns empty list."""
        chunks = chunk_text("   \n\n  \t  ", chunk_size=1000, overlap=100)
        assert chunks == []

    def test_overlap_validation(self):
        """Test that overlap >= chunk_size raises ValueError."""
        with pytest.raises(ValueError, match="overlap must be less than chunk_size"):
            chunk_text("test", chunk_size=100, overlap=100)
        
        with pytest.raises(ValueError, match="overlap must be less than chunk_size"):
            chunk_text("test", chunk_size=100, overlap=150)

    def test_zero_chunk_size_raises(self):
        """Test that zero chunk_size raises ValueError."""
        with pytest.raises(ValueError, match="chunk_size must be positive"):
            chunk_text("test", chunk_size=0, overlap=10)

    def test_negative_overlap_raises(self):
        """Test that negative overlap raises ValueError."""
        with pytest.raises(ValueError, match="overlap must be non-negative"):
            chunk_text("test", chunk_size=100, overlap=-10)

    def test_overlap_behavior(self):
        """Test that overlap is correctly applied."""
        text = "A" * 2000
        chunks = chunk_text(text, chunk_size=1000, overlap=200)
        
        # Should have 3 chunks with 200 char overlap
        assert len(chunks) == 3
        # Check overlap between consecutive chunks
        for i in range(len(chunks) - 1):
            overlap_region = chunks[i][-200:]
            next_start = chunks[i + 1][:200]
            assert overlap_region == next_start

    def test_boundary_detection(self):
        """Test that chunker prefers natural boundaries."""
        # Create text long enough to require chunking, with clear paragraph boundaries
        paragraph = "This is a test paragraph with enough content to fill a chunk. " * 3
        text = f"{paragraph}\n\n{paragraph}\n\n{paragraph}"
        chunks = chunk_text(text, chunk_size=200, overlap=20)
        
        # Should break at paragraph boundaries when possible
        assert len(chunks) >= 2
        # First chunk should end at a natural boundary (period or newline)
        assert chunks[0].endswith(".") or chunks[0].endswith("\n")

    def test_unicode_handling(self):
        """Test chunking handles Unicode correctly."""
        text = "Hello 世界! " * 100  # Mix of ASCII and Unicode
        chunks = chunk_text(text, chunk_size=500, overlap=50)
        
        assert len(chunks) > 0
        assert all(len(c) <= 500 for c in chunks)
        # Verify Unicode is preserved
        full = "".join(chunks)
        assert "世界" in full

    def test_rtl_text(self):
        """Test chunking handles RTL text correctly."""
        text = "مرحبا بالعالم " * 50  # Arabic text
        chunks = chunk_text(text, chunk_size=500, overlap=50)
        
        assert len(chunks) > 0
        assert all(len(c) <= 500 for c in chunks)

    def test_stable_chunk_ids(self):
        """Test that same input produces same chunks."""
        text = "Test content for stability. " * 50
        chunks1 = chunk_text(text, chunk_size=500, overlap=50)
        chunks2 = chunk_text(text, chunk_size=500, overlap=50)
        
        assert chunks1 == chunks2


class TestTextHash:
    """Tests for text hashing functions."""

    def test_compute_text_hash(self):
        """Test SHA-256 hash computation."""
        text = "Hello world!"
        hash1 = compute_text_hash(text)
        hash2 = compute_text_hash(text)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length

    def test_different_texts_different_hashes(self):
        """Test that different texts produce different hashes."""
        hash1 = compute_text_hash("text one")
        hash2 = compute_text_hash("text two")
        
        assert hash1 != hash2

    def test_empty_string_hash(self):
        """Test hash of empty string."""
        hash_val = compute_text_hash("")
        expected = hashlib.sha256(b"").hexdigest()
        assert hash_val == expected


class TestChunkerConfigHash:
    """Tests for chunker configuration hashing."""

    def test_config_hash_consistency(self):
        """Test that same config produces same hash."""
        hash1 = compute_chunker_config_hash(1200, 150)
        hash2 = compute_chunker_config_hash(1200, 150)
        
        assert hash1 == hash2

    def test_different_configs_different_hashes(self):
        """Test that different configs produce different hashes."""
        hash1 = compute_chunker_config_hash(1200, 150)
        hash2 = compute_chunker_config_hash(800, 100)
        
        assert hash1 != hash2


class TestSegmentation:
    """Tests for text segmentation."""

    def test_heading_detection(self):
        """Test heading detection."""
        text = "# Heading 1\n\n## Heading 2\n\nParagraph text."
        segments = segment_text(text)
        
        headings = [s for s in segments if s.segment_type == 'heading']
        assert len(headings) == 2
        assert headings[0].level == 1
        assert headings[1].level == 2
        assert headings[0].text == "Heading 1"
        assert headings[1].text == "Heading 2"

    def test_list_item_detection(self):
        """Test list item detection."""
        text = "- Item 1\n- Item 2\n- Item 3"
        segments = segment_text(text)
        
        list_items = [s for s in segments if s.segment_type == 'list_item']
        assert len(list_items) == 3

    def test_numbered_list_detection(self):
        """Test numbered list detection."""
        text = "1. First item\n2. Second item"
        segments = segment_text(text)
        
        list_items = [s for s in segments if s.segment_type == 'list_item']
        assert len(list_items) == 2

    def test_code_block_detection(self):
        """Test code block detection."""
        text = "Here is code:\n```python\ndef hello():\n    print('hello')\n```\nDone."
        segments = segment_text(text)
        
        code_blocks = [s for s in segments if s.segment_type == 'code_block']
        assert len(code_blocks) == 1
        assert 'def hello()' in code_blocks[0].text

    def test_paragraph_segmentation(self):
        """Test paragraph segmentation."""
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        segments = segment_text(text)
        
        paragraphs = [s for s in segments if s.segment_type == 'paragraph']
        assert len(paragraphs) == 3

    def test_mixed_content(self):
        """Test mixed content segmentation."""
        text = """# Title
        
        Introduction paragraph.
        
        - Item 1
        - Item 2
        
        ## Subsection
        
        Content here."""
        segments = segment_text(text)
        
        types = [s.segment_type for s in segments]
        assert 'heading' in types
        assert 'paragraph' in types
        assert 'list_item' in types

    def test_empty_text_segmentation(self):
        """Test segmentation of empty text."""
        segments = segment_text("")
        assert segments == []

    def test_whitespace_only_segmentation(self):
        """Test segmentation of whitespace only."""
        segments = segment_text("   \n\n  \t  ")
        assert segments == []


class TestStructureAwareChunking:
    """Tests for structure-aware chunking."""

    def test_basic_structure_aware_chunking(self):
        """Test basic structure-aware chunking."""
        text = "# Title\n\n" + "Paragraph content. " * 100
        chunks = structure_aware_chunk(text, chunk_size=500, overlap=50)
        
        assert len(chunks) > 0
        assert all(len(c) <= 500 for c in chunks)

    def test_structure_preserves_headings(self):
        """Test that headings are preserved in chunks."""
        text = "# Main Title\n\n## Section 1\n\nContent here.\n\n## Section 2\n\nMore content."
        chunks = structure_aware_chunk(text, chunk_size=200, overlap=20)
        
        # Should have multiple chunks
        assert len(chunks) >= 2
        # At least one chunk should contain heading
        assert any('#' in c for c in chunks)

    def test_list_items_preserved(self):
        """Test that list items are preserved in chunks."""
        text = "Items:\n- Item 1\n- Item 2\n- Item 3\n\nEnd of list."
        chunks = structure_aware_chunk(text, chunk_size=100, overlap=20)
        
        assert len(chunks) >= 1
        # At least one chunk should contain list markers
        assert any('-' in c for c in chunks)

    def test_code_blocks_preserved(self):
        """Test that code blocks are preserved."""
        text = """Code example:
```python
def hello():
    print("Hello, World!")
```
End of example."""
        chunks = structure_aware_chunk(text, chunk_size=200, overlap=20)
        
        assert len(chunks) >= 1
        # Code block should be preserved in some chunk
        assert any('```' in c or 'def hello' in c for c in chunks)

    def test_short_text_single_chunk(self):
        """Test short text produces single chunk."""
        text = "Short text."
        chunks = structure_aware_chunk(text, chunk_size=1000, overlap=100)
        
        assert len(chunks) == 1
        assert chunks[0] == "Short text."

    def test_empty_text(self):
        """Test empty text returns empty list."""
        chunks = structure_aware_chunk("", chunk_size=1000, overlap=100)
        assert chunks == []

    def test_overlap_preserved(self):
        """Test that overlap is maintained in structure-aware chunking."""
        text = "Content. " * 200
        chunks = structure_aware_chunk(text, chunk_size=500, overlap=100)
        
        assert len(chunks) >= 2
        # Check overlap between consecutive chunks - there should be some overlap
        for i in range(len(chunks) - 1):
            # Check that there's at least 30 characters of overlap (allowing for boundary adjustments)
            overlap_found = False
            for overlap_len in range(30, 51):
                if chunks[i].endswith(chunks[i + 1][:overlap_len]):
                    overlap_found = True
                    break
            assert overlap_found, f"No sufficient overlap between chunk {i} and {i+1}"

    def test_unicode_in_structure_aware(self):
        """Test structure-aware chunking with Unicode."""
        text = "# عنوان\n\nمحتوى باللغة العربية. " * 50
        chunks = structure_aware_chunk(text, chunk_size=500, overlap=50)
        
        assert len(chunks) > 0
        assert all(len(c) <= 500 for c in chunks)
        # Arabic should be preserved
        assert any('عربي' in c for c in chunks)

    def test_rtl_text_structure(self):
        """Test RTL text with structure."""
        text = "# عنوان رئيسي\n\nفقرة باللغة العربية.\n\n- عنصر 1\n- عنصر 2"
        chunks = structure_aware_chunk(text, chunk_size=200, overlap=20)
        
        assert len(chunks) >= 1
        # RTL content should be preserved
        full = "".join(chunks)
        assert "رئيسي" in full or "عربي" in full


class TestChunkMetadata:
    """Tests for chunk metadata creation."""

    def test_compute_embedding_config_hash(self):
        """Test embedding config hash computation."""
        from app.chunking.metadata import compute_embedding_config_hash
        
        hash1 = compute_embedding_config_hash("openai", "text-embedding-3-small", "1", 1536)
        hash2 = compute_embedding_config_hash("openai", "text-embedding-3-small", "1", 1536)
        
        assert hash1 == hash2
        assert len(hash1) == 16  # Truncated to 16 chars

    def test_different_embedding_configs_different_hashes(self):
        """Test different embedding configs produce different hashes."""
        from app.chunking.metadata import compute_embedding_config_hash
        
        hash1 = compute_embedding_config_hash("openai", "text-embedding-3-small", "1", 1536)
        hash2 = compute_embedding_config_hash("openai", "text-embedding-3-large", "1", 3072)
        
        assert hash1 != hash2