import magic
import os
from typing import BinaryIO, Tuple
from app.config import Settings


# Allowed MIME types and their corresponding file extensions
ALLOWED_MIME_TYPES = {
    "application/pdf": [".pdf"],
    "text/plain": [".txt"],
    "text/markdown": [".md", ".markdown"],
}

# File signatures (magic bytes) for validation
FILE_SIGNATURES = {
    "application/pdf": [b"%PDF"],
    "text/plain": [],  # No specific signature
    "text/markdown": [],  # No specific signature
}

# Maximum file sizes (in bytes)
MAX_FILE_SIZES = {
    "application/pdf": 20 * 1024 * 1024,  # 20 MB
    "text/plain": 10 * 1024 * 1024,  # 10 MB
    "text/markdown": 10 * 1024 * 1024,  # 10 MB
}

# Maximum extracted text length
MAX_EXTRACTED_CHARS = 1_000_000

# Maximum PDF pages
MAX_PDF_PAGES = 200


class ValidationError(Exception):
    """Raised when file validation fails."""

    def __init__(self, message: str, category: str = "validation"):
        self.message = message
        self.category = category
        super().__init__(message)


def validate_file_size(file_size: int, mime_type: str, settings: Settings) -> None:
    """Validate file size against limits."""
    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file_size > max_size:
        raise ValidationError(
            f"File size {file_size} bytes exceeds maximum allowed size of {max_size} bytes",
            category="validation"
        )
    
    # MIME-specific limits
    mime_max = MAX_FILE_SIZES.get(mime_type, max_size)
    if file_size > mime_max:
        raise ValidationError(
            f"File size {file_size} bytes exceeds maximum for {mime_type} of {mime_max} bytes",
            category="validation"
        )


def validate_mime_type(mime_type: str) -> None:
    """Validate MIME type is allowed."""
    if mime_type not in ALLOWED_MIME_TYPES:
        allowed = ", ".join(ALLOWED_MIME_TYPES.keys())
        raise ValidationError(
            f"Unsupported file type: {mime_type}. Allowed types: {allowed}",
            category="validation"
        )


def validate_file_extension(filename: str, mime_type: str) -> None:
    """Validate file extension matches MIME type."""
    ext = os.path.splitext(filename.lower())[1]
    allowed_extensions = ALLOWED_MIME_TYPES.get(mime_type, [])
    
    if ext not in allowed_extensions:
        raise ValidationError(
            f"File extension {ext} does not match MIME type {mime_type}",
            category="validation"
        )


def validate_file_signature(file_content: bytes, mime_type: str) -> None:
    """Validate file signature (magic bytes) matches expected type."""
    signatures = FILE_SIGNATURES.get(mime_type, [])
    
    if not signatures:
        # No signature to validate for text types
        return
    
    for signature in signatures:
        if file_content.startswith(signature):
            return
    
    raise ValidationError(
        f"File signature does not match expected type {mime_type}",
        category="validation"
    )


def validate_filename_safety(filename: str) -> str:
    """Validate and sanitize filename, return safe storage name."""
    if not filename or filename.strip() == "":
        raise ValidationError("Filename cannot be empty", category="validation")
    
    # Check for path traversal attempts
    if ".." in filename or "/" in filename or "\\" in filename:
        raise ValidationError("Filename contains path traversal sequences", category="validation")
    
    # Check for null bytes
    if "\x00" in filename:
        raise ValidationError("Filename contains null bytes", category="validation")
    
    # Check length
    if len(filename) > 255:
        raise ValidationError("Filename too long (max 255 characters)", category="validation")
    
    # Generate safe storage name (we'll use UUID in practice, but keep original for metadata)
    return filename


async def validate_upload_file(
    file: BinaryIO,
    filename: str,
    content_type: str,
    settings: Settings
) -> Tuple[str, int]:
    """
    Validate an uploaded file comprehensively.
    
    Returns:
        Tuple of (safe_filename, file_size)
    """
    # Read file content for validation (first 8KB for signature check)
    file.seek(0)
    header = file.read(8192)
    file.seek(0)
    
    # Get file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    # Determine MIME type
    mime_type = content_type or "application/octet-stream"
    
    # Validate
    validate_filename_safety(filename)
    validate_mime_type(mime_type)
    validate_file_extension(filename, mime_type)
    validate_file_size(file_size, mime_type, settings)
    validate_file_signature(header, mime_type)
    
    return filename, file_size


def get_mime_type_from_content(file_content: bytes, filename: str) -> str:
    """Detect MIME type from file content using python-magic."""
    mime = magic.Magic(mime=True)
    detected = mime.from_buffer(file_content)
    
    # Fallback to extension-based detection
    if detected == "application/octet-stream":
        ext = os.path.splitext(filename.lower())[1]
        if ext == ".pdf":
            return "application/pdf"
        elif ext in [".txt"]:
            return "text/plain"
        elif ext in [".md", ".markdown"]:
            return "text/markdown"
    
    return detected