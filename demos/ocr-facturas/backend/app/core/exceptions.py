"""Custom exception classes for OCR Facturas backend.

All exceptions inherit from a base AppException that integrates
with FastAPI's exception handling for consistent error responses.
"""

from typing import Any


class AppException(Exception):
    """Base exception for all application errors.

    Attributes:
        message: Human-readable error message.
        error_code: Machine-readable error code for frontend handling.
        status_code: HTTP status code to return.
        details: Additional error context.
    """

    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


# =============================================================================
# File Upload Errors (FILE_*)
# =============================================================================


class FileValidationError(AppException):
    """Raised when an uploaded file fails validation.

    Covers: unsupported type, size exceeded, invalid filename, path traversal.
    """

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            error_code="FILE_VALIDATION_ERROR",
            status_code=400,
            details=details,
        )


class FileTypeInvalidError(AppException):
    """Raised when a file has an unsupported type/extension."""

    def __init__(self, message: str = "Unsupported file type", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            error_code="FILE_TYPE_INVALID",
            status_code=400,
            details=details,
        )


class FileSizeExceededError(AppException):
    """Raised when a file exceeds the maximum allowed size."""

    def __init__(self, message: str = "File exceeds maximum size", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            error_code="FILE_SIZE_EXCEEDED",
            status_code=413,
            details=details,
        )


class FileNameInvalidError(AppException):
    """Raised when a filename contains path traversal or invalid characters."""

    def __init__(self, message: str = "Invalid file name", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            error_code="FILE_NAME_INVALID",
            status_code=400,
            details=details,
        )


# =============================================================================
# OCR Processing Errors (OCR_*)
# =============================================================================


class OCRProcessingError(AppException):
    """Raised when OCR processing fails for any reason."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            error_code="OCR_PROCESSING_ERROR",
            status_code=500,
            details=details,
        )


class OCRServiceUnavailableError(AppException):
    """Raised when the OCR service (Dify) is unreachable."""

    def __init__(self, message: str = "OCR service unavailable", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            error_code="OCR_SERVICE_UNAVAILABLE",
            status_code=503,
            details=details,
        )


class OCRTimeoutError(AppException):
    """Raised when OCR processing exceeds the timeout limit."""

    def __init__(self, message: str = "OCR processing timed out", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            error_code="OCR_TIMEOUT",
            status_code=504,
            details=details,
        )


class OCRNoTextError(AppException):
    """Raised when OCR returns empty or no text."""

    def __init__(self, message: str = "OCR returned no text", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            error_code="OCR_NO_TEXT",
            status_code=422,
            details=details,
        )


# =============================================================================
# Dify Errors (DIFY_*)
# =============================================================================


class DifyConnectionError(AppException):
    """Raised when the Dify API is unreachable."""

    def __init__(self, message: str = "Dify service unavailable", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            error_code="DIFY_CONNECTION_ERROR",
            status_code=503,
            details=details,
        )


class DifyAuthenticationError(AppException):
    """Raised when Dify API authentication fails."""

    def __init__(self, message: str = "Dify authentication failed", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            error_code="DIFY_AUTH_ERROR",
            status_code=503,
            details=details,
        )


class DifyWorkflowError(AppException):
    """Raised when a Dify workflow execution fails."""

    def __init__(self, message: str = "Dify workflow execution failed", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            error_code="DIFY_WORKFLOW_ERROR",
            status_code=502,
            details=details,
        )


# =============================================================================
# Chatbot Errors (CHAT_*)
# =============================================================================


class ChatbotError(AppException):
    """Raised when a chatbot operation fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            error_code="CHAT_ERROR",
            status_code=500,
            details=details,
        )


class ChatbotIntentUnknownError(AppException):
    """Raised when the chatbot cannot identify a valid intent."""

    def __init__(self, message: str = "Could not identify query intent", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            error_code="CHAT_INTENT_UNKNOWN",
            status_code=400,
            details=details,
        )


class ChatbotQueryTimeoutError(AppException):
    """Raised when a chatbot query exceeds the timeout limit."""

    def __init__(self, message: str = "Query timed out", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            error_code="CHAT_QUERY_TIMEOUT",
            status_code=408,
            details=details,
        )


# =============================================================================
# Settings/Credentials Errors (CRED_*)
# =============================================================================


class SettingsError(AppException):
    """Raised when a settings operation fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            error_code="SETTINGS_ERROR",
            status_code=500,
            details=details,
        )


class CredentialsNotConfiguredError(AppException):
    """Raised when required credentials are not configured."""

    def __init__(self, message: str = "Credentials not configured", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            error_code="CRED_NOT_CONFIGURED",
            status_code=503,
            details=details,
        )


class CredentialsInvalidError(AppException):
    """Raised when credentials fail validation."""

    def __init__(self, message: str = "Invalid credentials", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            error_code="CRED_INVALID_FORMAT",
            status_code=400,
            details=details,
        )


# =============================================================================
# Database Errors (DB_*)
# =============================================================================


class DatabaseError(AppException):
    """Raised when a database operation fails."""

    def __init__(self, message: str = "Database error", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            error_code="DB_ERROR",
            status_code=503,
            details=details,
        )


class RecordNotFoundError(AppException):
    """Raised when a requested record is not found."""

    def __init__(self, message: str = "Record not found", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            error_code="DB_NOT_FOUND",
            status_code=404,
            details=details,
        )


class DuplicateRecordError(AppException):
    """Raised when a duplicate record is detected."""

    def __init__(self, message: str = "Duplicate record detected", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            error_code="DB_DUPLICATE",
            status_code=409,
            details=details,
        )
