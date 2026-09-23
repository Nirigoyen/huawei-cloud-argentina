"""Application configuration using pydantic-settings.

Loads all configuration from environment variables with sensible defaults.
Supports .env file loading for local development.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All settings can be overridden via environment variables or a .env file.
    Nested values use double underscore (e.g., DATABASE_URL).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    app_name: str = "OCR Facturas"
    app_version: str = "0.1.0"
    debug: bool = False

    # --- Database ---
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ocr_facturas"
    chatbot_database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ocr_facturas"

    # --- Dify ---
    dify_base_url: str = "http://dify-api:5001"
    dify_api_key: str = ""
    dify_workflow_id: str = ""
    dify_console_api_url: str = "http://dify-api:5001"
    dify_web_url: str = "http://101.44.13.134:3001"

    # --- Dify LLM Model (for workflow's LLM node, separate from MaaS chatbot) ---
    dify_llm_api_key: str = ""
    dify_llm_base_url: str = ""
    dify_llm_model_name: str = ""
    dify_llm_prompt: str = ""

    # --- Huawei Cloud ---
    huawei_iam_username: str = ""
    huawei_iam_password: str = ""
    huawei_project_id: str = ""
    huawei_region: str = "ap-southeast-1"
    huawei_iam_endpoint: str = "https://iam.ap-southeast-1.myhuaweicloud.com/v3/auth/tokens"
    huawei_ocr_endpoint: str = (
        "https://ocr.ap-southeast-1.myhuaweicloud.com/v2/{project_id}/ocr/smart-document-recognizer"
    )

    # --- MaaS (Model-as-a-Service) ---
    maas_api_key: str = ""
    maas_base_url: str = "https://maas.ap-southeast-1.myhuaweicloud.com/v1"
    maas_model_name: str = "deepseek-v3"

    # --- File Upload ---
    upload_dir: str = "./uploads"
    max_file_size_mb: int = 15
    max_file_size_bytes: int = 15 * 1024 * 1024  # 15 MB = 15,728,640 bytes
    allowed_extensions: list[str] = [".pdf", ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"]
    allowed_mime_types: list[str] = [
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
        "image/svg+xml",
    ]

    # --- OCR Processing ---
    ocr_timeout_seconds: int = 120
    ocr_max_retries: int = 3
    ocr_retry_backoff_seconds: float = 1.0

    # --- Chatbot ---
    chatbot_query_timeout_seconds: int = 5
    chatbot_max_question_length: int = 1000

    # --- Destination Database (Data Forward) ---
    destination_db_type: str = ""  # "postgresql" or "mysql"
    destination_db_host: str = ""
    destination_db_port: str = ""
    destination_db_name: str = ""
    destination_db_username: str = ""
    destination_db_password: str = ""
    destination_db_table: str = "invoices"  # default table name
    data_forward_enabled: bool = False
    data_forward_url: str = ""  # URL that Dify will POST to (auto-generated or custom)

    # --- CORS ---
    cors_origins: str = "http://localhost:3000"

    # --- Logging ---
    log_level: str = "INFO"
    log_format: str = "json"

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse CORS_ORIGINS string into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_dify_configured(self) -> bool:
        """Check if Dify credentials are configured."""
        return bool(self.dify_api_key and self.dify_base_url)

    @property
    def is_huawei_configured(self) -> bool:
        """Check if Huawei Cloud credentials are configured."""
        return bool(self.huawei_iam_username and self.huawei_iam_password and self.huawei_project_id)

    @property
    def is_maas_configured(self) -> bool:
        """Check if MaaS credentials are configured."""
        return bool(self.maas_api_key and self.maas_base_url)

    @property
    def is_destination_db_configured(self) -> bool:
        """Check if destination database is configured."""
        return bool(
            self.destination_db_type
            and self.destination_db_host
            and self.destination_db_name
            and self.destination_db_username
        )


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings instance.

    Uses lru_cache to ensure settings are loaded only once.
    Call clear_settings() to force reload.
    """
    return Settings()


def clear_settings() -> None:
    """Clear the cached settings instance, forcing reload on next get_settings() call."""
    get_settings.cache_clear()
