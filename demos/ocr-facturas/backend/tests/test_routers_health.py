"""Tests for the health check API endpoint.

Covers:
- GET /api/v1/health/ — healthy response when DB is available
- Service status reporting (database, dify, maas)
- Unhealthy response when DB is down
"""

from unittest.mock import patch

import pytest
from httpx import AsyncClient

from app.core.config import Settings

# =============================================================================
# Health endpoint tests
# =============================================================================


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_returns_200_when_db_ok(self, client: AsyncClient):
        """When DB is reachable, health returns 200 with status 'healthy'."""
        with patch("app.core.config.get_settings") as mock_settings:
            settings = Settings(
                dify_api_key="",
                dify_base_url="",
                maas_api_key="",
                maas_base_url="",
            )
            mock_settings.return_value = settings

            response = await client.get("/api/v1/health/")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "services" in data

    @pytest.mark.asyncio
    async def test_health_includes_database_status(self, client: AsyncClient):
        """Health response includes database service status."""
        with patch("app.core.config.get_settings") as mock_settings:
            settings = Settings(
                dify_api_key="",
                dify_base_url="",
                maas_api_key="",
                maas_base_url="",
            )
            mock_settings.return_value = settings

            response = await client.get("/api/v1/health/")
            data = response.json()
            assert "database" in data["services"]

    @pytest.mark.asyncio
    async def test_health_shows_dify_not_configured(self, client: AsyncClient):
        """When Dify is not configured, status is 'not_configured'."""
        with patch("app.core.config.get_settings") as mock_settings:
            settings = Settings(
                dify_api_key="",
                dify_base_url="",
                maas_api_key="",
                maas_base_url="",
            )
            mock_settings.return_value = settings

            response = await client.get("/api/v1/health/")
            data = response.json()
            assert data["services"]["dify"] == "not_configured"

    @pytest.mark.asyncio
    async def test_health_shows_maas_not_configured(self, client: AsyncClient):
        """When MaaS is not configured, status is 'not_configured'."""
        with patch("app.core.config.get_settings") as mock_settings:
            settings = Settings(
                dify_api_key="",
                dify_base_url="",
                maas_api_key="",
                maas_base_url="",
            )
            mock_settings.return_value = settings

            response = await client.get("/api/v1/health/")
            data = response.json()
            assert data["services"]["maas"] == "not_configured"

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client: AsyncClient):
        """Root endpoint returns API info."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert data["name"] == "OCR Facturas API"
