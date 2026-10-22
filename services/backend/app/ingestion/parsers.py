import io
import re
from typing import List, Optional
from dataclasses import dataclass
import pdfplumber
from app.config import Settings


@dataclass
class PageContent:
    page_number: int
    text: str
    char_count: int
    metadata: dict


@dataclass
class ParsedDocument:
    pages: List[PageContent]
    page_count: int
    total_chars: int
    parser_metadata: dict
    parser_version: str


class ParserError(Exception):
    """Raised when parsing fails."""

    def __init__(self, message: str, category: str = "parsing"):
        self.message = message
        self.category = category
        super().__init__(message)


def normalize_text(text: str) -> str:
    """Normalize line endings and whitespace while preserving structure."""
    if not text:
        return ""
    
    # Normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Remove trailing whitespace from each line
    lines = text.split('\n')
    lines = [line.rstrip() for line in lines]
    
    # Collapse multiple blank lines to maximum 2 (preserving paragraph breaks)
    result = []
    blank_count = 0
    for line in lines:
        if line == "":
            blank_count += 1
            if blank_count <= 2:
                result.append(line)
        else:
            blank_count = 0
            result.append(line)
    
    return '\n'.join(result)


def parse_pdf(file_content: bytes, settings: Settings) -> ParsedDocument:
    """Parse PDF file and extract text with page metadata."""
    pages = []
    total_chars = 0
    
    try:
        with pdfplumber.open(io.BytesIO(file_content)) as pdf:
            # Check page count limit
            if len(pdf.pages) > settings.MAX_PDF_PAGES:
                raise ParserError(
                    f"PDF has {len(pdf.pages)} pages, exceeds maximum of {settings.MAX_PDF_PAGES}",
                    category="parsing"
                )
            
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                text = normalize_text(text)
                char_count = len(text)
                
                # Check per-page char limit
                if char_count > settings.MAX_EXTRACTED_CHARS:
                    raise ParserError(
                        f"Page {i+1} has {char_count} characters, exceeds maximum of {settings.MAX_EXTRACTED_CHARS}",
                        category="parsing"
                    )
                
                total_chars += char_count
                
                # Check total extracted chars limit
                if total_chars > settings.MAX_EXTRACTED_CHARS:
                    raise ParserError(
                        f"Total extracted characters {total_chars} exceeds maximum of {settings.MAX_EXTRACTED_CHARS}",
                        category="parsing"
                    )
                
                pages.append(PageContent(
                    page_number=i + 1,
                    text=text,
                    char_count=char_count,
                    metadata={
                        "width": page.width,
                        "height": page.height,
                        "rotation": page.rotation,
                    }
                ))
        
        return ParsedDocument(
            pages=pages,
            page_count=len(pages),
            total_chars=total_chars,
            parser_metadata={
                "parser": "pdfplumber",
                "total_pages": len(pages),
            },
            parser_version="1.0"
        )
        
    except pdfplumber.PDFSyntaxError as e:
        raise ParserError(f"PDF syntax error: {str(e)}", category="parsing")
    except Exception as e:
        if isinstance(e, ParserError):
            raise
        raise ParserError(f"PDF parsing failed: {str(e)}", category="parsing")


def parse_text(file_content: bytes, settings: Settings) -> ParsedDocument:
    """Parse plain text file."""
    try:
        # Try to decode as UTF-8
        text = file_content.decode('utf-8')
    except UnicodeDecodeError:
        # Try other encodings
        for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
            try:
                text = file_content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise ParserError("Unable to decode text file with any supported encoding", category="parsing")
    
    text = normalize_text(text)
    char_count = len(text)
    
    if char_count > settings.MAX_EXTRACTED_CHARS:
        raise ParserError(
            f"Text file has {char_count} characters, exceeds maximum of {settings.MAX_EXTRACTED_CHARS}",
            category="parsing"
        )
    
    if char_count == 0:
        raise ParserError("Text file is empty", category="parsing")
    
    return ParsedDocument(
        pages=[
            PageContent(
                page_number=1,
                text=text,
                char_count=char_count,
                metadata={}
            )
        ],
        page_count=1,
        total_chars=char_count,
        parser_metadata={
            "parser": "text",
            "encoding": "utf-8",
        },
        parser_version="1.0"
    )


def parse_markdown(file_content: bytes, settings: Settings) -> ParsedDocument:
    """Parse Markdown file, preserving structure."""
    try:
        text = file_content.decode('utf-8')
    except UnicodeDecodeError:
        for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
            try:
                text = file_content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise ParserError("Unable to decode Markdown file with any supported encoding", category="parsing")
    
    text = normalize_text(text)
    char_count = len(text)
    
    if char_count > settings.MAX_EXTRACTED_CHARS:
        raise ParserError(
            f"Markdown file has {char_count} characters, exceeds maximum of {settings.MAX_EXTRACTED_CHARS}",
            category="parsing"
        )
    
    if char_count == 0:
        raise ParserError("Markdown file is empty", category="parsing")
    
    # Simple structure detection - count headers
    header_count = len(re.findall(r'^#{1,6}\s+.+$', text, re.MULTILINE))
    
    return ParsedDocument(
        pages=[
            PageContent(
                page_number=1,
                text=text,
                char_count=char_count,
                metadata={
                    "header_count": header_count,
                }
            )
        ],
        page_count=1,
        total_chars=char_count,
        parser_metadata={
            "parser": "markdown",
            "header_count": header_count,
        },
        parser_version="1.0"
    )


def parse_document(
    file_content: bytes,
    mime_type: str,
    settings: Settings
) -> ParsedDocument:
    """Dispatch to appropriate parser based on MIME type."""
    if mime_type == "application/pdf":
        return parse_pdf(file_content, settings)
    elif mime_type == "text/plain":
        return parse_text(file_content, settings)
    elif mime_type == "text/markdown":
        return parse_markdown(file_content, settings)
    else:
        raise ParserError(f"Unsupported MIME type: {mime_type}", category="parsing")