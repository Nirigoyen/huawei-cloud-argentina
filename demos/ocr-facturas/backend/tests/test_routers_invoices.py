"""Tests for Invoice CRUD API endpoints.

Covers:
- POST /api/v1/invoices/upload — file upload with validation
- GET /api/v1/invoices/ — list with pagination
- GET /api/v1/invoices/{id} — get detail
- DELETE /api/v1/invoices/{id} — delete
- POST /api/v1/invoices/{id}/retry — retry OCR
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.core.config import Settings

# =============================================================================
# Upload endpoint tests
# =============================================================================


class TestInvoiceUpload:
    """Tests for POST /api/v1/invoices/upload."""

    @pytest.mark.asyncio
    async def test_upload_valid_pdf(self, client: AsyncClient):
        """Upload a valid PDF file returns 201."""
        with (
            patch("app.core.config.get_settings") as mock_settings,
            patch("app.services.ocr_service.process_invoice", new_callable=AsyncMock),
        ):
            settings = Settings(upload_dir="./test_uploads")
            mock_settings.return_value = settings

            files = {"file": ("invoice.pdf", b"%PDF-1.4 test", "application/pdf")}
            response = await client.post("/api/v1/invoices/upload", files=files)
            assert response.status_code == 201
            data = response.json()
            assert "invoice_id" in data
            assert data["status"] == "processing"

    @pytest.mark.asyncio
    async def test_upload_valid_image(self, client: AsyncClient):
        """Upload a valid PNG image returns 201."""
        with (
            patch("app.core.config.get_settings") as mock_settings,
            patch("app.services.ocr_service.process_invoice", new_callable=AsyncMock),
        ):
            settings = Settings(upload_dir="./test_uploads")
            mock_settings.return_value = settings

            files = {"file": ("scan.png", b"\x89PNG\r\n\x1a\n" + b"\x00" * 100, "image/png")}
            response = await client.post("/api/v1/invoices/upload", files=files)
            assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_upload_invalid_file_type(self, client: AsyncClient):
        """Upload an unsupported file type returns 400."""
        with patch("app.core.config.get_settings") as mock_settings:
            settings = Settings(upload_dir="./test_uploads")
            mock_settings.return_value = settings

            files = {"file": ("malware.exe", b"binary content", "application/octet-stream")}
            response = await client.post("/api/v1/invoices/upload", files=files)
            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_upload_file_too_large(self, client: AsyncClient):
        """Upload a file exceeding size limit returns 413."""
        with (
            patch("app.core.config.get_settings") as mock_settings,
            patch("app.core.security.get_settings") as mock_security_settings,
        ):
            settings = Settings(
                upload_dir="./test_uploads",
                max_file_size_bytes=100,  # 100 bytes limit
            )
            mock_settings.return_value = settings
            mock_security_settings.return_value = settings

            large_content = b"x" * 200
            files = {"file": ("big.pdf", large_content, "application/pdf")}
            response = await client.post("/api/v1/invoices/upload", files=files)
            assert response.status_code == 413

    @pytest.mark.asyncio
    async def test_upload_path_traversal_filename(self, client: AsyncClient):
        """Upload with path traversal in filename returns 400."""
        with patch("app.core.config.get_settings") as mock_settings:
            settings = Settings(upload_dir="./test_uploads")
            mock_settings.return_value = settings

            files = {"file": ("../../../etc/passwd", b"secret", "text/plain")}
            response = await client.post("/api/v1/invoices/upload", files=files)
            assert response.status_code == 400


# =============================================================================
# List endpoint tests
# =============================================================================


class TestInvoiceList:
    """Tests for GET /api/v1/invoices/."""

    @pytest.mark.asyncio
    async def test_list_invoices_default_pagination(self, client: AsyncClient):
        """List invoices returns paginated response."""
        with patch("app.core.config.get_settings") as mock_settings:
            settings = Settings()
            mock_settings.return_value = settings

            response = await client.get("/api/v1/invoices/")
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "total" in data
            assert "page" in data
            assert "page_size" in data
            assert "total_pages" in data

    @pytest.mark.asyncio
    async def test_list_invoices_with_pagination(self, client: AsyncClient):
        """List invoices with custom page/page_size."""
        with patch("app.core.config.get_settings") as mock_settings:
            settings = Settings()
            mock_settings.return_value = settings

            response = await client.get("/api/v1/invoices/?page=1&page_size=10")
            assert response.status_code == 200
            data = response.json()
            assert data["page"] == 1
            assert data["page_size"] == 10

    @pytest.mark.asyncio
    async def test_list_invoices_with_status_filter(self, client: AsyncClient):
        """List invoices filtered by status."""
        with patch("app.core.config.get_settings") as mock_settings:
            settings = Settings()
            mock_settings.return_value = settings

            response = await client.get("/api/v1/invoices/?status=completed")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_invoices_with_type_filter(self, client: AsyncClient):
        """List invoices filtered by invoice type."""
        with patch("app.core.config.get_settings") as mock_settings:
            settings = Settings()
            mock_settings.return_value = settings

            response = await client.get("/api/v1/invoices/?invoice_type=A")
            assert response.status_code == 200


# =============================================================================
# Detail endpoint tests
# =============================================================================


class TestInvoiceDetail:
    """Tests for GET /api/v1/invoices/{invoice_id}."""

    @pytest.mark.asyncio
    async def test_get_nonexistent_invoice_returns_404(self, client: AsyncClient):
        """Getting a non-existent invoice returns 404."""
        fake_id = uuid.uuid4()
        response = await client.get(f"/api/v1/invoices/{fake_id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_invalid_uuid_returns_422(self, client: AsyncClient):
        """Getting an invalid UUID returns 422."""
        response = await client.get("/api/v1/invoices/not-a-uuid")
        assert response.status_code == 422


# =============================================================================
# Delete endpoint tests
# =============================================================================


class TestInvoiceDelete:
    """Tests for DELETE /api/v1/invoices/{invoice_id}."""

    @pytest.mark.asyncio
    async def test_delete_nonexistent_invoice_returns_404(self, client: AsyncClient):
        """Deleting a non-existent invoice returns 404."""
        fake_id = uuid.uuid4()
        response = await client.delete(f"/api/v1/invoices/{fake_id}")
        assert response.status_code == 404


# =============================================================================
# Retry endpoint tests
# =============================================================================


class TestInvoiceRetry:
    """Tests for POST /api/v1/invoices/{invoice_id}/retry."""

    @pytest.mark.asyncio
    async def test_retry_nonexistent_invoice_returns_404(self, client: AsyncClient):
        """Retrying a non-existent invoice returns 404."""
        fake_id = uuid.uuid4()
        response = await client.post(f"/api/v1/invoices/{fake_id}/retry")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_retry_invalid_uuid_returns_422(self, client: AsyncClient):
        """Retrying with invalid UUID returns 422."""
        response = await client.post("/api/v1/invoices/not-a-uuid/retry")
        assert response.status_code == 422
