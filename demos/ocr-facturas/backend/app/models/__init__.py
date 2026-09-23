"""SQLAlchemy ORM models for OCR Facturas."""

from app.models.base import Base
from app.models.chatbot_query_log import ChatbotQueryLog
from app.models.invoice import Invoice
from app.models.invoice_client import InvoiceClient
from app.models.invoice_issuer import InvoiceIssuer
from app.models.invoice_line_item import InvoiceLineItem
from app.models.invoice_totals import InvoiceTotals
from app.models.settings import AppSettings

# Convenience alias for Alembic target_metadata
metadata = Base.metadata

__all__ = [
    "Base",
    "Invoice",
    "InvoiceIssuer",
    "InvoiceClient",
    "InvoiceLineItem",
    "InvoiceTotals",
    "ChatbotQueryLog",
    "AppSettings",
    "metadata",
]
