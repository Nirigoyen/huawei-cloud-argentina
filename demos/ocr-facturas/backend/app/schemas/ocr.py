"""Pydantic schemas for OCR processing and Dify API responses."""

import uuid
from typing import Any

from pydantic import BaseModel, Field


class DifyFileUploadResponse(BaseModel):
    """Response from Dify file upload API (POST /v1/files/upload)."""

    id: str = Field(description="Dify file ID (upload_file_id)")
    name: str = Field(description="Original file name")
    size: int = Field(description="File size in bytes")
    extension: str = Field(description="File extension")
    mime_type: str = Field(description="MIME type")
    created_by: str | None = None
    created_at: Any | None = None  # Dify 1.0.0 returns int (Unix timestamp), not string


class DifyWorkflowInputs(BaseModel):
    """Inputs for Dify workflow run."""

    archivo: dict[str, str] = Field(
        description="File reference for the workflow",
    )


class DifyWorkflowRunRequest(BaseModel):
    """Request body for Dify workflow run API (POST /v1/workflows/run)."""

    inputs: dict[str, Any]
    response_mode: str = "blocking"
    user: str = "ocr-facturas-backend"


class DifyWorkflowData(BaseModel):
    """Workflow run data from Dify response."""

    id: str
    workflow_id: str
    status: str
    outputs: dict[str, Any] | None = None
    error: str | None = None
    elapsed_time: float | None = None
    total_tokens: int | None = None
    total_steps: int | None = None
    created_at: Any | None = None  # Dify 1.0.0 returns int (Unix timestamp), not string
    finished_at: Any | None = None


class DifyWorkflowResponse(BaseModel):
    """Response from Dify workflow run API."""

    task_id: str
    workflow_run_id: str
    data: DifyWorkflowData


class OCRResult(BaseModel):
    """Structured result from OCR extraction.

    Parsed from the LLM text output in the Dify workflow response.
    """

    invoice_type: str | None = None
    invoice_code: str | None = None
    point_of_sale: str | None = None
    invoice_number: str | None = None
    complete_number: str | None = None
    issue_date: str | None = None
    currency: str | None = None
    exchange_rate: str | None = None
    cae: str | None = None
    cae_expiry_date: str | None = None

    # Issuer
    issuer_fantasy_name: str | None = None
    issuer_legal_name: str | None = None
    issuer_cuit: str | None = None
    issuer_fiscal_condition: str | None = None
    issuer_address: str | None = None
    issuer_locality: str | None = None
    issuer_province: str | None = None
    issuer_postal_code: str | None = None
    issuer_phone: str | None = None
    issuer_activity_start: str | None = None

    # Client
    client_legal_name: str | None = None
    client_document_type: str | None = None
    client_document_number: str | None = None
    client_fiscal_condition: str | None = None
    client_address: str | None = None
    client_locality: str | None = None
    client_province: str | None = None
    client_postal_code: str | None = None
    client_phone: str | None = None
    client_sale_condition: str | None = None

    # Line items (parsed from table)
    line_items: list[dict[str, Any]] = Field(default_factory=list)

    # Totals
    net_amount: str | None = None
    iva_amount: str | None = None
    iva_detail: list[dict[str, Any]] | None = None
    other_taxes: str | None = None
    total_invoice_currency: str | None = None
    total_ars: str | None = None

    # Raw text for debugging
    raw_text: str | None = None
    validation_warnings: list[str] = Field(default_factory=list)


class OCRResponse(BaseModel):
    """Response from the OCR processing pipeline."""

    invoice_id: uuid.UUID
    status: str
    ocr_result: OCRResult | None = None
    error_message: str | None = None
