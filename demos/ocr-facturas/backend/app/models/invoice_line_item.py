"""InvoiceLineItem SQLAlchemy ORM model.

Represents a single line item (product/service) on an Argentine invoice,
stored in a one-to-many relationship with the invoices table.
"""

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import UUID as SAUUID
from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.invoice import Invoice


class InvoiceLineItem(UUIDPrimaryKeyMixin, Base):
    """ORM model for the invoice_line_items table.

    Stores individual line items (products/services) for an invoice.
    One-to-many relationship with Invoice.

    Attributes:
        id: UUID primary key (server-generated).
        invoice_id: Foreign key to invoices.id (CASCADE delete).
        line_order: Line item order/sequence number (must be > 0).
        product_code: Product/service code.
        description: Line item description.
        quantity: Quantity of items.
        unit: Unit of measure.
        unit_price: Price per unit.
        discount: Discount amount.
        subtotal_without_iva: Subtotal before IVA.
        iva_rate: IVA rate applied (e.g., "21%", "10.5%", "27%").
        total_with_iva: Total including IVA.
    """

    __tablename__ = "invoice_line_items"

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        SAUUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        doc="Foreign key to the parent invoice",
    )

    line_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Line item order/sequence number (must be > 0)",
    )
    product_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Product/service code",
    )
    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="Line item description",
    )
    quantity: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
        doc="Quantity of items",
    )
    unit: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        doc="Unit of measure",
    )
    unit_price: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        nullable=True,
        doc="Price per unit",
    )
    discount: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        nullable=True,
        doc="Discount amount",
    )
    subtotal_without_iva: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        nullable=True,
        doc="Subtotal before IVA",
    )
    iva_rate: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        doc="IVA rate applied (e.g., 21%, 10.5%, 27%)",
    )
    total_with_iva: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        nullable=True,
        doc="Total including IVA",
    )

    # --- Relationships ---
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="line_items",
        doc="Parent invoice",
    )

    # --- Table constraints and indexes ---
    __table_args__ = (
        CheckConstraint(
            "line_order > 0",
            name="ck_line_items_line_order",
        ),
        Index(
            "ix_line_items_invoice_order",
            "invoice_id",
            "line_order",
        ),
    )

    def __repr__(self) -> str:
        return f"<InvoiceLineItem(id={self.id}, line_order={self.line_order}, description='{self.description}')>"
