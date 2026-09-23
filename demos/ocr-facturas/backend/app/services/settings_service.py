"""Settings service - CRUD for application settings and connection testing.

Manages API credentials stored in the app_settings database table
and provides connection test functionality for each external service.
"""

import logging
import time

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.settings import AppSettings
from app.schemas.settings import (
    CREDENTIAL_MASK,
    ConnectionTestResult,
    SettingsRead,
    SettingsUpdate,
    SettingsUpdateResponse,
)

logger = logging.getLogger(__name__)

# Mapping of settings keys to their descriptions and secret status
# Also serves as the canonical list of env-var keys that should be
# loaded from the database at application startup.
SETTINGS_KEYS = {
    "HUAWEI_IAM_USERNAME": ("Huawei Cloud IAM username", True),
    "HUAWEI_IAM_PASSWORD": ("Huawei Cloud IAM password", True),
    "HUAWEI_PROJECT_ID": ("Huawei Cloud project ID (Hong Kong region)", True),
    "HUAWEI_REGION": ("Huawei Cloud region", False),
    "DIFY_API_KEY": ("Dify workflow API key", True),
    "DIFY_BASE_URL": ("Dify API base URL", False),
    "DIFY_WORKFLOW_ID": ("Dify workflow ID", False),
    "DIFY_WEB_URL": ("Dify Web UI URL for embedded workflow viewer", False),
    "DIFY_LLM_API_KEY": ("Dify LLM API key (for workflow LLM node)", True),
    "DIFY_LLM_BASE_URL": ("Dify LLM base URL (OpenAI-compatible)", False),
    "DIFY_LLM_MODEL_NAME": ("Dify LLM model name", False),
    "DIFY_LLM_PROMPT": ("Dify LLM prompt for the workflow LLM node", False),
    "MAAS_API_KEY": ("Huawei MaaS API key", True),
    "MAAS_BASE_URL": ("Huawei MaaS API base URL", False),
    "MAAS_MODEL_NAME": ("MaaS model name for chatbot", False),
    "DESTINATION_DB_TYPE": ("Destination database type (postgresql/mysql)", False),
    "DESTINATION_DB_HOST": ("Destination database host", False),
    "DESTINATION_DB_PORT": ("Destination database port", False),
    "DESTINATION_DB_NAME": ("Destination database name", False),
    "DESTINATION_DB_USERNAME": ("Destination database username", True),
    "DESTINATION_DB_PASSWORD": ("Destination database password", True),
    "DESTINATION_DB_TABLE": ("Destination database table name", False),
    "DATA_FORWARD_ENABLED": ("Enable data forwarding to destination DB", False),
    "DATA_FORWARD_URL": ("Data forward URL (Dify posts extracted data here)", False),
}


async def get_settings_from_db(db: AsyncSession) -> SettingsRead:
    """Read current settings from the database.

    All secret values are returned masked.

    Args:
        db: Async database session.

    Returns:
        SettingsRead with masked credential values.
    """
    result = await db.execute(select(AppSettings))
    settings_rows = result.scalars().all()

    settings_map = {row.key: row.value for row in settings_rows}

    def _mask(key: str) -> str | None:
        value = settings_map.get(key)
        if value is None:
            return None
        is_secret = SETTINGS_KEYS.get(key, (None, True))[1]
        return CREDENTIAL_MASK if is_secret else value

    return SettingsRead(
        huawei_iam_username=_mask("HUAWEI_IAM_USERNAME"),
        huawei_iam_password=_mask("HUAWEI_IAM_PASSWORD"),
        huawei_project_id=_mask("HUAWEI_PROJECT_ID"),
        huawei_region=_mask("HUAWEI_REGION"),
        dify_api_key=_mask("DIFY_API_KEY"),
        dify_base_url=_mask("DIFY_BASE_URL"),
        dify_workflow_id=_mask("DIFY_WORKFLOW_ID"),
        dify_web_url=_mask("DIFY_WEB_URL"),
        dify_llm_api_key=_mask("DIFY_LLM_API_KEY"),
        dify_llm_base_url=_mask("DIFY_LLM_BASE_URL"),
        dify_llm_model_name=_mask("DIFY_LLM_MODEL_NAME"),
        dify_llm_prompt=_mask("DIFY_LLM_PROMPT"),
        maas_api_key=_mask("MAAS_API_KEY"),
        maas_base_url=_mask("MAAS_BASE_URL"),
        maas_model_name=_mask("MAAS_MODEL_NAME"),
        destination_db_type=_mask("DESTINATION_DB_TYPE"),
        destination_db_host=_mask("DESTINATION_DB_HOST"),
        destination_db_port=_mask("DESTINATION_DB_PORT"),
        destination_db_name=_mask("DESTINATION_DB_NAME"),
        destination_db_username=_mask("DESTINATION_DB_USERNAME"),
        destination_db_password=_mask("DESTINATION_DB_PASSWORD"),
        destination_db_table=_mask("DESTINATION_DB_TABLE"),
        data_forward_enabled=_mask("DATA_FORWARD_ENABLED"),
        data_forward_url=_mask("DATA_FORWARD_URL"),
    )


