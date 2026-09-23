"""Invoice API router - upload, list, detail, delete, retry endpoints."""

import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import FileSizeExceededError, FileValidationError, RecordNotFoundError
from app.core.security import validate_upload_file
from app.schemas.invoice import (
    InvoiceDetail,
    InvoiceListResponse,
    InvoiceRetryResponse,
    InvoiceUploadResponse,
)
from app.services.invoice_service import (
    delete_invoice,
    get_invoice,
    list_invoices,
    update_invoice_status,
)
from app.services.ocr_service import process_invoice

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.post("/upload", response_model=InvoiceUploadResponse, status_code=201)
async def upload_invoice(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Invoice file (PDF, JPG, PNG, GIF, WEBP, SVG)"),
    db: AsyncSession = Depends(get_db),
) -> InvoiceUploadResponse:
    """Upload an invoice file for OCR processing.

    Validates the file type, size, and filename, then:
    1. Saves the file to disk
    2. Creates an invoice record with status "processing"
    3. Triggers OCR processing in the background

    Returns the invoice ID and initial status.
    """
    try:
        # Validate file
        sanitized_filename, mime_type, file_size = await validate_upload_file(file)
    except (FileValidationError, FileSizeExceededError) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

    # Read file content
    file_bytes = await file.read()

    # Save file to disk
    import pathlib

    settings = __import__("app.core.config", fromlist=["get_settings"]).get_settings()
    upload_dir = pathlib.Path(settings.upload_dir)
    invoice_id = uuid.uuid4()
    invoice_dir = upload_dir / str(invoice_id)
    invoice_dir.mkdir(parents=True, exist_ok=True)
    file_path = invoice_dir / sanitized_filename
    file_path.write_bytes(file_bytes)
    relative_path = f"{invoice_id}/{sanitized_filename}"

    # Create invoice record
    from app.models.invoice import Invoice

    invoice = Invoice(
        id=invoice_id,
        status="processing",
        original_filename=sanitized_filename,
        file_size_bytes=file_size,
        file_path=relative_path,
    )
    db.add(invoice)
    await db.commit()
    await db.refresh(invoice)

    # Trigger OCR processing in background
    async def _process():
        from app.core.database import _get_session_factory

        session_factory = _get_session_factory()
        async with session_factory() as bg_db:
            try:
                await process_invoice(
                    bg_db,
                    invoice_id,
                    file_bytes,
                    sanitized_filename,
                    mime_type,
                    file_path=relative_path,
                    file_size=file_size,
                )
                await bg_db.commit()
            except Exception as e:
                logger.error("Background OCR processing failed for %s: %s", invoice_id, str(e))
                # Rollback any partial changes from process_invoice, then
                # explicitly set status to "failed" and commit so the UI
                # reflects the failure instead of staying stuck on "processing".
                await bg_db.rollback()
                try:
                    await update_invoice_status(bg_db, invoice_id, "failed")
                    await bg_db.commit()
                except Exception as status_err:
                    logger.error("Failed to update invoice status to 'failed': %s", str(status_err))

    background_tasks.add_task(_process)

    return InvoiceUploadResponse(
        invoice_id=invoice.id,
        status="processing",
        message="Invoice uploaded and OCR processing started",
    )


@router.get("/", response_model=InvoiceListResponse)
async def list_invoices_endpoint(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    status: str | None = Query(default=None, description="Filter by status"),
    invoice_type: str | None = Query(default=None, description="Filter by invoice type"),
    sort_by: str = Query(default="created_at", description="Sort field"),
    sort_order: str = Query(default="desc", description="Sort order (asc/desc)"),
    db: AsyncSession = Depends(get_db),
) -> InvoiceListResponse:
    """List invoices with pagination, filtering, and sorting."""
    return await list_invoices(
        db,
        page=page,
        page_size=page_size,
        status=status,
        invoice_type=invoice_type,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/{invoice_id}", response_model=InvoiceDetail)
async def get_invoice_detail(
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> InvoiceDetail:
    """Get full invoice detail including issuer, client, line items, and totals."""
    try:
        invoice = await get_invoice(db, invoice_id)
        return InvoiceDetail.model_validate(invoice)
    except RecordNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{invoice_id}", status_code=204)
async def delete_invoice_endpoint(
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete an invoice and all its associated data."""
    try:
        await delete_invoice(db, invoice_id)
    except RecordNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{invoice_id}/retry", response_model=InvoiceRetryResponse)
async def retry_invoice(
    invoice_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> InvoiceRetryResponse:
    """Retry OCR processing for a failed invoice."""
    try:
        invoice = await get_invoice(db, invoice_id)
    except RecordNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if invoice.status != "failed":
        raise HTTPException(
            status_code=409,
            detail="Invoice is not in failed status. Only failed invoices can be retried.",
        )

    # Reset status to processing
    await update_invoice_status(db, invoice_id, "processing")

    # Read original file
    import pathlib

    settings = __import__("app.core.config", fromlist=["get_settings"]).get_settings()
    file_path = pathlib.Path(settings.upload_dir) / invoice.file_path
    file_bytes = file_path.read_bytes()

    # Trigger re-processing in background
    async def _retry():
        from app.core.database import _get_session_factory

        session_factory = _get_session_factory()
        async with session_factory() as bg_db:
            try:
                await process_invoice(
                    bg_db,
                    invoice_id,
                    file_bytes,
                    invoice.original_filename,
                    "application/octet-stream",
                    file_path=invoice.file_path,
                    file_size=invoice.file_size_bytes,
                )
                await bg_db.commit()
            except Exception as e:
                logger.error("Retry OCR processing failed for %s: %s", invoice_id, str(e))
                # Rollback partial changes, then set status to "failed" and commit
                await bg_db.rollback()
                try:
                    await update_invoice_status(bg_db, invoice_id, "failed")
                    await bg_db.commit()
                except Exception as status_err:
                    logger.error("Failed to update invoice status to 'failed': %s", str(status_err))

    background_tasks.add_task(_retry)

    return InvoiceRetryResponse(invoice_id=invoice_id)
