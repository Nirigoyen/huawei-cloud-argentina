"""Tests for Pydantic schema validation.

Covers:
- Invoice schemas: Create, Read, Detail, ListResponse, UploadResponse
- OCR schemas: DifyWorkflowResponse, OCRResult
- Chatbot schemas: ChatbotQueryRequest, IntentClassification, QueryResult
- Settings schemas: SettingsRead, SettingsUpdate, ConnectionTestRequest
- Dashboard schemas: DashboardStats, MonthlyStats
"""

import uuid
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.chatbot import (
    ChatbotQueryRequest,
    ChatbotQueryResponse,
    IntentClassification,
    QueryResult,
)
from app.schemas.dashboard import (
    DashboardStats,
    MonthlyStats,
    StatusSummary,
    SupplierStats,
)
from app.schemas.invoice import (
    ClientCreate,
    InvoiceCreate,
    InvoiceListParams,
    InvoiceUploadResponse,
    IssuerCreate,
    LineItemCreate,
    TotalsCreate,
)
from app.schemas.ocr import (
    DifyFileUploadResponse,
    DifyWorkflowData,
    DifyWorkflowResponse,
    OCRResponse,
    OCRResult,
)
from app.schemas.settings import (
    CREDENTIAL_MASK,
    ConnectionTestRequest,
    ConnectionTestResult,
    SettingsRead,
    SettingsUpdate,
    SettingsUpdateResponse,
)

# =============================================================================
# Invoice Schemas
# =============================================================================


class TestIssuerCreate:
    """Tests for IssuerCreate schema."""

    def test_all_optional_fields(self):
        issuer = IssuerCreate()
        assert issuer.fantasy_name is None
        assert issuer.legal_name is None
        assert issuer.cuit is None

    def test_with_values(self):
        issuer = IssuerCreate(
            fantasy_name="Test Corp",
            legal_name="Test Corp SA",
            cuit="20-12345678-9",
        )
        assert issuer.fantasy_name == "Test Corp"
        assert issuer.cuit == "20-12345678-9"


class TestClientCreate:
    """Tests for ClientCreate schema."""

    def test_all_optional_fields(self):
        client = ClientCreate()
        assert client.legal_name is None

    def test_with_values(self):
        client = ClientCreate(
            legal_name="Client SA",
            document_type="CUIT",
            document_number="30-87654321-0",
        )
        assert client.legal_name == "Client SA"
        assert client.document_type == "CUIT"


class TestLineItemCreate:
    """Tests for LineItemCreate schema."""

    def test_line_order_required(self):
        with pytest.raises(ValidationError):
            LineItemCreate()

    def test_with_minimal_data(self):
        item = LineItemCreate(line_order=1)
        assert item.line_order == 1
        assert item.discount == Decimal("0.00")

    def test_with_full_data(self):
        item = LineItemCreate(
            line_order=1,
            description="Product A",
            quantity=Decimal("2.00"),
            unit_price=Decimal("100.00"),
            iva_rate="21%",
            total_with_iva=Decimal("242.00"),
        )
        assert item.description == "Product A"
        assert item.quantity == Decimal("2.00")


class TestTotalsCreate:
    """Tests for TotalsCreate schema."""

    def test_defaults(self):
        totals = TotalsCreate()
        assert totals.other_taxes == Decimal("0.00")

    def test_with_values(self):
        totals = TotalsCreate(
            net_amount=Decimal("1000.00"),
            iva_amount=Decimal("210.00"),
            total_ars=Decimal("1210.00"),
        )
        assert totals.net_amount == Decimal("1000.00")


class TestInvoiceCreate:
    """Tests for InvoiceCreate schema."""

    def test_required_fields(self):
        with pytest.raises(ValidationError):
            InvoiceCreate()

    def test_with_required_fields(self):
        inv = InvoiceCreate(
            original_filename="test.pdf",
            file_size_bytes=1024,
            file_path="test/test.pdf",
        )
        assert inv.original_filename == "test.pdf"
        assert inv.validation_warnings == []
        assert inv.line_items == []

    def test_with_full_data(self):
        inv = InvoiceCreate(
            invoice_type="A",
            invoice_code="001",
            original_filename="test.pdf",
            file_size_bytes=1024,
            file_path="test/test.pdf",
            issuer=IssuerCreate(fantasy_name="Corp"),
            line_items=[LineItemCreate(line_order=1)],
        )
        assert inv.invoice_type == "A"
        assert inv.issuer.fantasy_name == "Corp"
        assert len(inv.line_items) == 1


