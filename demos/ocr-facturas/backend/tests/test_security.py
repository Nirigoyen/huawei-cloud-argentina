"""Tests for file upload security validation and sanitization.

Covers:
- validate_file_type: extension and MIME type validation
- validate_file_size: size limit enforcement
- sanitize_filename: path traversal prevention
- validate_upload_file: comprehensive upload validation
"""

import io
from unittest.mock import patch

import pytest
from fastapi import UploadFile
from starlette.datastructures import Headers

from app.core.config import Settings
from app.core.exceptions import FileSizeExceededError, FileValidationError
from app.core.security import (
    DANGEROUS_SEQUENCES,
    EXTENSION_TO_MIME,
    sanitize_filename,
    validate_file_size,
    validate_file_type,
    validate_upload_file,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def settings():
    """Default test settings."""
    return Settings()


@pytest.fixture
def mock_settings(settings):
    """Patch get_settings to return test settings."""
    with patch("app.core.security.get_settings", return_value=settings):
        yield settings


# =============================================================================
# validate_file_type tests
# =============================================================================


class TestValidateFileType:
    """Tests for validate_file_type function."""

    def test_valid_pdf(self, mock_settings):
        ext, mime = validate_file_type("invoice.pdf", "application/pdf")
        assert ext == ".pdf"
        assert mime == "application/pdf"

    def test_valid_jpg(self, mock_settings):
        ext, mime = validate_file_type("photo.jpg", "image/jpeg")
        assert ext == ".jpg"
        assert mime == "image/jpeg"

    def test_valid_jpeg(self, mock_settings):
        ext, mime = validate_file_type("photo.jpeg", "image/jpeg")
        assert ext == ".jpeg"
        assert mime == "image/jpeg"

    def test_valid_png(self, mock_settings):
        ext, mime = validate_file_type("scan.png", "image/png")
        assert ext == ".png"
        assert mime == "image/png"

    def test_valid_gif(self, mock_settings):
        ext, mime = validate_file_type("anim.gif", "image/gif")
        assert ext == ".gif"
        assert mime == "image/gif"

    def test_valid_webp(self, mock_settings):
        ext, mime = validate_file_type("image.webp", "image/webp")
        assert ext == ".webp"
        assert mime == "image/webp"

    def test_valid_svg(self, mock_settings):
        ext, mime = validate_file_type("diagram.svg", "image/svg+xml")
        assert ext == ".svg"
        assert mime == "image/svg+xml"

    def test_uppercase_extension(self, mock_settings):
        ext, mime = validate_file_type("INVOICE.PDF", "application/pdf")
        assert ext == ".pdf"
        assert mime == "application/pdf"

    def test_mixed_case_extension(self, mock_settings):
        ext, mime = validate_file_type("Invoice.PdF", "application/pdf")
        assert ext == ".pdf"
        assert mime == "application/pdf"

    def test_no_extension_raises(self, mock_settings):
        with pytest.raises(FileValidationError) as exc_info:
            validate_file_type("README", None)
        assert "no extension" in exc_info.value.message.lower()

    def test_empty_filename_raises(self, mock_settings):
        with pytest.raises(FileValidationError) as exc_info:
            validate_file_type("", None)
        assert "no extension" in exc_info.value.message.lower()

    def test_unsupported_extension_raises(self, mock_settings):
        with pytest.raises(FileValidationError) as exc_info:
            validate_file_type("malware.exe", "application/octet-stream")
        assert "unsupported" in exc_info.value.message.lower()

    def test_unsupported_txt_raises(self, mock_settings):
        with pytest.raises(FileValidationError) as exc_info:
            validate_file_type("notes.txt", "text/plain")
        assert "unsupported" in exc_info.value.message.lower()

    def test_mime_mismatch_raises(self, mock_settings):
        with pytest.raises(FileValidationError) as exc_info:
            validate_file_type("image.png", "image/jpeg")
        assert "does not match" in exc_info.value.message.lower()

    def test_jpg_with_jpeg_mime_ok(self, mock_settings):
        """JPG extension with image/jpeg MIME should pass (special case)."""
        ext, mime = validate_file_type("photo.jpg", "image/jpeg")
        assert ext == ".jpg"

    def test_jpeg_with_jpeg_mime_ok(self, mock_settings):
        """JPEG extension with image/jpeg MIME should pass."""
        ext, mime = validate_file_type("photo.jpeg", "image/jpeg")
        assert ext == ".jpeg"

    def test_no_content_type_skips_mime_check(self, mock_settings):
        """When content_type is None, MIME check is skipped."""
        ext, mime = validate_file_type("invoice.pdf", None)
        assert ext == ".pdf"
        assert mime == "application/pdf"

    def test_returns_expected_mime_even_without_content_type(self, mock_settings):
        ext, mime = validate_file_type("scan.png", None)
        assert mime == "image/png"


# =============================================================================
# validate_file_size tests
# =============================================================================


class TestValidateFileSize:
    """Tests for validate_file_size function."""

    def test_valid_small_file(self, mock_settings):
        # Should not raise
        validate_file_size(1024)

    def test_valid_exact_max_size(self, mock_settings):
        # 15 MB = 15,728,640 bytes
        validate_file_size(15 * 1024 * 1024)

    def test_zero_size_raises(self, mock_settings):
        with pytest.raises(FileValidationError) as exc_info:
            validate_file_size(0)
        assert "empty" in exc_info.value.message.lower()

    def test_negative_size_raises(self, mock_settings):
        with pytest.raises(FileValidationError) as exc_info:
            validate_file_size(-1)
        assert "empty" in exc_info.value.message.lower()

    def test_exceeds_max_size_raises(self, mock_settings):
        with pytest.raises(FileSizeExceededError) as exc_info:
            validate_file_size(15 * 1024 * 1024 + 1)
        assert "exceeds" in exc_info.value.message.lower()

    def test_very_large_file_raises(self, mock_settings):
        with pytest.raises(FileSizeExceededError) as exc_info:
            validate_file_size(100 * 1024 * 1024)  # 100 MB
        assert "exceeds" in exc_info.value.message.lower()

    def test_one_byte_file(self, mock_settings):
        # 1 byte is valid (> 0 and <= max)
        validate_file_size(1)


# =============================================================================
# sanitize_filename tests
# =============================================================================


class TestSanitizeFilename:
    """Tests for sanitize_filename function."""

    def test_simple_filename(self):
        result = sanitize_filename("invoice.pdf")
        assert result == "invoice.pdf"

    def test_filename_with_spaces(self):
        result = sanitize_filename("my invoice.pdf")
        assert result == "my invoice.pdf"

    def test_path_traversal_double_dot_raises(self):
        with pytest.raises(FileValidationError) as exc_info:
            sanitize_filename("../../../etc/passwd")
        assert "forbidden" in exc_info.value.message.lower()

    def test_backslash_raises(self):
        with pytest.raises(FileValidationError) as exc_info:
            sanitize_filename("dir\\file.pdf")
        assert "forbidden" in exc_info.value.message.lower()

    def test_double_slash_raises(self):
        with pytest.raises(FileValidationError) as exc_info:
            sanitize_filename("dir//file.pdf")
        assert "forbidden" in exc_info.value.message.lower()

    def test_empty_filename_raises(self):
        with pytest.raises(FileValidationError) as exc_info:
            sanitize_filename("")
        assert "empty" in exc_info.value.message.lower()

    def test_whitespace_only_filename_raises(self):
        with pytest.raises(FileValidationError) as exc_info:
            sanitize_filename("   ")
        assert "empty" in exc_info.value.message.lower()

    def test_very_long_filename_raises(self):
        long_name = "a" * 256 + ".pdf"
        with pytest.raises(FileValidationError) as exc_info:
            sanitize_filename(long_name)
        assert "too long" in exc_info.value.message.lower()

    def test_max_length_filename_ok(self):
        """255 chars is the max allowed length."""
        max_name = "a" * 251 + ".pdf"  # 255 chars total
        result = sanitize_filename(max_name)
        assert result == max_name
        assert len(result) == 255

    def test_path_traversal_in_middle_raises(self):
        with pytest.raises(FileValidationError) as exc_info:
            sanitize_filename("docs/../secret.pdf")
        assert "forbidden" in exc_info.value.message.lower()

    def test_dangerous_sequences_constant(self):
        """Verify the DANGEROUS_SEQUENCES constant is properly defined."""
        assert ".." in DANGEROUS_SEQUENCES
        assert "\\" in DANGEROUS_SEQUENCES
        assert "//" in DANGEROUS_SEQUENCES


# =============================================================================
# validate_upload_file tests
# =============================================================================


class TestValidateUploadFile:
    """Tests for the comprehensive validate_upload_file function."""

    @pytest.mark.asyncio
    async def test_valid_pdf_upload(self, mock_settings):
        file = UploadFile(
            filename="invoice.pdf",
            file=io.BytesIO(b"%PDF-1.4 test content"),
            headers=Headers({"content-type": "application/pdf"}),
        )

        sanitized, mime, size = await validate_upload_file(file)
        assert sanitized == "invoice.pdf"
        assert mime == "application/pdf"
        assert size > 0

    @pytest.mark.asyncio
    async def test_valid_image_upload(self, mock_settings):
        content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        file = UploadFile(
            filename="scan.png",
            file=io.BytesIO(content),
            headers=Headers({"content-type": "image/png"}),
        )

        sanitized, mime, size = await validate_upload_file(file)
        assert sanitized == "scan.png"
        assert mime == "image/png"
        assert size == len(content)

    @pytest.mark.asyncio
    async def test_invalid_file_type_raises(self, mock_settings):
        file = UploadFile(
            filename="malware.exe",
            file=io.BytesIO(b"binary content"),
            headers=Headers({"content-type": "application/octet-stream"}),
        )

        with pytest.raises(FileValidationError):
            await validate_upload_file(file)

    @pytest.mark.asyncio
    async def test_path_traversal_filename_raises(self, mock_settings):
        file = UploadFile(
            filename="../../../etc/passwd",
            file=io.BytesIO(b"secret"),
            headers=Headers({"content-type": "text/plain"}),
        )

        with pytest.raises(FileValidationError):
            await validate_upload_file(file)

    @pytest.mark.asyncio
    async def test_file_resets_position_after_validation(self, mock_settings):
        """After validation, the file position should be reset to 0."""
        content = b"%PDF-1.4 test content"
        file = UploadFile(
            filename="test.pdf",
            file=io.BytesIO(content),
            headers=Headers({"content-type": "application/pdf"}),
        )

        await validate_upload_file(file)

        # Read again - should get the same content
        remaining = await file.read()
        assert remaining == content


# =============================================================================
# Extension-to-MIME mapping tests
# =============================================================================


class TestExtensionToMimeMap:
    """Tests for the EXTENSION_TO_MIME constant."""

    def test_pdf_mapping(self):
        assert EXTENSION_TO_MIME[".pdf"] == "application/pdf"

    def test_jpg_mapping(self):
        assert EXTENSION_TO_MIME[".jpg"] == "image/jpeg"

    def test_jpeg_mapping(self):
        assert EXTENSION_TO_MIME[".jpeg"] == "image/jpeg"

    def test_png_mapping(self):
        assert EXTENSION_TO_MIME[".png"] == "image/png"

    def test_gif_mapping(self):
        assert EXTENSION_TO_MIME[".gif"] == "image/gif"

    def test_webp_mapping(self):
        assert EXTENSION_TO_MIME[".webp"] == "image/webp"

    def test_svg_mapping(self):
        assert EXTENSION_TO_MIME[".svg"] == "image/svg+xml"

    def test_all_extensions_have_mime(self, mock_settings):
        """Every allowed extension should have a MIME type mapping."""
        for ext in mock_settings.allowed_extensions:
            assert ext in EXTENSION_TO_MIME, f"Extension {ext} missing from EXTENSION_TO_MIME"