async def update_settings_in_db(
    db: AsyncSession,
    update: SettingsUpdate,
) -> SettingsUpdateResponse:
    """Update settings in the database.

    Only non-null fields in the update request are modified.
    Also updates the runtime environment variables.

    Args:
        db: Async database session.
        update: Settings update with new values.

    Returns:
        SettingsUpdateResponse listing updated fields.
    """
    import os

    updated_fields: list[str] = []

    # Map from SettingsUpdate fields to DB keys
    field_to_key = {
        "huawei_iam_username": "HUAWEI_IAM_USERNAME",
        "huawei_iam_password": "HUAWEI_IAM_PASSWORD",
        "huawei_project_id": "HUAWEI_PROJECT_ID",
        "huawei_region": "HUAWEI_REGION",
        "dify_api_key": "DIFY_API_KEY",
        "dify_base_url": "DIFY_BASE_URL",
        "dify_workflow_id": "DIFY_WORKFLOW_ID",
        "dify_web_url": "DIFY_WEB_URL",
        "dify_llm_api_key": "DIFY_LLM_API_KEY",
        "dify_llm_base_url": "DIFY_LLM_BASE_URL",
        "dify_llm_model_name": "DIFY_LLM_MODEL_NAME",
        "dify_llm_prompt": "DIFY_LLM_PROMPT",
        "maas_api_key": "MAAS_API_KEY",
        "maas_base_url": "MAAS_BASE_URL",
        "maas_model_name": "MAAS_MODEL_NAME",
        "destination_db_type": "DESTINATION_DB_TYPE",
        "destination_db_host": "DESTINATION_DB_HOST",
        "destination_db_port": "DESTINATION_DB_PORT",
        "destination_db_name": "DESTINATION_DB_NAME",
        "destination_db_username": "DESTINATION_DB_USERNAME",
        "destination_db_password": "DESTINATION_DB_PASSWORD",
        "destination_db_table": "DESTINATION_DB_TABLE",
        "data_forward_enabled": "DATA_FORWARD_ENABLED",
        "data_forward_url": "DATA_FORWARD_URL",
    }

    for field_name, db_key in field_to_key.items():
        new_value = getattr(update, field_name, None)
        if new_value is not None:
            # Reject masked values — they are display placeholders, not real credentials
            if new_value == CREDENTIAL_MASK:
                logger.warning(
                    "Rejecting update for %s: value is credential mask (not a real value)",
                    db_key,
                )
                continue
            # Convert bool to str — DB value column is VARCHAR, os.environ also requires str
            if isinstance(new_value, bool):
                str_value = str(new_value)
            else:
                str_value = str(new_value)

            # Update or create the setting in DB
            result = await db.execute(select(AppSettings).where(AppSettings.key == db_key))
            setting = result.scalar_one_or_none()

            if setting:
                setting.value = str_value
            else:
                description, is_secret = SETTINGS_KEYS.get(db_key, (db_key, True))
                setting = AppSettings(
                    key=db_key,
                    value=str_value,
                    description=description,
                    is_secret=is_secret,
                )
                db.add(setting)

            # Also update runtime environment variable
            os.environ[db_key] = str_value
            updated_fields.append(field_name)

    await db.flush()

    # Clear cached settings so they reload
    from app.core.config import clear_settings

    clear_settings()

    return SettingsUpdateResponse(
        message="Settings updated successfully",
        updated_fields=updated_fields,
    )


