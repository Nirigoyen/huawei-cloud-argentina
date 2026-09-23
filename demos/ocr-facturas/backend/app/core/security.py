"""File upload security validation and sanitization.

Provides:
- validate_file_type: Check file extension and MIME type against whitelist
- validate_file_size: Check file size against maximum limit
- sanitize_filename: Prevent path traversal attacks in filenames
"""

import pathlib

from fastapi import UploadFile

from app.core.config import get_settings
from app.core.exceptions import FileSizeExceededError, FileValidationError

# Extension to MIME type mapping for validation
EXTENSION_TO_MIME: dict[str, str] = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
}

# Dangerous path traversal sequences
DANGEROUS_SEQUENCES: list[str] = ["..", "\\", "//"]


def validate_file_type(filename: str, content_type: str | None = None) -> tuple[str, str]:
    """Validate that a file has an allowed extension and MIME type.

    Args:
        filename: The original filename from the upload.
        content_type: The MIME type reported by the client (optional).

    Returns:
        Tuple of (normalized_extension, expected_mime_type).

    Raises:
        FileValidationError: If the file type is not allowed.
    """
    settings = get_settings()

    # Extract extension (lowercase)
    if not filename or "." not in filename:
        raise FileValidationError(f"File has no extension. Allowed types: {', '.join(settings.allowed_extensions)}")

    ext = pathlib.PurePosixPath(filename).suffix.lower()

    if ext not in settings.allowed_extensions:
        raise FileValidationError(f"Unsupported file type '{ext}'. Allowed: {', '.join(settings.allowed_extensions)}")

    expected_mime = EXTENSION_TO_MIME.get(ext, "")

    # If content_type is provided, validate it matches
    if content_type and expected_mime:
        # Allow some flexibility in MIME type reporting
        # e.g., "image/jpeg" matches both .jpg and .jpeg
        if content_type != expected_mime:
            # Special case: .jpg and .jpeg both map to image/jpeg
            if not (ext in (".jpg", ".jpeg") and content_type == "image/jpeg"):
                raise FileValidationError(
                    f"File extension '{ext}' does not match MIME type '{content_type}'. Expected '{expected_mime}'."
                )

    return ext, expected_mime


def validate_file_size(file_size_bytes: int) -> None:
    """Validate that a file does not exceed the maximum allowed size.

    Args:
        file_size_bytes: The file size in bytes.

    Raises:
        FileValidationError: If the file exceeds the maximum size.
    """
    settings = get_settings()

    if file_size_bytes <= 0:
        raise FileValidationError("File is empty.")

    if file_size_bytes > settings.max_file_size_bytes:
        max_mb = settings.max_file_size_mb
        raise FileSizeExceededError(
            f"File size ({file_size_bytes / (1024 * 1024):.1f} MB) exceeds maximum allowed size of {max_mb} MB."
        )


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename to prevent path traversal attacks.

    Security measures:
    - Reject filenames containing '..' (parent directory traversal)
    - Reject filenames containing '\\' (Windows path separator)
    - Reject filenames containing '//' (double slash)
    - Extract basename to strip any directory components
    - Limit filename length to 255 characters

    Args:
        filename: The original filename to sanitize.

    Returns:
        The sanitized (basename only) filename.

    Raises:
        FileValidationError: If the filename contains dangerous sequences.
    """
    if not filename or not filename.strip():
        raise FileValidationError("Filename is empty.")

    # Check for dangerous sequences before any processing
    for seq in DANGEROUS_SEQUENCES:
        if seq in filename:
            raise FileValidationError(f"Filename contains forbidden sequence '{seq}'. Path traversal is not allowed.")

    # Extract basename using pathlib (strips directory components)
    basename = pathlib.PurePosixPath(filename).name

    # If basename is empty after extraction, the filename was suspicious
    if not basename:
        raise FileValidationError("Invalid filename: could not extract basename.")

    # Reject if basename differs from original (means there were directory components)
    if basename != filename and not (filename == basename):
        # Allow if the only difference is a leading ./ or similar
        if not filename.endswith(basename):
            raise FileValidationError("Filename contains directory components. Only plain filenames are allowed.")

    # Limit filename length
    if len(basename) > 255:
        raise FileValidationError(f"Filename too long ({len(basename)} chars). Maximum is 255 characters.")

    return basename


async def validate_upload_file(file: UploadFile) -> tuple[str, str, int]:
    """Validate an uploaded file comprehensively.

    Performs all validations: type, size, and filename sanitization.

    Args:
        file: The FastAPI UploadFile object.

    Returns:
        Tuple of (sanitized_filename, expected_mime_type, file_size_bytes).

    Raises:
        FileValidationError: If any validation fails.
    """
    # Sanitize filename first
    original_filename = file.filename or "unknown"
    sanitized = sanitize_filename(original_filename)

    # Validate file type
    ext, expected_mime = validate_file_type(sanitized, file.content_type)

    # Read file content to get size
    content = await file.read()
    file_size = len(content)

    # Validate file size
    validate_file_size(file_size)

    # Reset file position so it can be read again by downstream code
    await file.seek(0)

    return sanitized, expected_mime, file_size
