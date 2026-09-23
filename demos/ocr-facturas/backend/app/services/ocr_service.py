"""OCR processing pipeline service.

Orchestrates the full invoice processing flow:
1. Validate file type/size/filename
2. Save file to disk
3. Upload file to Dify
4. Run Dify workflow
5. Parse LLM response
6. Validate extracted data
7. Store in database
"""

import logging
import uuid
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import OCRProcessingError, OCRServiceUnavailableError
from app.schemas.invoice import (
    ClientCreate,
    InvoiceCreate,
    IssuerCreate,
    LineItemCreate,
    TotalsCreate,
)
from app.schemas.ocr import OCRResult
from app.services.dify_service import dify_service
from app.services.invoice_service import update_invoice_status

logger = logging.getLogger(__name__)


async def process_invoice(
    db: AsyncSession,
    invoice_id: uuid.UUID,
    file_bytes: bytes,
    filename: str,
    mime_type: str,
    *,
    file_path: str,
    file_size: int,
) -> None:
    """Process an uploaded invoice through the full OCR pipeline.

    This is the main orchestration function that:
    1. Uploads the file to Dify
    2. Runs the OCR workflow
    3. Parses the LLM response
    4. Validates and normalizes extracted data
    5. Updates the invoice record with results

    Args:
        db: Async database session.
        invoice_id: UUID of the invoice record (already created).
        file_bytes: Raw file content.
        filename: Sanitized filename.
        mime_type: MIME type of the file.
        file_path: Path where file is stored.
        file_size: File size in bytes.
    """
    settings = get_settings()

    try:
        # Step 1: Upload file to Dify
        logger.info("Uploading file to Dify: %s (%d bytes)", filename, file_size)
        upload_response = await dify_service.upload_file(file_bytes, filename, mime_type)
        upload_file_id = upload_response.id
        logger.info("File uploaded to Dify: upload_file_id=%s", upload_file_id)

        # Step 2: Run Dify workflow
        logger.info("Running Dify workflow for invoice %s", invoice_id)
        workflow_response = await dify_service.run_workflow_with_timeout(upload_file_id, mime_type)
        logger.info("Dify workflow completed for invoice %s", invoice_id)

        # Step 3: Parse LLM response
        ocr_result = dify_service.parse_workflow_response(workflow_response)
        logger.info("Parsed OCR result for invoice %s", invoice_id)

        # Step 4: Validate and convert to InvoiceCreate
        invoice_data = _ocr_result_to_invoice_create(ocr_result, filename, file_size, file_path)

        # Step 5: Update invoice record with extracted data
        await _update_invoice_with_ocr_data(db, invoice_id, invoice_data)

        # Step 6: Mark as completed
        await update_invoice_status(db, invoice_id, "completed")
        logger.info("Invoice %s processing completed successfully", invoice_id)

    except OCRServiceUnavailableError as e:
        logger.error("OCR service unavailable for invoice %s: %s", invoice_id, str(e))
        await update_invoice_status(db, invoice_id, "failed")
        raise

    except Exception as e:
        logger.error("OCR processing failed for invoice %s: %s", invoice_id, str(e))
        await update_invoice_status(db, invoice_id, "failed")
        raise OCRProcessingError(f"OCR processing failed: {str(e)}")


