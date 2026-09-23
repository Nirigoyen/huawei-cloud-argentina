"""Pytest fixtures for OCR Facturas backend tests.

Provides:
- Mock Settings (no real DB or external services)
- In-memory SQLite async DB session for model tests
- FastAPI TestClient using httpx.AsyncClient
- Mock UploadFile for file upload tests
"""

import io
import uuid
from collections.abc import AsyncGenerator, Generator
from unittest.mock import patch

import pytest
import pytest_asyncio
from fastapi import UploadFile
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy import StaticPool
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from starlette.datastructures import Headers

from app.core.auth import ADMIN_USERNAME, create_access_token, get_current_user
from app.core.config import Settings
from app.core.database import get_db
from app.main import app
from app.models.base import Base

# =============================================================================
# Mock Settings
# =============================================================================


@pytest.fixture
def mock_settings() -> Settings:
    """Create a Settings instance with safe test defaults (no real credentials)."""
    return Settings(
        app_name="OCR Facturas Test",
        app_version="0.1.0",
        debug=True,
        database_url="sqlite+aiosqlite:///test.db",
        chatbot_database_url="sqlite+aiosqlite:///test.db",
        dify_base_url="http://localhost:3001",
        dify_api_key="test-dify-key",
        dify_workflow_id="test-workflow-id",
        huawei_iam_username="test-user",
        huawei_iam_password="test-pass",
        huawei_project_id="test-project",
        huawei_region="ap-southeast-1",
        maas_api_key="test-maas-key",
        maas_base_url="http://localhost:3002",
        maas_model_name="test-model",
        upload_dir="./test_uploads",
        max_file_size_mb=15,
        max_file_size_bytes=15 * 1024 * 1024,
        allowed_extensions=[".pdf", ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"],
        allowed_mime_types=[
            "application/pdf",
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/webp",
            "image/svg+xml",
        ],
        ocr_timeout_seconds=30,
        ocr_max_retries=2,
        ocr_retry_backoff_seconds=0.5,
        chatbot_query_timeout_seconds=5,
        chatbot_max_question_length=1000,
        cors_origins="http://localhost:3000",
        log_level="DEBUG",
        log_format="text",
    )


@pytest.fixture
def mock_settings_env(mock_settings: Settings) -> Generator[None, None, None]:
    """Patch get_settings() to return mock_settings throughout the app."""
    with patch("app.core.config.get_settings", return_value=mock_settings):
        yield


# =============================================================================
# In-Memory SQLite Async DB
# =============================================================================


@pytest_asyncio.fixture
async def async_db_engine():
    """Create an in-memory async SQLite engine for tests."""
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def async_db_session(async_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create an async DB session for tests, with auto-rollback."""
    session_factory = async_sessionmaker(
        async_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


# =============================================================================
# FastAPI Test Client
# =============================================================================


@pytest_asyncio.fixture
async def client(async_db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create an httpx AsyncClient that talks to the FastAPI app.

    Overrides the get_db dependency to use the test DB session.
    Overrides get_current_user to bypass authentication in tests.
    """

    async def _override_get_db():
        yield async_db_session

    def _override_get_current_user():
        return "test-user"

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user

    # Generate a valid JWT token for the auth middleware
    token = create_access_token({"sub": ADMIN_USERNAME})
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def sync_client(async_db_session: AsyncSession) -> Generator[TestClient, None, None]:
    """Create a synchronous TestClient for simple endpoint tests."""

    async def _override_get_db():
        yield async_db_session

    def _override_get_current_user():
        return "test-user"

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user
    with TestClient(app) as tc:
        yield tc
    app.dependency_overrides.clear()


# =============================================================================
# Mock UploadFile
# =============================================================================


def make_upload_file(
    filename: str = "test.pdf",
    content_type: str = "application/pdf",
    content: bytes = b"%PDF-1.4 test content",
) -> UploadFile:
    """Create a FastAPI UploadFile for testing file uploads."""
    file = UploadFile(
        filename=filename,
        file=io.BytesIO(content),
        headers=Headers({"content-type": content_type}),
    )
    return file


# =============================================================================
# UUID helpers
# =============================================================================


@pytest.fixture
def sample_invoice_id() -> uuid.UUID:
    """A fixed UUID for consistent test assertions."""
    return uuid.UUID("00000000-0000-0000-0000-000000000001")
