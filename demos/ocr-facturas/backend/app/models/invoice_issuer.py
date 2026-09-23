"""InvoiceIssuer SQLAlchemy ORM model.

Represents the issuer (emisor) of an Argentine invoice, stored in a
one-to-one relationship with the invoices table.
"""

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import UUID as SAUUID
from sqlalchemy import Date, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.invoice import Invoice


class InvoiceIssuer(UUIDPrimaryKeyMixin, Base):
    """ORM model for the invoice_issuers table.

    Stores the issuer (emisor) data for an invoice. One-to-one
    relationship with Invoice via unique constraint on invoice_id.

    Attributes:
        id: UUID primary key (server-generated).
        invoice_id: Foreign key to invoices.id (CASCADE delete).
        fantasy_name: Trade/fantasy name of the issuer.
        legal_name: Legal name (razón social) of the issuer.
        cuit: Argentine tax ID (format: XX-XXXXXXXX-X).
        fiscal_condition: Fiscal condition (e.g., "IVA Responsable Inscripto").
        address: Street address.
        locality: City/locality.
        province: Province/state.
        postal_code: Postal/ZIP code.
        phone: Phone number.
        activity_start: Date business activity started.
    """

    __tablename__ = "invoice_issuers"

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        SAUUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        doc="Foreign key to the parent invoice",
    )

    fantasy_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        doc="Trade/fantasy name of the issuer",
    )
    legal_name: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True,
        doc="Legal name (razón social) of the issuer",
    )
    cuit: Mapped[str | None] = mapped_column(
        String(13),
        nullable=True,
        doc="Argentine tax ID (format: XX-XXXXXXXX-X)",
    )
    fiscal_condition: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Fiscal condition (e.g., IVA Responsable Inscripto)",
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
    activity_start: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="Date business activity started",
    )

    # --- Relationships ---
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="issuer",
        doc="Parent invoice",
    )

    # --- Table constraints and indexes ---
    __table_args__ = (
        UniqueConstraint(
            "invoice_id",
            name="uq_invoice_issuers_invoice_id",
        ),
        Index(
            "ix_invoice_issuers_cuit",
            "cuit",
        ),
    )

    def __repr__(self) -> str:
        return f"<InvoiceIssuer(id={self.id}, cuit='{self.cuit}', fantasy_name='{self.fantasy_name}')>"