async def test_huawei_connection() -> ConnectionTestResult:
    """Test Huawei Cloud IAM connection.

    Sends an authentication request to the IAM endpoint.
    """
    settings = get_settings()
    start = time.time()

    if not settings.huawei_iam_username or not settings.huawei_iam_password:
        return ConnectionTestResult(
            service="huawei_iam",
            success=False,
            message="Huawei IAM credentials not configured",
        )

    try:
        auth_body = {
            "auth": {
                "identity": {
                    "methods": ["password"],
                    "password": {
                        "user": {
                            "name": settings.huawei_iam_username,
                            "password": settings.huawei_iam_password,
                            "domain": {"name": settings.huawei_iam_username},
                        }
                    },
                },
                "scope": {
                    "project": {
                        "id": settings.huawei_project_id,
                    }
                },
            }
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                settings.huawei_iam_endpoint,
                json=auth_body,
            )

        latency = int((time.time() - start) * 1000)

        if response.status_code == 201 and "x-subject-token" in response.headers:
            return ConnectionTestResult(
                service="huawei_iam",
                success=True,
                message="Huawei IAM authentication successful",
                latency_ms=latency,
            )
        else:
            return ConnectionTestResult(
                service="huawei_iam",
                success=False,
                message=f"IAM auth failed: HTTP {response.status_code}",
                latency_ms=latency,
            )

    except Exception as e:
        return ConnectionTestResult(
            service="huawei_iam",
            success=False,
            message=f"Connection error: {str(e)}",
        )


async def test_dify_connection() -> ConnectionTestResult:
    """Test Dify API connection.

    Makes a simple request to verify the API key and connectivity.
    """
    settings = get_settings()
    start = time.time()

    if not settings.dify_api_key:
        return ConnectionTestResult(
            service="dify",
            success=False,
            message="Dify API key not configured",
        )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{settings.dify_base_url}/v1/workflows/run",
                headers={"Authorization": f"Bearer {settings.dify_api_key}"},
            )

        latency = int((time.time() - start) * 1000)

        # Any response (even 404/405) means the service is reachable
        if response.status_code in (200, 404, 405):
            return ConnectionTestResult(
                service="dify",
                success=True,
                message="Dify API is reachable",
                latency_ms=latency,
            )
        elif response.status_code in (401, 403):
            return ConnectionTestResult(
                service="dify",
                success=False,
                message="Dify API key is invalid",
                latency_ms=latency,
            )
        else:
            return ConnectionTestResult(
                service="dify",
                success=False,
                message=f"Dify returned HTTP {response.status_code}",
                latency_ms=latency,
            )

    except Exception as e:
        return ConnectionTestResult(
            service="dify",
            success=False,
            message=f"Connection error: {str(e)}",
        )


async def test_maas_connection() -> ConnectionTestResult:
    """Test MaaS API connection.

    Sends a minimal chat completion request.
    """
    settings = get_settings()
    start = time.time()

    if not settings.maas_api_key:
        return ConnectionTestResult(
            service="maas",
            success=False,
            message="MaaS API key not configured",
        )

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{settings.maas_base_url}/chat/completions",
                headers={"Authorization": f"Bearer {settings.maas_api_key}"},
                json={
                    "model": settings.maas_model_name,
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 5,
                },
            )

        latency = int((time.time() - start) * 1000)

        if response.status_code == 200:
            return ConnectionTestResult(
                service="maas",
                success=True,
                message="MaaS API is reachable and authenticated",
                latency_ms=latency,
            )
        elif response.status_code in (401, 403):
            return ConnectionTestResult(
                service="maas",
                success=False,
                message="MaaS API key is invalid",
                latency_ms=latency,
            )
        else:
            return ConnectionTestResult(
                service="maas",
                success=False,
                message=f"MaaS returned HTTP {response.status_code}",
                latency_ms=latency,
            )

    except Exception as e:
        return ConnectionTestResult(
            service="maas",
            success=False,
            message=f"Connection error: {str(e)}",
        )


async def load_settings_from_db(db: AsyncSession) -> None:
    """Load all settings from the database into environment variables.

    This is called at application startup to ensure that credentials
    persisted in the database are available as environment variables,
    even after an app restart (where env vars would otherwise be lost).

    After loading, the cached Settings instance is cleared so that
    the next call to get_settings() picks up the new env-var values.

    Args:
        db: Async database session.
    """
    import os

    from app.core.config import clear_settings

    result = await db.execute(select(AppSettings))
    settings_rows = result.scalars().all()

    loaded_count = 0
    for row in settings_rows:
        # Only load keys that we recognize as application settings
        if row.key in SETTINGS_KEYS and row.value is not None:
            os.environ[row.key] = row.value
            loaded_count += 1

    # Clear cached settings so they reload from the updated env vars
    clear_settings()

    logger.info(
        "Loaded %d setting(s) from database into environment variables",
        loaded_count,
    )
