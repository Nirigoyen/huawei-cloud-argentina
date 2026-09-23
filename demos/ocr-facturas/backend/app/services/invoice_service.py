"""Invoice CRUD service operations."""

import math
import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import RecordNotFoundError
from app.models.invoice import Invoice
from app.models.invoice_client import InvoiceClient
from app.models.invoice_issuer import InvoiceIssuer
from app.models.invoice_line_item import InvoiceLineItem
from app.models.invoice_totals import InvoiceTotals
from app.schemas.invoice import InvoiceCreate, InvoiceListResponse, InvoiceRead


async def create_invoice(db: AsyncSession, data: InvoiceCreate) -> Invoice:
    """Create a new invoice record with all nested data.

    Args:
        db: Async database session.
        data: Invoice creation data from OCR extraction.

    Returns:
        The created Invoice ORM object with id populated.
    """
    invoice = Invoice(
        status="processing",
        invoice_type=data.invoice_type,
        invoice_code=data.invoice_code,
        point_of_sale=data.point_of_sale,
        invoice_number=data.invoice_number,
        complete_number=data.complete_number,
        issue_date=data.issue_date,
        currency=data.currency,
        exchange_rate=data.exchange_rate,
        cae=data.cae,
        cae_expiry_date=data.cae_expiry_date,
        original_filename=data.original_filename,
        file_size_bytes=data.file_size_bytes,
        file_path=data.file_path,
        validation_warnings=data.validation_warnings,
    )
    db.add(invoice)
    await db.flush()
    await db.refresh(invoice)

    # Create issuer if provided
    if data.issuer:
        issuer = InvoiceIssuer(invoice_id=invoice.id, **data.issuer.model_dump())
        db.add(issuer)

    # Create client if provided
    if data.client:
        client = InvoiceClient(invoice_id=invoice.id, **data.client.model_dump())
        db.add(client)

    # Create line items
    for item_data in data.line_items:
        item = InvoiceLineItem(invoice_id=invoice.id, **item_data.model_dump())
        db.add(item)

    # Create totals if provided
    if data.totals:
        totals = InvoiceTotals(invoice_id=invoice.id, **data.totals.model_dump())
        db.add(totals)

    await db.flush()
    return invoice


async def get_invoice(db: AsyncSession, invoice_id: uuid.UUID) -> Invoice:
    """Get a single invoice by ID with all nested relationships.

    Args:
        db: Async database session.
        invoice_id: UUID of the invoice.

    Returns:
        The Invoice ORM object with issuer, client, line_items, totals.

    Raises:
        RecordNotFoundError: If the invoice does not exist.
    """
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.unique().scalar_one_or_none()
    if invoice is None:
        raise RecordNotFoundError(f"Invoice with id {invoice_id} not found")
    return invoice


async def list_invoices(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    invoice_type: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> InvoiceListResponse:
    """List invoices with pagination, filtering, and sorting.

    Args:
        db: Async database session.
        page: Page number (1-indexed).
        page_size: Items per page.
        status: Optional status filter.
        invoice_type: Optional invoice type filter.
        sort_by: Sort field name.
        sort_order: Sort direction ('asc' or 'desc').

    Returns:
        Paginated InvoiceListResponse.
    """
    # Build query with filters
    query = select(Invoice)
    count_query = select(func.count()).select_from(Invoice)

    if status:
        query = query.where(Invoice.status == status)
        count_query = count_query.where(Invoice.status == status)

    if invoice_type:
        query = query.where(Invoice.invoice_type == invoice_type)
        count_query = count_query.where(Invoice.invoice_type == invoice_type)

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply sorting
    sort_column = getattr(Invoice, sort_by, Invoice.created_at)
    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    invoices = result.unique().scalars().all()

    total_pages = math.ceil(total / page_size) if total > 0 else 0

    items = []
    for inv in invoices:
        item = InvoiceRead.model_validate(inv)
        item.issuer_name = (inv.issuer.fantasy_name or inv.issuer.legal_name) if inv.issuer else None
        item.total_amount = inv.totals.total_ars if inv.totals else None
        items.append(item)

    return InvoiceListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


async def update_invoice_status(
    db: AsyncSession,
    invoice_id: uuid.UUID,
    status: str,
    processed_at: datetime | None = None,
) -> Invoice:
    """Update the processing status of an invoice.

    Args:
        db: Async database session.
        invoice_id: UUID of the invoice.
        status: New status ('processing', 'completed', 'failed').
        processed_at: Timestamp of processing completion.

    Returns:
        The updated Invoice ORM object.

    Raises:
        RecordNotFoundError: If the invoice does not exist.
    """
    invoice = await get_invoice(db, invoice_id)
    invoice.status = status
    if processed_at:
        invoice.processed_at = processed_at
    elif status in ("completed", "failed"):
        invoice.processed_at = datetime.utcnow()
    await db.flush()
    await db.refresh(invoice)
    return invoice


async def delete_invoice(db: AsyncSession, invoice_id: uuid.UUID) -> None:
    """Delete an invoice and all its nested data.

    Cascading deletes will handle issuer, client, line items, totals.

    Args:
        db: Async database session.
        invoice_id: UUID of the invoice.

    Raises:
        RecordNotFoundError: If the invoice does not exist.
    """
    invoice = await get_invoice(db, invoice_id)
    await db.delete(invoice)
    await db.flush()
