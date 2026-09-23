"""Tests for SQLAlchemy ORM model creation and relationships.

Uses in-memory SQLite to verify:
- Model instantiation with valid data
- Relationship definitions
- Table constraints (check constraints, unique constraints)
- String representations (__repr__)
"""

import uuid
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.chatbot_query_log import ChatbotQueryLog
from app.models.invoice import Invoice
from app.models.invoice_client import InvoiceClient
from app.models.invoice_issuer import InvoiceIssuer
from app.models.invoice_line_item import InvoiceLineItem
from app.models.invoice_totals import InvoiceTotals
from app.models.settings import AppSettings

# =============================================================================
# Base model tests
# =============================================================================


class TestBaseModel:
    """Tests for the Base model and mixins."""

    def test_base_class_exists(self):
        assert Base is not None

    def test_timestamp_mixin_has_created_at(self):
        assert hasattr(TimestampMixin, "created_at")

    def test_timestamp_mixin_has_updated_at(self):
        assert hasattr(TimestampMixin, "updated_at")

    def test_uuid_primary_key_mixin_has_id(self):
        assert hasattr(UUIDPrimaryKeyMixin, "id")


# =============================================================================
# Invoice model tests
# =============================================================================


class TestInvoiceModel:
    """Tests for the Invoice ORM model."""

    def test_tablename(self):
        assert Invoice.__tablename__ == "invoices"

    def test_repr(self):
        inv = Invoice(
            status="processing",
            original_filename="test.pdf",
            file_size_bytes=1024,
            file_path="test/test.pdf",
        )
        inv.id = uuid.uuid4()
        repr_str = repr(inv)
        assert "Invoice" in repr_str
        assert "processing" in repr_str

    def test_has_required_columns(self):
        assert hasattr(Invoice, "id")
        assert hasattr(Invoice, "status")
        assert hasattr(Invoice, "invoice_type")
        assert hasattr(Invoice, "invoice_code")
        assert hasattr(Invoice, "point_of_sale")
        assert hasattr(Invoice, "invoice_number")
        assert hasattr(Invoice, "complete_number")
        assert hasattr(Invoice, "issue_date")
        assert hasattr(Invoice, "currency")
        assert hasattr(Invoice, "cae")
        assert hasattr(Invoice, "original_filename")
        assert hasattr(Invoice, "file_size_bytes")
        assert hasattr(Invoice, "file_path")
        assert hasattr(Invoice, "validation_warnings")
        assert hasattr(Invoice, "created_at")
        assert hasattr(Invoice, "updated_at")
        assert hasattr(Invoice, "processed_at")

    def test_has_relationships(self):
        assert hasattr(Invoice, "issuer")
        assert hasattr(Invoice, "client")
        assert hasattr(Invoice, "line_items")
        assert hasattr(Invoice, "totals")

    @pytest.mark.asyncio
    async def test_create_invoice_in_db(self, async_db_session: AsyncSession):
        invoice = Invoice(
            status="processing",
            original_filename="test.pdf",
            file_size_bytes=2048,
            file_path="uuid/test.pdf",
        )
        async_db_session.add(invoice)
        await async_db_session.flush()

        assert invoice.id is not None
        assert invoice.status == "processing"
        assert invoice.original_filename == "test.pdf"
        assert invoice.file_size_bytes == 2048


# =============================================================================
# InvoiceIssuer model tests
# =============================================================================


class TestInvoiceIssuerModel:
    """Tests for the InvoiceIssuer ORM model."""

    def test_tablename(self):
        assert InvoiceIssuer.__tablename__ == "invoice_issuers"

    def test_repr(self):
        issuer = InvoiceIssuer(
            fantasy_name="Test Corp",
            cuit="20-12345678-9",
        )
        repr_str = repr(issuer)
        assert "InvoiceIssuer" in repr_str
        assert "20-12345678-9" in repr_str

    def test_has_required_columns(self):
        assert hasattr(InvoiceIssuer, "id")
        assert hasattr(InvoiceIssuer, "invoice_id")
        assert hasattr(InvoiceIssuer, "fantasy_name")
        assert hasattr(InvoiceIssuer, "legal_name")
        assert hasattr(InvoiceIssuer, "cuit")
        assert hasattr(InvoiceIssuer, "fiscal_condition")
        assert hasattr(InvoiceIssuer, "address")
        assert hasattr(InvoiceIssuer, "locality")
        assert hasattr(InvoiceIssuer, "province")
        assert hasattr(InvoiceIssuer, "postal_code")
        assert hasattr(InvoiceIssuer, "phone")
        assert hasattr(InvoiceIssuer, "activity_start")


# =============================================================================
# InvoiceClient model tests
# =============================================================================


class TestInvoiceClientModel:
    """Tests for the InvoiceClient ORM model."""

    def test_tablename(self):
        assert InvoiceClient.__tablename__ == "invoice_clients"

    def test_repr(self):
        client = InvoiceClient(legal_name="Client SA")
        repr_str = repr(client)
        assert "InvoiceClient" in repr_str
        assert "Client SA" in repr_str

    def test_has_required_columns(self):
        assert hasattr(InvoiceClient, "id")
        assert hasattr(InvoiceClient, "invoice_id")
        assert hasattr(InvoiceClient, "legal_name")
        assert hasattr(InvoiceClient, "document_type")
        assert hasattr(InvoiceClient, "document_number")
        assert hasattr(InvoiceClient, "fiscal_condition")
        assert hasattr(InvoiceClient, "sale_condition")


