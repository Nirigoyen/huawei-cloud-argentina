"""Data forward API router - receives invoice data from Dify and writes to destination DB."""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from app.services.data_forward_service import forward_invoice_data, get_destination_db_schema

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data-forward", tags=["data-forward"])


@router.post("/invoice")
async def forward_invoice(invoice_data: dict[str, Any]) -> dict[str, Any]:
    """Receive invoice data from Dify workflow and forward to destination database.

    This endpoint is called by the Dify workflow's HTTP Request 3 node
    after the LLM extracts the invoice data.

    The request body should contain the extracted invoice data as a JSON object.
    """
    logger.info(
        "Received data forward request with invoice data keys: %s",
        list(invoice_data.keys()),
    )

    result = forward_invoice_data(invoice_data)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.post("/test")
async def test_destination_connection() -> dict[str, Any]:
    """Test connection to the configured destination database."""
    from sqlalchemy import create_engine, text

    from app.core.config import get_settings
    from app.services.data_forward_service import _build_connection_url

    settings = get_settings()

    if not settings.is_destination_db_configured:
        return {"success": False, "message": "Destination database not configured"}

    try:
        conn_url = _build_connection_url(settings)
        engine = create_engine(conn_url, pool_pre_ping=True)

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        return {
            "success": True,
            "message": (
                f"Connected to {settings.destination_db_type}://"
                f"{settings.destination_db_host}/{settings.destination_db_name}"
            ),
        }
    except Exception as e:
        return {"success": False, "message": f"Connection failed: {str(e)}"}


@router.get("/schema")
async def get_schema() -> dict[str, Any]:
    """Get the schema of the destination database table.

    Returns column names, types, and nullability for the configured
    destination database table. This schema is used by the Dify workflow
    LLM to constrain its extraction output to only fields that match
    the database structure.
    """
    result = get_destination_db_schema()

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return result
