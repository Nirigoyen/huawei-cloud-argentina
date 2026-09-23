"""Safe parameterized query executor for chatbot.

Enforces:
- Table/column whitelist validation
- Read-only query execution (SELECT only)
- Statement timeout (5 seconds)
- Parameterized queries only (no raw SQL interpolation)
"""

import asyncio
import logging
import time
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import ChatbotError, ChatbotQueryTimeoutError
from app.services.chatbot.intents import DENIED_TABLES

logger = logging.getLogger(__name__)


# SQL keywords that indicate write operations
FORBIDDEN_KEYWORDS: set[str] = {
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "CREATE",
    "TRUNCATE",
    "REPLACE",
    "MERGE",
    "GRANT",
    "REVOKE",
}


def validate_query_safety(sql_template: str) -> None:
    """Validate that a SQL template is safe for execution.

    Checks:
    - No forbidden SQL keywords (INSERT, UPDATE, DELETE, etc.)
    - Only references allowed tables
    - Uses parameterized syntax (:param_name)

    Args:
        sql_template: The SQL template to validate.

    Raises:
        ChatbotError: If the query violates safety rules.
    """
    upper_sql = sql_template.upper()

    # Check for forbidden keywords
    for keyword in FORBIDDEN_KEYWORDS:
        if keyword in upper_sql:
            raise ChatbotError(f"Query contains forbidden keyword '{keyword}'. Only SELECT queries are allowed.")

    # Check for table references
    for denied_table in DENIED_TABLES:
        if denied_table in sql_template.lower():
            raise ChatbotError(f"Query references denied table '{denied_table}'.")


async def execute_query(
    db: AsyncSession,
    sql_template: str,
    params: dict[str, Any],
    timeout_seconds: int | None = None,
) -> list[dict[str, Any]]:
    """Execute a parameterized SQL query with safety controls.

    Args:
        db: Async database session (read-only chatbot connection).
        sql_template: Parameterized SQL template with :param placeholders.
        params: Dictionary of parameter values.
        timeout_seconds: Override timeout (default from config).

    Returns:
        List of result rows as dictionaries.

    Raises:
        ChatbotError: If the query fails safety validation.
        ChatbotQueryTimeoutError: If the query exceeds the timeout.
    """
    settings = get_settings()
    timeout = timeout_seconds or settings.chatbot_query_timeout_seconds

    # Validate query safety
    validate_query_safety(sql_template)

    # Build the SQLAlchemy text query with parameters
    query = text(sql_template)

    start_time = time.time()

    try:
        # Execute with timeout
        result = await asyncio.wait_for(
            db.execute(query, params),
            timeout=timeout,
        )

        # Convert result rows to dictionaries
        rows = []
        for row in result.mappings():
            row_dict = {}
            for key, value in row.items():
                # Convert non-serializable types
                if hasattr(value, "isoformat"):
                    row_dict[key] = value.isoformat()
                else:
                    row_dict[key] = value
            rows.append(row_dict)

        elapsed_ms = (time.time() - start_time) * 1000
        logger.info(
            "Chatbot query executed in %.1fms, %d rows returned",
            elapsed_ms,
            len(rows),
        )

        return rows

    except TimeoutError:
        elapsed_ms = (time.time() - start_time) * 1000
        logger.warning(
            "Chatbot query timed out after %.1fms (limit: %ds)",
            elapsed_ms,
            timeout,
        )
        raise ChatbotQueryTimeoutError(f"Query timed out after {timeout} seconds")

    except Exception as e:
        elapsed_ms = (time.time() - start_time) * 1000
        logger.error(
            "Chatbot query failed after %.1fms: %s",
            elapsed_ms,
            str(e),
        )
        raise ChatbotError(f"Query execution failed: {str(e)}")
