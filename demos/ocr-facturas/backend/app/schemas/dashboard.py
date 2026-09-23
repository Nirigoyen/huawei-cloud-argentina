"""Pydantic schemas for Dashboard API responses."""

from decimal import Decimal

from pydantic import BaseModel, Field


class SupplierStats(BaseModel):
    """Statistics for a single supplier (issuer)."""

    fantasy_name: str | None = None
    legal_name: str | None = None
    cuit: str | None = None
    total_amount: Decimal = Field(default=Decimal("0"))
    invoice_count: int = 0


class MonthlyStats(BaseModel):
    """Spending statistics for a single month."""

    month: str = Field(description="Month in YYYY-MM format")
    total_amount: Decimal = Field(default=Decimal("0"))
    invoice_count: int = 0


class InvoiceTypeStats(BaseModel):
    """Count of invoices by type letter."""

    type_letter: str
    count: int = 0


class StatusSummary(BaseModel):
    """Summary of invoice counts by processing status."""

    processing: int = 0
    completed: int = 0
    failed: int = 0


class DashboardStats(BaseModel):
    """Complete dashboard statistics response."""

    total_invoices: int = 0
    total_spending: Decimal = Field(default=Decimal("0"))
    average_invoice_amount: Decimal = Field(default=Decimal("0"))
    invoices_by_type: dict[str, int] = Field(default_factory=dict)
    top_suppliers: list[SupplierStats] = Field(default_factory=list)
    monthly_trend: list[MonthlyStats] = Field(default_factory=list)
    status_summary: dict[str, int] = Field(default_factory=dict)