class TestInvoiceListParams:
    """Tests for InvoiceListParams schema."""

    def test_defaults(self):
        params = InvoiceListParams()
        assert params.page == 1
        assert params.page_size == 20
        assert params.sort_by == "created_at"
        assert params.sort_order == "desc"

    def test_page_ge_1(self):
        with pytest.raises(ValidationError):
            InvoiceListParams(page=0)

    def test_page_size_bounds(self):
        with pytest.raises(ValidationError):
            InvoiceListParams(page_size=0)
        with pytest.raises(ValidationError):
            InvoiceListParams(page_size=101)


class TestInvoiceUploadResponse:
    """Tests for InvoiceUploadResponse schema."""

    def test_with_defaults(self):
        resp = InvoiceUploadResponse(
            invoice_id=uuid.uuid4(),
            status="processing",
        )
        assert resp.message == "Invoice uploaded and processing started"

    def test_custom_message(self):
        resp = InvoiceUploadResponse(
            invoice_id=uuid.uuid4(),
            status="processing",
            message="Custom message",
        )
        assert resp.message == "Custom message"


# =============================================================================
# OCR Schemas
# =============================================================================


class TestDifyFileUploadResponse:
    """Tests for DifyFileUploadResponse schema."""

    def test_with_required_fields(self):
        resp = DifyFileUploadResponse(
            id="file-123",
            name="test.pdf",
            size=1024,
            extension="pdf",
            mime_type="application/pdf",
        )
        assert resp.id == "file-123"
        assert resp.size == 1024


class TestDifyWorkflowResponse:
    """Tests for DifyWorkflowResponse schema."""

    def test_with_data(self):
        data = DifyWorkflowData(
            id="run-123",
            workflow_id="wf-456",
            status="succeeded",
            outputs={"respuesta_llm": "test output"},
        )
        resp = DifyWorkflowResponse(
            task_id="task-789",
            workflow_run_id="run-123",
            data=data,
        )
        assert resp.data.status == "succeeded"
        assert resp.data.outputs["respuesta_llm"] == "test output"


class TestOCRResult:
    """Tests for OCRResult schema."""

    def test_defaults(self):
        result = OCRResult()
        assert result.line_items == []
        assert result.validation_warnings == []
        assert result.invoice_type is None

    def test_with_values(self):
        result = OCRResult(
            invoice_type="A",
            invoice_code="001",
            point_of_sale="0003",
            invoice_number="00000456",
            issuer_cuit="20-12345678-9",
            total_ars="1210.00",
        )
        assert result.invoice_type == "A"
        assert result.issuer_cuit == "20-12345678-9"


class TestOCRResponse:
    """Tests for OCRResponse schema."""

    def test_with_result(self):
        resp = OCRResponse(
            invoice_id=uuid.uuid4(),
            status="completed",
            ocr_result=OCRResult(invoice_type="A"),
        )
        assert resp.status == "completed"
        assert resp.ocr_result.invoice_type == "A"

    def test_with_error(self):
        resp = OCRResponse(
            invoice_id=uuid.uuid4(),
            status="failed",
            error_message="Processing failed",
        )
        assert resp.error_message == "Processing failed"
        assert resp.ocr_result is None


# =============================================================================
# Chatbot Schemas
# =============================================================================


class TestChatbotQueryRequest:
    """Tests for ChatbotQueryRequest schema."""

    def test_valid_question(self):
        req = ChatbotQueryRequest(question="How much did we spend?")
        assert req.question == "How much did we spend?"

    def test_empty_question_raises(self):
        with pytest.raises(ValidationError):
            ChatbotQueryRequest(question="")

    def test_too_long_question_raises(self):
        with pytest.raises(ValidationError):
            ChatbotQueryRequest(question="x" * 1001)

    def test_max_length_question_ok(self):
        req = ChatbotQueryRequest(question="x" * 1000)
        assert len(req.question) == 1000


class TestIntentClassification:
    """Tests for IntentClassification schema."""

    def test_defaults(self):
        ic = IntentClassification()
        assert ic.intent is None
        assert ic.parameters == {}
        assert ic.is_read_only is True

    def test_with_values(self):
        ic = IntentClassification(
            intent="total_spending",
            parameters={"start_date": "2024-01-01", "end_date": "2024-12-31"},
        )
        assert ic.intent == "total_spending"
        assert ic.is_read_only is True


