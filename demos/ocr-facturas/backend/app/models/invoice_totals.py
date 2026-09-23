"""InvoiceTotals SQLAlchemy ORM model.

Represents the financial totals for an Argentine invoice, stored in a
one-to-one relationship with the invoices table.
"""

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy import UUID as SAUUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.invoice import Invoice


class InvoiceTotals(UUIDPrimaryKeyMixin, Base):
    """ORM model for the invoice_totals table.

    Stores financial totals for an invoice. One-to-one relationship
    with Invoice via unique constraint on invoice_id.

    The iva_detail JSONB column stores a structured IVA breakdown, e.g.:
    [{"rate": "21%", "amount": 2100.00}, {"rate": "10.5%", "amount": 500.00}]

    Attributes:
        id: UUID primary key (server-generated).
        invoice_id: Foreign key to invoices.id (CASCADE delete).
        net_amount: Net amount (before IVA and taxes).
        iva_amount: Total IVA amount.
        iva_detail: JSONB array with IVA rate/amount breakdown.
        other_taxes: Total of other taxes (not IVA).
        total_invoice_currency: Total in original invoice currency.
        total_ars: Total in Argentine Pesos (ARS).
    """

    __tablename__ = "invoice_totals"

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        SAUUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        doc="Foreign key to the parent invoice",
    )

    net_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        nullable=True,
        doc="Net amount (before IVA and taxes)",
    )
    iva_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        nullable=True,
        doc="Total IVA amount",
    )
    iva_detail: Mapped[Any] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
        doc="JSONB array with IVA rate/amount breakdown",
    )
    other_taxes: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        nullable=True,
        doc="Total of other taxes (not IVA)",
    )
    total_invoice_currency: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        nullable=True,
        doc="Total in original invoice currency",
    )
    total_ars: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        nullable=True,
        doc="Total in Argentine Pesos (ARS)",
    )

    # --- Relationships ---
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="totals",
        doc="Parent invoice",
    )

    # --- Table constraints ---
    __table_args__ = (
        UniqueConstraint(
            "invoice_id",
            name="uq_invoice_totals_invoice_id",
        ),
    )

    def __repr__(self) -> str:
        return f"<InvoiceTotals(id={self.id}, total_ars={self.total_ars})>"
