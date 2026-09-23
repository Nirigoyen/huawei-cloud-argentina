"""Settings API router - credential management and connection testing."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import SettingsError
from app.schemas.settings import (
    ConnectionTestRequest,
    ConnectionTestResult,
    DifyDefaultPromptResponse,
    DifyModelsResponse,
    SettingsRead,
    SettingsUpdate,
    SettingsUpdateResponse,
)
from app.services.settings_service import (
    get_settings_from_db,
    test_dify_connection,
    test_huawei_connection,
    test_maas_connection,
    update_settings_in_db,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/", response_model=SettingsRead)
async def read_settings(
    db: AsyncSession = Depends(get_db),
) -> SettingsRead:
    """Get current application settings.

    All secret values are returned masked (••••••••).
    Null values indicate unconfigured credentials.
    """
    return await get_settings_from_db(db)


@router.put("/", response_model=SettingsUpdateResponse)
async def update_settings(
    update: SettingsUpdate,
    db: AsyncSession = Depends(get_db),
) -> SettingsUpdateResponse:
    """Update application settings/credentials.

    Only non-null fields in the request body are updated.
    Credentials are stored in the database and also updated
    in the runtime environment variables.
    """
    try:
        return await update_settings_in_db(db, update)
    except SettingsError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/test-connection", response_model=ConnectionTestResult)
async def test_connection(
    request: ConnectionTestRequest,
) -> ConnectionTestResult:
    """Test connectivity and authentication for an external service.

    Supported services: huawei_iam, dify, maas

    Returns success/failure with a descriptive message and latency measurement.
    """
    service = request.service.lower()

    if service == "huawei_iam":
        return await test_huawei_connection()
    elif service == "dify":
        return await test_dify_connection()
    elif service == "maas":
        return await test_maas_connection()
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown service '{request.service}'. Supported: huawei_iam, dify, maas",
        )


@router.post("/apply-workflow")
async def apply_settings_to_workflow():
    """Apply current settings to the Dify workflow.

    Updates environment variable values in the Dify workflow graph
    with the current settings from the app configuration, then saves
    the draft and publishes the workflow.
    """
    from app.services.dify_workflow_service import apply_settings_to_workflow as apply_fn

    result = await apply_fn()
    return result


@router.post("/convert-env-vars")
async def convert_to_env_variables():
    """Convert Start node credential variables to Dify environment variables.

    One-time migration that:
    - Creates environment variables for credentials (iam_username, iam_password,
      project_id, data_forward_url, db_schema)
    - Replaces all Start node variable references with env var references
    - Removes credential variables from the Start node (keeps only 'archivo')
    - Saves the draft and publishes the workflow
    """
    from app.services.dify_workflow_service import convert_to_env_variables as convert_fn

    result = await convert_fn()
    return result


@router.get("/dify-models", response_model=DifyModelsResponse)
async def get_dify_models() -> DifyModelsResponse:
    """Fetch available LLM models from the Dify Console API.

    Logs into the Dify Console, fetches models from the configured
    provider, and supplements with models from the MaaS /v1/models
    endpoint as a fallback.

    Returns:
        DifyModelsResponse with a list of available models.
    """
    from app.services.dify_workflow_service import fetch_available_models

    try:
        models = await fetch_available_models()
        return DifyModelsResponse(models=models)
    except Exception as e:
        logger.error("Failed to fetch Dify models: %s", str(e))
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch models from Dify: {str(e)}",
        )


@router.get("/dify-default-prompt", response_model=DifyDefaultPromptResponse)
async def get_dify_default_prompt() -> DifyDefaultPromptResponse:
    """Fetch the current LLM prompt from the Dify workflow.

    Logs into the Dify Console, fetches the workflow draft, and
    extracts the prompt_template from the LLM node.

    Returns:
        DifyDefaultPromptResponse with the current prompt text.
    """
    from app.services.dify_workflow_service import fetch_llm_default_prompt

    try:
        prompt = await fetch_llm_default_prompt()
        return DifyDefaultPromptResponse(prompt=prompt)
    except Exception as e:
        logger.error("Failed to fetch Dify default prompt: %s", str(e))
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch default prompt from Dify: {str(e)}",
        )
