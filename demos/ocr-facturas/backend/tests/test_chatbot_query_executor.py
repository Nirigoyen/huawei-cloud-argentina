"""Tests for the chatbot query executor.

Covers:
- validate_query_safety: forbidden keywords, denied tables
- execute_query: parameterized execution, timeout, read-only enforcement
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import ChatbotError
from app.services.chatbot.query_executor import (
    FORBIDDEN_KEYWORDS,
    execute_query,
    validate_query_safety,
)

# =============================================================================
# validate_query_safety tests
# =============================================================================


class TestValidateQuerySafety:
    """Tests for the validate_query_safety function."""

    def test_valid_select_query(self):
        """A simple SELECT query should pass validation."""
        validate_query_safety("SELECT * FROM invoices WHERE status = 'completed'")

    def test_valid_parameterized_query(self):
        """A parameterized SELECT query should pass validation."""
        validate_query_safety("SELECT * FROM invoices WHERE issue_date >= :start_date AND issue_date <= :end_date")

    def test_insert_raises(self):
        """INSERT keyword should be rejected."""
        with pytest.raises(ChatbotError) as exc_info:
            validate_query_safety("INSERT INTO invoices VALUES (1, 2, 3)")
        assert "INSERT" in exc_info.value.message

    def test_update_raises(self):
        """UPDATE keyword should be rejected."""
        with pytest.raises(ChatbotError) as exc_info:
            validate_query_safety("UPDATE invoices SET status = 'archived'")
        assert "UPDATE" in exc_info.value.message

    def test_delete_raises(self):
        """DELETE keyword should be rejected."""
        with pytest.raises(ChatbotError) as exc_info:
            validate_query_safety("DELETE FROM invoices")
        assert "DELETE" in exc_info.value.message

    def test_drop_raises(self):
        """DROP keyword should be rejected."""
        with pytest.raises(ChatbotError) as exc_info:
            validate_query_safety("DROP TABLE invoices")
        assert "DROP" in exc_info.value.message

    def test_alter_raises(self):
        """ALTER keyword should be rejected."""
        with pytest.raises(ChatbotError) as exc_info:
            validate_query_safety("ALTER TABLE invoices ADD COLUMN test TEXT")
        assert "ALTER" in exc_info.value.message

    def test_create_raises(self):
        """CREATE keyword should be rejected."""
        with pytest.raises(ChatbotError) as exc_info:
            validate_query_safety("CREATE TABLE evil (id INT)")
        assert "CREATE" in exc_info.value.message

    def test_truncate_raises(self):
        """TRUNCATE keyword should be rejected."""
        with pytest.raises(ChatbotError) as exc_info:
            validate_query_safety("TRUNCATE TABLE invoices")
        assert "TRUNCATE" in exc_info.value.message

    def test_denied_table_chatbot_logs_raises(self):
        """Query referencing chatbot_query_logs should be rejected."""
        with pytest.raises(ChatbotError) as exc_info:
            validate_query_safety("SELECT * FROM chatbot_query_logs")
        assert "denied" in exc_info.value.message.lower()

    def test_denied_table_app_settings_raises(self):
        """Query referencing app_settings should be rejected."""
        with pytest.raises(ChatbotError) as exc_info:
            validate_query_safety("SELECT * FROM app_settings")
        assert "denied" in exc_info.value.message.lower()

    def test_denied_table_alembic_raises(self):
        """Query referencing alembic_version should be rejected."""
        with pytest.raises(ChatbotError) as exc_info:
            validate_query_safety("SELECT * FROM alembic_version")
        assert "denied" in exc_info.value.message.lower()

    def test_grant_raises(self):
        """GRANT keyword should be rejected."""
        with pytest.raises(ChatbotError) as exc_info:
            validate_query_safety("GRANT ALL ON invoices TO public")
        assert "GRANT" in exc_info.value.message

    def test_revoke_raises(self):
        """REVOKE keyword should be rejected."""
        with pytest.raises(ChatbotError) as exc_info:
            validate_query_safety("REVOKE ALL ON invoices FROM public")
        assert "REVOKE" in exc_info.value.message


# =============================================================================
# FORBIDDEN_KEYWORDS constant tests
# =============================================================================


class TestForbiddenKeywords:
    """Tests for the FORBIDDEN_KEYWORDS constant."""

    def test_contains_expected_keywords(self):
        expected = {"INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE"}
        assert expected.issubset(FORBIDDEN_KEYWORDS)

    def test_is_set(self):
        assert isinstance(FORBIDDEN_KEYWORDS, set)


# =============================================================================
# execute_query tests
# =============================================================================


class TestExecuteQuery:
    """Tests for the execute_query function."""

    @pytest.mark.asyncio
    async def test_unsafe_query_raises(self):
        """Executing an unsafe query raises ChatbotError."""
        with patch("app.core.config.get_settings") as mock_settings:
            settings = Settings(chatbot_query_timeout_seconds=5)
            mock_settings.return_value = settings

            mock_db = AsyncMock(spec=AsyncSession)
            with pytest.raises(ChatbotError):
                await execute_query(
                    mock_db,
                    "DELETE FROM invoices",
                    {},
                )

    @pytest.mark.asyncio
    async def test_denied_table_raises(self):
        """Executing a query on a denied table raises ChatbotError."""
        with patch("app.core.config.get_settings") as mock_settings:
            settings = Settings(chatbot_query_timeout_seconds=5)
            mock_settings.return_value = settings

            mock_db = AsyncMock(spec=AsyncSession)
            with pytest.raises(ChatbotError):
                await execute_query(
                    mock_db,
                    "SELECT * FROM app_settings",
                    {},
                )

    @pytest.mark.asyncio
    async def test_custom_timeout(self):
        """Custom timeout_seconds parameter is used."""
        with patch("app.core.config.get_settings") as mock_settings:
            settings = Settings(chatbot_query_timeout_seconds=5)
            mock_settings.return_value = settings

            mock_db = AsyncMock(spec=AsyncSession)
            mock_result = MagicMock()
            mock_result.mappings.return_value = []
            mock_db.execute = AsyncMock(return_value=mock_result)

            # With a very short timeout and a fast query, this should succeed
            result = await execute_query(
                mock_db,
                "SELECT 1",
                {},
                timeout_seconds=10,
            )
            assert isinstance(result, list)
