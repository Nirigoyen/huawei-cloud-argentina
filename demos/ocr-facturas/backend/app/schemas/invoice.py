"""Pydantic schemas for Invoice API requests and responses."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# --- Create schemas (for OCR extraction input) ---


class IssuerCreate(BaseModel):
    fantasy_name: str | None = None
    legal_name: str | None = None
    cuit: str | None = None
    fiscal_condition: str | None = None
    address: str | None = None
    locality: str | None = None
    province: str | None = None
    postal_code: str | None = None
    phone: str | None = None
    activity_start: date | None = None


class ClientCreate(BaseModel):
    legal_name: str | None = None
    document_type: str | None = None
    document_number: str | None = None
    fiscal_condition: str | None = None
    address: str | None = None
    locality: str | None = None
    province: str | None = None
    postal_code: str | None = None
    phone: str | None = None
    sale_condition: str | None = None


class LineItemCreate(BaseModel):
    line_order: int
    product_code: str | None = None
    description: str | None = None
    quantity: Decimal | None = None
    unit: str | None = None
    unit_price: Decimal | None = None
    discount: Decimal | None = Field(default=Decimal("0.00"))
    subtotal_without_iva: Decimal | None = None
    iva_rate: str | None = None
    total_with_iva: Decimal | None = None


class TotalsCreate(BaseModel):
    net_amount: Decimal | None = None
    iva_amount: Decimal | None = None
    iva_detail: Any | None = None
    other_taxes: Decimal | None = Field(default=Decimal("0.00"))
    total_invoice_currency: Decimal | None = None
    total_ars: Decimal | None = None


# --- Read schemas (sub-sections) ---


class IssuerSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    invoice_id: uuid.UUID
    fantasy_name: str | None = None
    legal_name: str | None = None
    cuit: str | None = None
    fiscal_condition: str | None = None
    address: str | None = None
    locality: str | None = None
    province: str | None = None
    postal_code: str | None = None
    phone: str | None = None
    activity_start: date | None = None


class ClientSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    invoice_id: uuid.UUID
    legal_name: str | None = None
    document_type: str | None = None
    document_number: str | None = None
    fiscal_condition: str | None = None
    address: str | None = None
    locality: str | None = None
    province: str | None = None
    postal_code: str | None = None
    phone: str | None = None
    sale_condition: str | None = None


class LineItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    invoice_id: uuid.UUID
    line_order: int
    product_code: str | None = None
    description: str | None = None
    quantity: Decimal | None = None
    unit: str | None = None
    unit_price: Decimal | None = None
    discount: Decimal | None = None
    subtotal_without_iva: Decimal | None = None
    iva_rate: str | None = None
    total_with_iva: Decimal | None = None


class TotalsSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    invoice_id: uuid.UUID
    net_amount: Decimal | None = None
    iva_amount: Decimal | None = None
    iva_detail: Any | None = None
    other_taxes: Decimal | None = None
    total_invoice_currency: Decimal | None = None
    total_ars: Decimal | None = None


# --- Main schemas ---


class InvoiceCreate(BaseModel):
    invoice_type: str | None = None
    invoice_code: str | None = None
    point_of_sale: str | None = None
    invoice_number: str | None = None
    complete_number: str | None = None
    issue_date: date | None = None
    currency: str | None = None
    exchange_rate: str | None = None
    cae: str | None = None
    cae_expiry_date: date | None = None
    original_filename: str
    file_size_bytes: int
    file_path: str
    validation_warnings: list[str] = Field(default_factory=list)
    issuer: IssuerCreate | None = None
    client: ClientCreate | None = None
    line_items: list[LineItemCreate] = Field(default_factory=list)
    totals: TotalsCreate | None = None


class InvoiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    status: str
    invoice_type: str | None = None
    invoice_code: str | None = None
    point_of_sale: str | None = None
    invoice_number: str | None = None
    complete_number: str | None = None
    issue_date: date | None = None
    currency: str | None = None
    cae: str | None = None
    original_filename: str
    file_size_bytes: int
    created_at: datetime
    processed_at: datetime | None = None
    validation_warnings: Any = Field(default_factory=list)
    issuer_name: str | None = None
    total_amount: Decimal | None = None


class InvoiceDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    status: str
    invoice_type: str | None = None
    invoice_code: str | None = None
    point_of_sale: str | None = None
    invoice_number: str | None = None
    complete_number: str | None = None
    issue_date: date | None = None
    currency: str | None = None
    exchange_rate: str | None = None
    cae: str | None = None
    cae_expiry_date: date | None = None
    original_filename: str
    file_size_bytes: int
    file_path: str
    ocr_status_code: int | None = None
    text_blocks_count: int | None = None
    validation_warnings: Any = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    processed_at: datetime | None = None
    issuer: IssuerSchema | None = None
    client: ClientSchema | None = None
    line_items: list[LineItemSchema] = Field(default_factory=list)
    totals: TotalsSchema | None = None


class InvoiceListResponse(BaseModel):
    items: list[InvoiceRead]
    total: int
    page: int
    page_size: int
    total_pages: int


class InvoiceUploadResponse(BaseModel):
    invoice_id: uuid.UUID
    status: str
    message: str = "Invoice uploaded and processing started"


class InvoiceRetryResponse(BaseModel):
    invoice_id: uuid.UUID
    status: str = "processing"
    message: str = "OCR processing restarted"


class InvoiceListParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    status: str | None = None
    invoice_type: str | None = None
    sort_by: str = Field(default="created_at")
    sort_order: str = Field(default="desc")
