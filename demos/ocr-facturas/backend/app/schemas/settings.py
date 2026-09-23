"""Pydantic schemas for Settings API requests and responses."""

from pydantic import BaseModel, Field

# Mask for hiding credential values in API responses
CREDENTIAL_MASK = "••••••••"


class SettingsRead(BaseModel):
    """Response for reading current settings (all values masked)."""

    huawei_iam_username: str | None = None
    huawei_iam_password: str | None = None
    huawei_project_id: str | None = None
    huawei_region: str | None = None
    dify_api_key: str | None = None
    dify_base_url: str | None = None
    dify_workflow_id: str | None = None
    dify_web_url: str | None = None
    dify_llm_api_key: str | None = None
    dify_llm_base_url: str | None = None
    dify_llm_model_name: str | None = None
    dify_llm_prompt: str | None = None
    maas_api_key: str | None = None
    maas_base_url: str | None = None
    maas_model_name: str | None = None
    # Destination Database
    destination_db_type: str | None = None
    destination_db_host: str | None = None
    destination_db_port: str | None = None
    destination_db_name: str | None = None
    destination_db_username: str | None = None
    destination_db_password: str | None = None
    destination_db_table: str | None = None
    data_forward_enabled: bool | None = None
    data_forward_url: str | None = None


class SettingsUpdate(BaseModel):
    """Request body for updating settings/credentials.

    Only non-null fields will be updated.
    """

    huawei_iam_username: str | None = None
    huawei_iam_password: str | None = None
    huawei_project_id: str | None = None
    huawei_region: str | None = None
    dify_api_key: str | None = None
    dify_base_url: str | None = None
    dify_workflow_id: str | None = None
    dify_web_url: str | None = None
    dify_llm_api_key: str | None = None
    dify_llm_base_url: str | None = None
    dify_llm_model_name: str | None = None
    dify_llm_prompt: str | None = None
    maas_api_key: str | None = None
    maas_base_url: str | None = None
    maas_model_name: str | None = None
    # Destination Database
    destination_db_type: str | None = None
    destination_db_host: str | None = None
    destination_db_port: str | None = None
    destination_db_name: str | None = None
    destination_db_username: str | None = None
    destination_db_password: str | None = None
    destination_db_table: str | None = None
    data_forward_enabled: bool | None = None
    data_forward_url: str | None = None


class ConnectionTestRequest(BaseModel):
    """Request body for testing a service connection."""

    service: str = Field(
        ...,
        description="Service to test: huawei_iam, dify, or maas",
    )


class ConnectionTestResult(BaseModel):
    """Result of a connection test."""

    service: str
    success: bool
    message: str
    latency_ms: int | None = None


class SettingsUpdateResponse(BaseModel):
    """Response after updating settings."""

    message: str = "Settings updated successfully"
    updated_fields: list[str] = Field(default_factory=list)


class DifyModelInfo(BaseModel):
    """Information about a single Dify LLM model."""

    id: str
    name: str
    type: str = "llm"
    status: str = "active"


class DifyModelsResponse(BaseModel):
    """Response with available Dify LLM models."""

    models: list[DifyModelInfo] = Field(default_factory=list)


class DifyDefaultPromptResponse(BaseModel):
    """Response with the default LLM prompt from the Dify workflow."""

    prompt: str = ""