def _ocr_result_to_invoice_create(
    ocr_result: OCRResult,
    filename: str,
    file_size: int,
    file_path: str,
) -> InvoiceCreate:
    """Convert an OCRResult to an InvoiceCreate schema.

    Applies validation and normalization:
    - Invoice code zero-padding (3 digits)
    - Point of sale zero-padding (4 digits)
    - Invoice number zero-padding (8 digits)
    - Complete number composition
    - Date parsing
    - Decimal conversion for amounts

    Args:
        ocr_result: Parsed OCR result from Dify.
        filename: Original filename.
        file_size: File size in bytes.
        file_path: Stored file path.

    Returns:
        InvoiceCreate schema ready for persistence.
    """
    warnings = list(ocr_result.validation_warnings)

    # Normalize invoice code (3 digits)
    invoice_code = _normalize_code(ocr_result.invoice_code, warnings)

    # Normalize point of sale (4 digits)
    point_of_sale = _zero_pad(ocr_result.point_of_sale, 4, warnings, "point_of_sale")

    # Normalize invoice number (8 digits)
    invoice_number = _zero_pad(ocr_result.invoice_number, 8, warnings, "invoice_number")

    # Compose complete number if not provided
    complete_number = ocr_result.complete_number
    if not complete_number and point_of_sale and invoice_number:
        complete_number = f"{point_of_sale}-{invoice_number}"

    # Parse dates
    issue_date = _parse_date(ocr_result.issue_date)
    cae_expiry_date = _parse_date(ocr_result.cae_expiry_date)

    # Build issuer
    issuer = None
    if ocr_result.issuer_cuit or ocr_result.issuer_legal_name:
        issuer = IssuerCreate(
            fantasy_name=ocr_result.issuer_fantasy_name,
            legal_name=ocr_result.issuer_legal_name,
            cuit=_normalize_cuit(ocr_result.issuer_cuit, warnings),
            fiscal_condition=ocr_result.issuer_fiscal_condition,
            address=ocr_result.issuer_address,
            locality=ocr_result.issuer_locality,
            province=ocr_result.issuer_province,
            postal_code=ocr_result.issuer_postal_code,
            phone=ocr_result.issuer_phone,
            activity_start=_parse_date(ocr_result.issuer_activity_start),
        )

    # Build client
    client = None
    if ocr_result.client_legal_name or ocr_result.client_document_number:
        client = ClientCreate(
            legal_name=ocr_result.client_legal_name,
            document_type=ocr_result.client_document_type,
            document_number=ocr_result.client_document_number,
            fiscal_condition=ocr_result.client_fiscal_condition,
            address=ocr_result.client_address,
            locality=ocr_result.client_locality,
            province=ocr_result.client_province,
            postal_code=ocr_result.client_postal_code,
            phone=ocr_result.client_phone,
            sale_condition=ocr_result.client_sale_condition,
        )

    # Build line items
    line_items = []
    for idx, item_data in enumerate(ocr_result.line_items, 1):
        line_items.append(
            LineItemCreate(
                line_order=item_data.get("order", idx),
                product_code=item_data.get("product_code"),
                description=item_data.get("description"),
                quantity=_parse_decimal(item_data.get("quantity")),
                unit=item_data.get("unit"),
                unit_price=_parse_decimal(item_data.get("unit_price")),
                discount=_parse_decimal(item_data.get("discount")),
                subtotal_without_iva=_parse_decimal(item_data.get("subtotal_without_iva")),
                iva_rate=item_data.get("iva_rate"),
                total_with_iva=_parse_decimal(item_data.get("total_with_iva")),
            )
        )

    # Build totals
    totals = None
    if ocr_result.total_ars or ocr_result.net_amount:
        totals = TotalsCreate(
            net_amount=_parse_decimal(ocr_result.net_amount),
            iva_amount=_parse_decimal(ocr_result.iva_amount),
            iva_detail=ocr_result.iva_detail,
            other_taxes=_parse_decimal(ocr_result.other_taxes),
            total_invoice_currency=_parse_decimal(ocr_result.total_invoice_currency),
            total_ars=_parse_decimal(ocr_result.total_ars),
        )

    return InvoiceCreate(
        invoice_type=ocr_result.invoice_type,
        invoice_code=invoice_code,
        point_of_sale=point_of_sale,
        invoice_number=invoice_number,
        complete_number=complete_number,
        issue_date=issue_date,
        currency=ocr_result.currency,
        exchange_rate=ocr_result.exchange_rate,
        cae=ocr_result.cae,
        cae_expiry_date=cae_expiry_date,
        original_filename=filename,
        file_size_bytes=file_size,
        file_path=file_path,
        validation_warnings=warnings,
        issuer=issuer,
        client=client,
        line_items=line_items,
        totals=totals,
    )


