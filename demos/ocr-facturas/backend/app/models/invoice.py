"""Invoice SQLAlchemy ORM model.

Represents the main invoice record with processing status, file metadata,
and extracted invoice header fields.
"""

from datetime import date, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Date,
    DateTime,
    Index,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.invoice_client import InvoiceClient
    from app.models.invoice_issuer import InvoiceIssuer
    from app.models.invoice_line_item import InvoiceLineItem
    from app.models.invoice_totals import InvoiceTotals


class Invoice(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """ORM model for the invoices table.

    Stores the main invoice record including processing status,
    file metadata, and extracted invoice header fields.

    Attributes:
        id: UUID primary key (server-generated via gen_random_uuid()).
        status: Processing status - 'processing', 'completed', or 'failed'.
        invoice_type: Invoice letter (A, B, C, E, M).
        invoice_code: Three-digit AFIP fiscal document code.
        point_of_sale: Point-of-sale number (4 digits, zero-padded).
        invoice_number: Invoice number (8 digits, zero-padded).
        complete_number: Full invoice number (e.g., "0003-00000456").
        issue_date: Date the invoice was issued.
        currency: Currency code (ARS, USD, EUR).
        exchange_rate: Exchange rate if currency is not ARS.
        cae: Electronic Authorization Code (14 digits).
        cae_expiry_date: CAE expiration date.
        original_filename: Original uploaded file name.
        file_size_bytes: File size in bytes.
        file_path: Relative path to stored file.
        ocr_status_code: OCR service response status code.
        text_blocks_count: Number of text blocks detected by OCR.
        validation_warnings: JSONB array of validation warnings.
        created_at: Record creation timestamp.
        processed_at: Timestamp when processing completed/failed.
    """

    __tablename__ = "invoices"

    # --- Processing status ---
    status: Mapped[str] = mapped_column(
        String(12),
        nullable=False,
        server_default="processing",
        doc="Processing status: processing, completed, or failed",
    )

    # --- Invoice header fields (extracted via OCR) ---
    invoice_type: Mapped[str | None] = mapped_column(
        String(1),
        nullable=True,
        doc="Invoice letter: A, B, C, E, or M",
    )
    invoice_code: Mapped[str | None] = mapped_column(
        String(3),
        nullable=True,
        doc="Three-digit AFIP fiscal document code",
    )
    point_of_sale: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        doc="Point-of-sale number (4 digits, zero-padded)",
    )
    invoice_number: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        doc="Invoice number (8 digits, zero-padded)",
    )
    complete_number: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        doc="Full invoice number (e.g., 0003-00000456)",
    )
    issue_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="Date the invoice was issued",
    )
    currency: Mapped[str | None] = mapped_column(
        String(3),
        nullable=True,
        doc="Currency code: ARS, USD, or EUR",
    )
    exchange_rate: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Exchange rate if currency is not ARS",
    )

    # --- Authorization fields ---
    cae: Mapped[str | None] = mapped_column(
        String(14),
        nullable=True,
        doc="Electronic Authorization Code (14 digits)",
    )
    cae_expiry_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="CAE expiration date",
    )

    # --- File metadata ---
    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Original uploaded file name",
    )
    file_size_bytes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="File size in bytes",
    )
    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Relative path to stored file",
    )

    # --- OCR metadata ---
    ocr_status_code: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        doc="OCR service response status code",
    )
    text_blocks_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        doc="Number of text blocks detected by OCR",
    )

    # --- Validation ---
    validation_warnings: Mapped[Any] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        server_default="[]",
        doc="JSONB array of validation warning strings",
    )

    # --- Timestamps ---
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when processing completed or failed",
    )

    # --- Relationships ---
    issuer: Mapped["InvoiceIssuer | None"] = relationship(
        "InvoiceIssuer",
        back_populates="invoice",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
        doc="Invoice issuer (one-to-one)",
    )

    client: Mapped["InvoiceClient | None"] = relationship(
        "InvoiceClient",
        back_populates="invoice",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
        doc="Invoice client/receiver (one-to-one)",
    )

    line_items: Mapped[list["InvoiceLineItem"]] = relationship(
        "InvoiceLineItem",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="InvoiceLineItem.line_order",
        doc="Invoice line items (one-to-many)",
    )

    totals: Mapped["InvoiceTotals | None"] = relationship(
        "InvoiceTotals",
        back_populates="invoice",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
        doc="Invoice totals (one-to-one)",
    )

    # --- Table constraints ---
    __table_args__ = (
        CheckConstraint(
            "status IN ('processing', 'completed', 'failed')",
            name="ck_invoices_status",
        ),
        CheckConstraint(
            "file_size_bytes > 0 AND file_size_bytes <= 15728640",
            name="ck_invoices_file_size",
        ),
        Index("ix_invoices_status", "status"),
        Index("ix_invoices_created_at", "created_at", postgresql_using="btree"),
        Index("ix_invoices_complete_number", "complete_number"),
        Index("ix_invoices_invoice_type", "invoice_type"),
    )

    def __repr__(self) -> str:
        return f"<Invoice(id={self.id}, status='{self.status}', complete_number='{self.complete_number}')>"