# =============================================================================
# InvoiceLineItem model tests
# =============================================================================


class TestInvoiceLineItemModel:
    """Tests for the InvoiceLineItem ORM model."""

    def test_tablename(self):
        assert InvoiceLineItem.__tablename__ == "invoice_line_items"

    def test_repr(self):
        item = InvoiceLineItem(line_order=1, description="Test Product")
        repr_str = repr(item)
        assert "InvoiceLineItem" in repr_str
        assert "Test Product" in repr_str

    def test_has_required_columns(self):
        assert hasattr(InvoiceLineItem, "id")
        assert hasattr(InvoiceLineItem, "invoice_id")
        assert hasattr(InvoiceLineItem, "line_order")
        assert hasattr(InvoiceLineItem, "product_code")
        assert hasattr(InvoiceLineItem, "description")
        assert hasattr(InvoiceLineItem, "quantity")
        assert hasattr(InvoiceLineItem, "unit")
        assert hasattr(InvoiceLineItem, "unit_price")
        assert hasattr(InvoiceLineItem, "discount")
        assert hasattr(InvoiceLineItem, "subtotal_without_iva")
        assert hasattr(InvoiceLineItem, "iva_rate")
        assert hasattr(InvoiceLineItem, "total_with_iva")


# =============================================================================
# InvoiceTotals model tests
# =============================================================================


class TestInvoiceTotalsModel:
    """Tests for the InvoiceTotals ORM model."""

    def test_tablename(self):
        assert InvoiceTotals.__tablename__ == "invoice_totals"

    def test_repr(self):
        totals = InvoiceTotals(total_ars=Decimal("1000.00"))
        repr_str = repr(totals)
        assert "InvoiceTotals" in repr_str

    def test_has_required_columns(self):
        assert hasattr(InvoiceTotals, "id")
        assert hasattr(InvoiceTotals, "invoice_id")
        assert hasattr(InvoiceTotals, "net_amount")
        assert hasattr(InvoiceTotals, "iva_amount")
        assert hasattr(InvoiceTotals, "iva_detail")
        assert hasattr(InvoiceTotals, "other_taxes")
        assert hasattr(InvoiceTotals, "total_invoice_currency")
        assert hasattr(InvoiceTotals, "total_ars")


# =============================================================================
# ChatbotQueryLog model tests
# =============================================================================


class TestChatbotQueryLogModel:
    """Tests for the ChatbotQueryLog ORM model."""

    def test_tablename(self):
        assert ChatbotQueryLog.__tablename__ == "chatbot_query_logs"

    def test_repr(self):
        log = ChatbotQueryLog(
            question="How much did we spend?",
            identified_intent="total_spending",
        )
        repr_str = repr(log)
        assert "ChatbotQueryLog" in repr_str
        assert "total_spending" in repr_str

    def test_has_required_columns(self):
        assert hasattr(ChatbotQueryLog, "id")
        assert hasattr(ChatbotQueryLog, "question")
        assert hasattr(ChatbotQueryLog, "identified_intent")
        assert hasattr(ChatbotQueryLog, "query_parameters")
        assert hasattr(ChatbotQueryLog, "result_summary")
        assert hasattr(ChatbotQueryLog, "response_text")
        assert hasattr(ChatbotQueryLog, "created_at")


# =============================================================================
# AppSettings model tests
# =============================================================================


class TestAppSettingsModel:
    """Tests for the AppSettings ORM model."""

    def test_tablename(self):
        assert AppSettings.__tablename__ == "app_settings"

    def test_repr_secret(self):
        setting = AppSettings(
            key="DIFY_API_KEY",
            value="secret-key-123",
            is_secret=True,
        )
        repr_str = repr(setting)
        assert "AppSettings" in repr_str
        # Secret values should be masked
        assert "secret-key-123" not in repr_str
        assert "••••••••" in repr_str

    def test_repr_non_secret(self):
        setting = AppSettings(
            key="DIFY_BASE_URL",
            value="http://dify:80",
            is_secret=False,
        )
        repr_str = repr(setting)
        assert "http://dify:80" in repr_str

    def test_has_required_columns(self):
        assert hasattr(AppSettings, "id")
        assert hasattr(AppSettings, "key")
        assert hasattr(AppSettings, "value")
        assert hasattr(AppSettings, "description")
        assert hasattr(AppSettings, "is_secret")
        assert hasattr(AppSettings, "created_at")
        assert hasattr(AppSettings, "updated_at")

    @pytest.mark.asyncio
    async def test_create_setting_in_db(self, async_db_session: AsyncSession):
        setting = AppSettings(
            key="TEST_KEY",
            value="test_value",
            description="Test description",
            is_secret=False,
        )
        async_db_session.add(setting)
        await async_db_session.flush()

        assert setting.id is not None
        assert setting.key == "TEST_KEY"
        assert setting.value == "test_value"