class TestQueryResult:
    """Tests for QueryResult schema."""

    def test_defaults(self):
        qr = QueryResult(intent="total_spending", parameters={})
        assert qr.rows == []
        assert qr.row_count == 0
        assert qr.execution_time_ms is None

    def test_with_rows(self):
        qr = QueryResult(
            intent="total_spending",
            parameters={},
            rows=[{"total": 1000}],
            row_count=1,
            execution_time_ms=42.5,
        )
        assert qr.row_count == 1
        assert qr.execution_time_ms == 42.5


class TestChatbotQueryResponse:
    """Tests for ChatbotQueryResponse schema."""

    def test_with_values(self):
        resp = ChatbotQueryResponse(
            response="Total spending: ARS 100,000",
            intent="total_spending",
            query_log_id=uuid.uuid4(),
        )
        assert resp.intent == "total_spending"


# =============================================================================
# Settings Schemas
# =============================================================================


class TestSettingsRead:
    """Tests for SettingsRead schema."""

    def test_defaults(self):
        sr = SettingsRead()
        assert sr.huawei_iam_username is None
        assert sr.dify_api_key is None

    def test_with_masked_values(self):
        sr = SettingsRead(
            huawei_iam_username=CREDENTIAL_MASK,
            dify_api_key=CREDENTIAL_MASK,
        )
        assert sr.huawei_iam_username == CREDENTIAL_MASK


class TestSettingsUpdate:
    """Tests for SettingsUpdate schema."""

    def test_defaults(self):
        su = SettingsUpdate()
        assert su.huawei_iam_username is None
        assert su.dify_api_key is None

    def test_with_values(self):
        su = SettingsUpdate(
            dify_api_key="new-key",
            dify_base_url="http://new-dify:80",
        )
        assert su.dify_api_key == "new-key"


class TestConnectionTestRequest:
    """Tests for ConnectionTestRequest schema."""

    def test_valid_service(self):
        req = ConnectionTestRequest(service="dify")
        assert req.service == "dify"

    def test_service_required(self):
        with pytest.raises(ValidationError):
            ConnectionTestRequest()


class TestConnectionTestResult:
    """Tests for ConnectionTestResult schema."""

    def test_success(self):
        result = ConnectionTestResult(
            service="dify",
            success=True,
            message="Reachable",
            latency_ms=42,
        )
        assert result.success is True
        assert result.latency_ms == 42

    def test_failure(self):
        result = ConnectionTestResult(
            service="huawei_iam",
            success=False,
            message="Not configured",
        )
        assert result.success is False
        assert result.latency_ms is None


class TestSettingsUpdateResponse:
    """Tests for SettingsUpdateResponse schema."""

    def test_defaults(self):
        resp = SettingsUpdateResponse()
        assert resp.message == "Settings updated successfully"
        assert resp.updated_fields == []

    def test_with_updated_fields(self):
        resp = SettingsUpdateResponse(updated_fields=["dify_api_key", "dify_base_url"])
        assert len(resp.updated_fields) == 2


# =============================================================================
# Dashboard Schemas
# =============================================================================


class TestDashboardStats:
    """Tests for DashboardStats schema."""

    def test_defaults(self):
        stats = DashboardStats()
        assert stats.total_invoices == 0
        assert stats.total_spending == Decimal("0")
        assert stats.invoices_by_type == {}
        assert stats.top_suppliers == []
        assert stats.monthly_trend == []
        assert stats.status_summary == {}


class TestMonthlyStats:
    """Tests for MonthlyStats schema."""

    def test_with_values(self):
        ms = MonthlyStats(month="2024-01", total_amount=Decimal("5000"), invoice_count=10)
        assert ms.month == "2024-01"
        assert ms.invoice_count == 10


class TestSupplierStats:
    """Tests for SupplierStats schema."""

    def test_defaults(self):
        ss = SupplierStats()
        assert ss.total_amount == Decimal("0")
        assert ss.invoice_count == 0


class TestStatusSummary:
    """Tests for StatusSummary schema."""

    def test_defaults(self):
        ss = StatusSummary()
        assert ss.processing == 0
        assert ss.completed == 0
        assert ss.failed == 0
