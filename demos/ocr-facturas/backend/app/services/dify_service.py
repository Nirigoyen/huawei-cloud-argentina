"""Dify API client service.

Handles all communication with the Dify platform:
- File upload to Dify storage
- Workflow execution with file reference
- Response parsing from LLM output
"""

import asyncio
import logging

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import get_settings
from app.core.exceptions import (
    DifyAuthenticationError,
    DifyConnectionError,
    DifyWorkflowError,
    OCRTimeoutError,
)
from app.schemas.ocr import (
    DifyFileUploadResponse,
    DifyWorkflowResponse,
    OCRResult,
)

logger = logging.getLogger(__name__)


class DifyService:
    """Async client for the Dify Workflow API.

    Handles file upload, workflow execution, and response parsing
    with retry logic and error handling.
    """

    def __init__(self):
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the httpx async client."""
        if self._client is None or self._client.is_closed:
            settings = get_settings()
            self._client = httpx.AsyncClient(
                base_url=settings.dify_base_url,
                timeout=httpx.Timeout(
                    connect=10.0,
                    read=settings.ocr_timeout_seconds,
                    write=30.0,
                    pool=10.0,
                ),
            )
        return self._client

    async def close(self) -> None:
        """Close the httpx client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
        reraise=True,
    )
    async def upload_file(
        self,
        file_bytes: bytes,
        filename: str,
        mime_type: str,
    ) -> DifyFileUploadResponse:
        """Upload a file to Dify's file storage.

        Args:
            file_bytes: Raw file content.
            filename: Original filename.
            mime_type: MIME type of the file.

        Returns:
            DifyFileUploadResponse with the upload_file_id.

        Raises:
            DifyConnectionError: If Dify is unreachable.
            DifyAuthenticationError: If API key is invalid.
        """
        settings = get_settings()
        client = await self._get_client()

        try:
            response = await client.post(
                "/v1/files/upload",
                headers={"Authorization": f"Bearer {settings.dify_api_key}"},
                files={"file": (filename, file_bytes, mime_type)},
                data={"user": "ocr-facturas-backend"},
            )
            response.raise_for_status()
            return DifyFileUploadResponse(**response.json())

        except httpx.ConnectError as e:
            logger.error("Dify connection failed: %s", str(e))
            raise DifyConnectionError(f"Cannot connect to Dify at {settings.dify_base_url}")
        except httpx.TimeoutException as e:
            logger.error("Dify file upload timed out: %s", str(e))
            raise DifyConnectionError("Dify file upload timed out")
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (401, 403):
                raise DifyAuthenticationError("Dify API key is invalid")
            raise DifyConnectionError(f"Dify file upload failed: HTTP {e.response.status_code}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError)),
        reraise=True,
    )
    async def run_workflow(
        self,
        upload_file_id: str,
        mime_type: str = "",
    ) -> DifyWorkflowResponse:
        """Execute the OCR workflow with an uploaded file.

        Args:
            upload_file_id: Dify file ID from upload_file().

        Returns:
            DifyWorkflowResponse with workflow execution results.

        Raises:
            DifyConnectionError: If Dify is unreachable.
            DifyAuthenticationError: If API key is invalid.
            DifyWorkflowError: If the workflow execution fails.
            OCRTimeoutError: If the workflow times out.
        """
        settings = get_settings()
        client = await self._get_client()

        # Credentials (iam_username, iam_password, project_id, data_forward_url)
        # and db_schema are now Dify environment variables — no longer passed
        # as workflow inputs. They are set via apply_settings_to_workflow()
        # or convert_to_env_variables() in dify_workflow_service.py.

        request_body = {
            "inputs": {
                "archivo": {
                    # Dify expects "image" or "document", not "file"
                    "type": "image" if mime_type.startswith("image/") else "document",
                    "transfer_method": "local_file",
                    "upload_file_id": upload_file_id,
                },
            },
            "response_mode": "blocking",
            "user": "ocr-facturas-backend",
        }

        try:
            response = await client.post(
                "/v1/workflows/run",
                headers={"Authorization": f"Bearer {settings.dify_api_key}"},
                json=request_body,
            )
            response.raise_for_status()
            data = response.json()

            # Check workflow status
            workflow_data = data.get("data", {})
            workflow_status = workflow_data.get("status", "")

            if workflow_status == "failed":
                error_msg = workflow_data.get("error", "Unknown workflow error")
                raise DifyWorkflowError(f"Dify workflow failed: {error_msg}")

            return DifyWorkflowResponse(**data)

        except httpx.ConnectError as e:
            logger.error("Dify workflow connection failed: %s", str(e))
            raise DifyConnectionError("Cannot connect to Dify workflow API")
        except httpx.TimeoutException:
            logger.error("Dify workflow timed out after %ds", settings.ocr_timeout_seconds)
            raise OCRTimeoutError(f"OCR processing timed out after {settings.ocr_timeout_seconds} seconds")
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (401, 403):
                raise DifyAuthenticationError("Dify API key is invalid")
            if e.response.status_code >= 500:
                # Retry on 5xx errors
                raise
            raise DifyWorkflowError(f"Dify workflow request failed: HTTP {e.response.status_code}")

    async def run_workflow_with_timeout(
        self,
        upload_file_id: str,
        mime_type: str = "",
    ) -> DifyWorkflowResponse:
        """Run workflow with an overall timeout wrapper.

        Args:
            upload_file_id: Dify file ID from upload_file().

        Returns:
            DifyWorkflowResponse with workflow execution results.

        Raises:
            OCRTimeoutError: If the workflow exceeds the timeout.
        """
        settings = get_settings()
        try:
            return await asyncio.wait_for(
                self.run_workflow(upload_file_id, mime_type),
                timeout=settings.ocr_timeout_seconds,
            )
        except TimeoutError:
            raise OCRTimeoutError(f"OCR processing timed out after {settings.ocr_timeout_seconds} seconds")

    def parse_workflow_response(
        self,
        workflow_response: DifyWorkflowResponse,
    ) -> OCRResult:
        """Parse the Dify workflow response into a structured OCRResult.

        Extracts the LLM text output (respuesta_llm) from the workflow
        response and parses it into structured fields.

        Args:
            workflow_response: The raw Dify workflow response.

        Returns:
            OCRResult with parsed invoice data.
        """
        outputs = workflow_response.data.outputs or {}
        llm_text = outputs.get("respuesta_llm", "")

        if not llm_text or not llm_text.strip():
            return OCRResult(
                raw_text=llm_text,
                validation_warnings=["Empty extraction result from LLM"],
            )

        return self._parse_llm_text(llm_text)

    def _parse_llm_text(self, text: str) -> OCRResult:
        """Parse the LLM text output into structured fields.

        The LLM output follows a section-based format with headers like:
        - INFORMACIÓN DEL COMPROBANTE
        - DATOS DEL EMISOR
        - DATOS DEL CLIENTE
        - PRODUCTOS O SERVICIOS
        - TOTALES
        - AUTORIZACIÓN

        Args:
            text: Raw LLM text output.

        Returns:
            OCRResult with parsed fields.
        """
        result = OCRResult(raw_text=text)
        warnings = []

        lines = text.strip().split("\n")
        current_section = ""

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Detect section headers
            upper_line = line.upper()
            if "COMPROBANTE" in upper_line and ("INFORMACIÓN" in upper_line or "DATOS" in upper_line):
                current_section = "comprobante"
                continue
            elif "EMISOR" in upper_line:
                current_section = "emisor"
                continue
            elif "CLIENTE" in upper_line or "RECEPTOR" in upper_line:
                current_section = "cliente"
                continue
            elif "PRODUCTO" in upper_line or "SERVICIO" in upper_line:
                current_section = "items"
                continue
            elif "TOTALES" in upper_line and ":" not in line:
                current_section = "totales"
                continue
            elif "AUTORIZACIÓN" in upper_line:
                current_section = "autorizacion"
                continue

            # Parse line items (pipe-delimited rows in items section)
            if current_section == "items" and "|" in line:
                # Skip header row
                lower_line = line.lower()
                if (
                    "código" in lower_line
                    or "codigo" in lower_line
                    or "descripción" in lower_line
                    or "descripcion" in lower_line
                ):
                    continue

                parts = [p.strip() for p in line.split("|")]
                if len(parts) < 5:
                    continue

                # Skip rows where description is "No encontrado" or empty
                description = parts[1] if len(parts) > 1 else ""
                if description.lower() in ("no encontrado", "n/a", "-", ""):
                    continue

                # Normalize sentinels to None
                sentinels = ("no encontrado", "n/a", "-", "")
                cleaned = [p if p.lower() not in sentinels else None for p in parts]

                item = {
                    "product_code": cleaned[0] if len(cleaned) > 0 else None,
                    "description": description,
                    "quantity": cleaned[2] if len(cleaned) > 2 else None,
                    "unit": cleaned[3] if len(cleaned) > 3 else None,
                    "unit_price": cleaned[4] if len(cleaned) > 4 else None,
                    "discount": None,
                    "subtotal_without_iva": None,
                    "iva_rate": cleaned[5] if len(cleaned) > 5 else None,
                    "total_with_iva": cleaned[6] if len(cleaned) > 6 else None,
                }
                result.line_items.append(item)
                continue

            # Parse key-value pairs (format: "Key: Value")
            if ":" in line and current_section != "items":
                key, _, value = line.partition(":")
                key = key.strip().lower()
                value = value.strip()

                if "no encontrado" in value.lower() or value.lower() in ("n/a", "-", ""):
                    continue

                self._assign_field(result, current_section, key, value)

        result.validation_warnings = warnings
        return result

    def _assign_field(
        self,
        result: OCRResult,
        section: str,
        key: str,
        value: str,
    ) -> None:
        """Assign a parsed key-value pair to the appropriate OCRResult field.

        Args:
            result: The OCRResult to populate.
            section: Current section name.
            key: Parsed key (lowercase).
            value: Parsed value.
        """
        # Comprobante section
        if section == "comprobante":
            if "tipo" in key and "comprobante" in key or "letra" in key:
                result.invoice_type = value.strip()[:1] if value else None
            elif "código" in key or "codigo" in key:
                code = value.strip()
                result.invoice_code = code.zfill(3) if code else None
            elif "punto" in key and "venta" in key:
                pos = value.strip()
                result.point_of_sale = pos.zfill(4) if pos else None
            elif "número" in key or "numero" in key:
                if "completo" in key:
                    result.complete_number = value.strip()
                else:
                    num = value.strip()
                    result.invoice_number = num.zfill(8) if num else None
            elif "fecha" in key and "emisión" in key:
                result.issue_date = value.strip()
            elif "moneda" in key:
                result.currency = value.strip()
            elif "tipo de cambio" in key or "cambio" in key:
                result.exchange_rate = value.strip()

        # Emisor section
        elif section == "emisor":
            if "fantasía" in key or "fantasia" in key:
                result.issuer_fantasy_name = value.strip()
            elif "razón" in key or "razon" in key or "legal" in key:
                result.issuer_legal_name = value.strip()
            elif "nombre" in key:
                result.issuer_fantasy_name = value.strip()
            elif "cuit" in key:
                result.issuer_cuit = value.strip()
            elif "condición" in key or "condicion" in key:
                result.issuer_fiscal_condition = value.strip()
            elif "dirección" in key or "direccion" in key or "domicilio" in key:
                result.issuer_address = value.strip()
            elif "localidad" in key:
                result.issuer_locality = value.strip()
            elif "provincia" in key:
                result.issuer_province = value.strip()
            elif "código" in key and "postal" in key:
                result.issuer_postal_code = value.strip()
            elif "teléfono" in key or "telefono" in key:
                result.issuer_phone = value.strip()
            elif "inicio" in key and "actividad" in key:
                result.issuer_activity_start = value.strip()

        # Cliente section
        elif section == "cliente":
            if "razón" in key or "razon" in key or "legal" in key or "nombre" in key:
                result.client_legal_name = value.strip()
            elif "documento" in key and "tipo" in key:
                result.client_document_type = value.strip()
            elif "documento" in key and "número" in key:
                result.client_document_number = value.strip()
            elif ("condición" in key or "condicion" in key) and "venta" in key:
                result.client_sale_condition = value.strip()
            elif "condición" in key or "condicion" in key:
                result.client_fiscal_condition = value.strip()
            elif "dirección" in key or "direccion" in key or "domicilio" in key:
                result.client_address = value.strip()
            elif "localidad" in key:
                result.client_locality = value.strip()
            elif "provincia" in key:
                result.client_province = value.strip()
            elif "código" in key and "postal" in key:
                result.client_postal_code = value.strip()
            elif "teléfono" in key or "telefono" in key:
                result.client_phone = value.strip()

        # Totals section
        elif section == "totales":
            if "neto" in key or "gravado" in key:
                result.net_amount = value.strip()
            elif "iva" in key and "total" not in key:
                result.iva_amount = value.strip()
            elif "pesos" in key or "equivalente" in key:
                result.total_ars = value.strip()
            elif "total" in key and "moneda" in key or "total" in key and "ars" not in key:
                result.total_invoice_currency = value.strip()
            elif "ars" in key:
                result.total_ars = value.strip()
            elif "otro" in key or "otros" in key:
                result.other_taxes = value.strip()

        # Autorizacion section
        elif section == "autorizacion":
            if "cae" in key and "vencimiento" not in key:
                result.cae = value.strip()
            elif "vencimiento" in key:
                result.cae_expiry_date = value.strip()


# Singleton instance
dify_service = DifyService()