async def _update_invoice_with_ocr_data(
    db: AsyncSession,
    invoice_id: uuid.UUID,
    data: InvoiceCreate,
) -> None:
    """Update an existing invoice record with OCR-extracted data.

    Args:
        db: Async database session.
        invoice_id: UUID of the invoice to update.
        data: Invoice creation data with extracted fields.
    """
    from sqlalchemy import select

    from app.models.invoice import Invoice
    from app.models.invoice_client import InvoiceClient
    from app.models.invoice_issuer import InvoiceIssuer
    from app.models.invoice_line_item import InvoiceLineItem
    from app.models.invoice_totals import InvoiceTotals

    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()
    if invoice is None:
        return

    # Update invoice header fields
    invoice.invoice_type = data.invoice_type
    invoice.invoice_code = data.invoice_code
    invoice.point_of_sale = data.point_of_sale
    invoice.invoice_number = data.invoice_number
    invoice.complete_number = data.complete_number
    invoice.issue_date = data.issue_date
    invoice.currency = data.currency
    invoice.exchange_rate = data.exchange_rate
    invoice.cae = data.cae
    invoice.cae_expiry_date = data.cae_expiry_date
    invoice.validation_warnings = data.validation_warnings

    # Create issuer
    if data.issuer:
        db.add(InvoiceIssuer(invoice_id=invoice_id, **data.issuer.model_dump()))

    # Create client
    if data.client:
        db.add(InvoiceClient(invoice_id=invoice_id, **data.client.model_dump()))

    # Create line items
    for item_data in data.line_items:
        db.add(InvoiceLineItem(invoice_id=invoice_id, **item_data.model_dump()))

    # Create totals
    if data.totals:
        db.add(InvoiceTotals(invoice_id=invoice_id, **data.totals.model_dump()))

    await db.flush()


# --- Helper functions ---


def _normalize_code(code: str | None, warnings: list[str]) -> str | None:
    """Normalize invoice code to 3-digit format."""
    if not code:
        return None
    # Strip prefixes like "COD." or "COD"
    clean = code.upper().replace("COD.", "").replace("COD", "").strip()
    if clean.isdigit():
        return clean.zfill(3)
    warnings.append(f"Could not normalize invoice code: '{code}'")
    return code


def _zero_pad(value: str | None, length: int, warnings: list[str], field_name: str) -> str | None:
    """Zero-pad a numeric string to the specified length."""
    if not value:
        return None
    clean = value.strip()
    if clean.isdigit():
        return clean.zfill(length)
    warnings.append(f"Could not zero-pad {field_name}: '{value}'")
    return None


def _normalize_cuit(cuit: str | None, warnings: list[str]) -> str | None:
    """Normalize CUIT to XX-XXXXXXXX-X format."""
    if not cuit:
        return None
    clean = cuit.strip().replace("-", "").replace(".", "").replace(" ", "")
    if len(clean) == 11 and clean.isdigit():
        return f"{clean[:2]}-{clean[2:10]}-{clean[10]}"
    warnings.append(f"CUIT format may be invalid: '{cuit}'")
    return cuit


def _parse_date(date_str: str | None) -> date | None:
    """Parse a date string in various formats."""
    if not date_str:
        return None
    date_str = date_str.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


def _parse_decimal(value: str | None) -> Decimal | None:
    """Parse a string to Decimal, handling Argentine number format."""
    if value is None:
        return None
    if isinstance(value, (int, float, Decimal)):
        return Decimal(str(value))
    clean = str(value).strip()
    if not clean:
        return None
    # Handle Argentine format: 1.000.000,00 → 1000000.00
    clean = clean.replace(".", "").replace(",", ".")
    try:
        return Decimal(clean)
    except InvalidOperation:
        return None
