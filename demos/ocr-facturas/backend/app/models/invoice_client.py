"""InvoiceClient SQLAlchemy ORM model.

Represents the client/receiver (receptor) of an Argentine invoice,
stored in a one-to-one relationship with the invoices table.
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import UUID as SAUUID
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.invoice import Invoice


class InvoiceClient(UUIDPrimaryKeyMixin, Base):
    """ORM model for the invoice_clients table.

    Stores the client/receiver (receptor) data for an invoice.
    One-to-one relationship with Invoice via unique constraint on invoice_id.

    Attributes:
        id: UUID primary key (server-generated).
        invoice_id: Foreign key to invoices.id (CASCADE delete).
        legal_name: Legal name of the client.
        document_type: Type of identification document.
        document_number: Identification document number.
        fiscal_condition: Fiscal condition of the client.
        address: Street address.
        locality: City/locality.
        province: Province/state.
        postal_code: Postal/ZIP code.
        phone: Phone number.
        sale_condition: Sale condition (e.g., "Contado", "30 días").
    """

    __tablename__ = "invoice_clients"

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        SAUUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        doc="Foreign key to the parent invoice",
    )

    legal_name: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True,
        doc="Legal name of the client",
    )
    document_type: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        doc="Type of identification document",
    )
    document_number: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        doc="Identification document number",
    )
    fiscal_condition: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Fiscal condition of the client",
    )
    address: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True,
        doc="Street address",
    )
    locality: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="City/locality",
    )
    province: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Province/state",
    )
    postal_code: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        doc="Postal/ZIP code",
    )
    phone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Phone number",
    )
    sale_condition: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Sale condition (e.g., Contado, 30 días)",
    )

    # --- Relationships ---
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="client",
        doc="Parent invoice",
    )

    # --- Table constraints ---
    __table_args__ = (
        UniqueConstraint(
            "invoice_id",
            name="uq_invoice_clients_invoice_id",
        ),
    )

    def __repr__(self) -> str:
        return f"<InvoiceClient(id={self.id}, legal_name='{self.legal_name}')>"
