"""Data forward service - writes invoice data to a configured destination database.

Supports PostgreSQL and MySQL destinations. Creates the target table
if it doesn't exist, then inserts the invoice data as a JSON record.
Also provides schema introspection for the destination database table.
"""

import json
import logging
from typing import Any

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def _build_connection_url(settings) -> str:
    """Build SQLAlchemy connection URL from settings."""
    db_type = settings.destination_db_type.lower()

    if db_type == "postgresql":
        port = settings.destination_db_port or "5432"
        return (
            f"postgresql+psycopg2://{settings.destination_db_username}"
            f":{settings.destination_db_password}@{settings.destination_db_host}"
            f":{port}/{settings.destination_db_name}"
        )
    elif db_type == "mysql":
        port = settings.destination_db_port or "3306"
        return (
            f"mysql+pymysql://{settings.destination_db_username}"
            f":{settings.destination_db_password}@{settings.destination_db_host}"
            f":{port}/{settings.destination_db_name}"
        )
    else:
        raise ValueError(f"Unsupported destination database type: {db_type}")


def _ensure_table_exists(engine: Engine, table_name: str, db_type: str) -> None:
    """Create the destination table if it doesn't exist."""
    if db_type == "postgresql":
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            invoice_data JSONB NOT NULL,
            source VARCHAR(100) DEFAULT 'ocr-facturas',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    elif db_type == "mysql":
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            invoice_data JSON NOT NULL,
            source VARCHAR(100) DEFAULT 'ocr-facturas',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    else:
        raise ValueError(f"Unsupported db_type: {db_type}")

    with engine.connect() as conn:
        conn.execute(text(create_sql))
        conn.commit()
    logger.info("Ensured table '%s' exists in destination database", table_name)


def forward_invoice_data(invoice_data: dict[str, Any]) -> dict[str, Any]:
    """Forward invoice data to the configured destination database.

    Args:
        invoice_data: Dictionary containing the extracted invoice data.

    Returns:
        Dict with 'success' bool and 'message' str.
    """
    settings = get_settings()

    if not settings.data_forward_enabled:
        return {"success": False, "message": "Data forwarding is disabled"}

    if not settings.is_destination_db_configured:
        return {"success": False, "message": "Destination database not configured"}

    try:
        conn_url = _build_connection_url(settings)
        engine = create_engine(conn_url, pool_pre_ping=True)

        table_name = settings.destination_db_table or "invoices"
        db_type = settings.destination_db_type.lower()

        # Ensure table exists
        _ensure_table_exists(engine, table_name, db_type)

        # Insert data
        json_str = json.dumps(invoice_data, ensure_ascii=False, default=str)

        with engine.connect() as conn:
            if db_type == "postgresql":
                conn.execute(
                    text(f"INSERT INTO {table_name} (invoice_data) VALUES (:data::jsonb)"),
                    {"data": json_str},
                )
            elif db_type == "mysql":
                conn.execute(
                    text(f"INSERT INTO {table_name} (invoice_data) VALUES (:data)"),
                    {"data": json_str},
                )
            conn.commit()

        logger.info(
            "Forwarded invoice data to %s://%s/%s.%s",
            db_type,
            settings.destination_db_host,
            settings.destination_db_name,
            table_name,
        )

        return {
            "success": True,
            "message": (
                f"Data forwarded to {db_type}://{settings.destination_db_host}"
                f"/{settings.destination_db_name}.{table_name}"
            ),
        }

    except Exception as e:
        logger.error("Failed to forward invoice data: %s", str(e))
        return {"success": False, "message": f"Forward failed: {str(e)}"}


def get_destination_db_schema() -> dict[str, Any]:
    """Get the schema of the destination database table.

    Introspects the configured destination database and returns column
    names, types, and nullability. This schema is passed to the Dify
    workflow so the LLM only extracts fields that match the database
    structure.

    Returns:
        Dict with 'success' bool, 'message' str, and 'schema' dict or None.
        The schema dict contains 'table' (str) and 'columns' (list of dicts).
    """
    settings = get_settings()

    if not settings.is_destination_db_configured:
        return {"success": False, "message": "Destination database not configured", "schema": None}

    try:
        conn_url = _build_connection_url(settings)
        engine = create_engine(conn_url, pool_pre_ping=True)
        table_name = settings.destination_db_table or "invoices"

        inspector = inspect(engine)

        if not inspector.has_table(table_name):
            return {
                "success": False,
                "message": f"Table '{table_name}' does not exist",
                "schema": None,
            }

        columns = inspector.get_columns(table_name)
        schema = {
            "table": table_name,
            "columns": [
                {
                    "name": col["name"],
                    "type": str(col["type"]),
                    "nullable": col.get("nullable", True),
                }
                for col in columns
            ],
        }

        logger.info("Retrieved schema for table '%s': %d columns", table_name, len(schema["columns"]))
        return {"success": True, "message": f"Schema retrieved for {table_name}", "schema": schema}

    except Exception as e:
        logger.error("Failed to get destination DB schema: %s", str(e))
        return {"success": False, "message": f"Error: {str(e)}", "schema": None}
