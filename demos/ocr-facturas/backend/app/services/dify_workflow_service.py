"""Service to apply settings to the Dify workflow via Console API.

Manages Dify workflow configuration through environment variables
instead of Start node input variables. Credentials and configuration
values (iam_username, iam_password, project_id, data_forward_url,
db_schema) are stored as Dify environment variables, referenced as
{{#env.var_name#}} in the workflow graph.

Also configures the OpenAI-compatible model provider, installs the
plugin if needed, and updates the LLM node model reference.
"""

import asyncio
import json
import logging
import os
import uuid
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Dify workflow app ID
APP_ID = "d34dbaef-5521-4040-888e-d6c8a7526f9f"
START_NODE_ID = "1783697484527"

# Node IDs in the workflow graph
LLM_NODE_ID = "1784210722315"
OCR_HTTP_NODE_ID = "1784168167268"

# Full provider name in Dify 1.0.0 plugin system
PROVIDER_NAME = "langgenius/openai_api_compatible/openai_api_compatible"

# Dify Console login credentials (from environment variables)
DIFY_CONSOLE_EMAIL = os.environ.get("DIFY_CONSOLE_EMAIL", "admin@example.com")
DIFY_CONSOLE_PASSWORD = os.environ.get("DIFY_CONSOLE_PASSWORD", "change-me-in-production")

# Path to the .difypkg plugin file inside the container.
# Can be overridden via the DIFY_PLUGIN_PKG_PATH environment variable.
DIFYPKG_PATH = os.environ.get(
    "DIFY_PLUGIN_PKG_PATH",
    "/opt/ocrfacturas/openai_api_compatible.difypkg",
)

# Credential/config variable names that should be environment variables
# (not Start node input variables). These are removed from the Start node
# and stored in graph.environment_variables instead.
CREDENTIAL_ENV_VARS = [
    "iam_username",
    "iam_password",
    "project_id",
    "data_forward_url",
    "db_schema",
]

# Default values for environment variables (used by convert_to_env_variables)
ENV_VAR_DEFAULTS: dict[str, str] = {
    "iam_username": os.environ.get("HWCLOUD_IAM_USERNAME", ""),
    "iam_password": os.environ.get("HWCLOUD_IAM_PASSWORD", ""),
    "project_id": "166fd493f76543709f58a6049690bcf3",
    "data_forward_url": "http://ocr-facturas-backend:8000/api/v1/data-forward/invoice",
    "db_schema": "",
}

# Mapping: environment variable name -> settings attribute name
# Used by apply_settings_to_workflow() to set env var values from app settings.
ENV_VAR_TO_SETTING = {
    "iam_username": "huawei_iam_username",
    "iam_password": "huawei_iam_password",
    "project_id": "huawei_project_id",
    "data_forward_url": "data_forward_url",
    # db_schema is set dynamically from get_destination_db_schema()
}


async def _login_to_dify_console(
    client: httpx.AsyncClient,
    console_url: str,
) -> dict[str, str]:
    """Login to the Dify Console API and return auth headers.

    Args:
        client: httpx async client.
        console_url: Dify Console API base URL.

    Returns:
        Dict with Authorization header.

    Raises:
        Exception: If login fails.
    """
    login_resp = await client.post(
        f"{console_url}/console/api/login",
        json={"email": DIFY_CONSOLE_EMAIL, "password": DIFY_CONSOLE_PASSWORD},
    )
    login_resp.raise_for_status()
    login_data = login_resp.json()
    token = login_data.get("access_token") or login_data.get("data", {}).get("access_token")

    if not token:
        raise RuntimeError("Failed to get Dify Console token")

    return {"Authorization": f"Bearer {token}"}


def _replace_variable_references(graph: dict[str, Any]) -> dict[str, Any]:
    """Replace Start node variable references with environment variable references.

    Converts all {{#1783697484527.iam_username#}} style references to
    {{#env.iam_username#}} style references throughout the entire graph,
    including node data, URLs, headers, and prompt templates.

    This is done by serializing the graph to JSON, performing string
    replacement, and deserializing back.

    Args:
        graph: The workflow graph dict.

    Returns:
        The graph with all credential variable references replaced.
    """
    graph_json = json.dumps(graph, ensure_ascii=False)

    for var_name in CREDENTIAL_ENV_VARS:
        old_ref = f"{{{{#{START_NODE_ID}.{var_name}#}}}}"
        new_ref = f"{{{{#env.{var_name}#}}}}"
        graph_json = graph_json.replace(old_ref, new_ref)

    return json.loads(graph_json)


def _set_environment_variables(
    graph: dict[str, Any],
    env_var_values: dict[str, str],
) -> list[str]:
    """Set environment variable values in the workflow graph.

    Updates existing environment variables or creates new ones in
    graph.environment_variables for each name/value pair provided.

    Args:
        graph: The workflow graph dict.
        env_var_values: Dict mapping env var name to its value.

    Returns:
        List of descriptive strings for logging (e.g., "iam_username=hwst...").
    """
    # Ensure environment_variables list exists
    if "environment_variables" not in graph:
        graph["environment_variables"] = []

    env_vars = graph["environment_variables"]
    updated = []

    # Build index of existing env vars by name
    existing_by_name = {ev.get("name"): ev for ev in env_vars if "name" in ev}

    for var_name, var_value in env_var_values.items():
        if var_name in existing_by_name:
            # Update existing env var
            existing_by_name[var_name]["value"] = var_value
        else:
            # Create new env var entry
            new_env_var = {
                "id": str(uuid.uuid4()),
                "name": var_name,
                "value": var_value,
                "value_type": "string",
            }
            env_vars.append(new_env_var)
            existing_by_name[var_name] = new_env_var

        # Log-friendly truncated value
        display_val = f"{var_value[:20]}{'...' if len(var_value) > 20 else ''}"
        updated.append(f"{var_name}={display_val}")

    return updated


def _remove_credential_start_variables(graph: dict[str, Any]) -> list[str]:
    """Remove credential variables from the Start node, keeping only 'archivo'.

    Args:
        graph: The workflow graph dict.

    Returns:
        List of removed variable names.
    """
    removed = []
    for node in graph.get("nodes", []):
        if node.get("data", {}).get("type") == "start":
            original_vars = node["data"].get("variables", [])
            # Keep only non-credential variables (i.e., 'archivo')
            filtered_vars = [v for v in original_vars if v.get("variable", "") not in CREDENTIAL_ENV_VARS]
            removed = [v.get("variable", "") for v in original_vars if v.get("variable", "") in CREDENTIAL_ENV_VARS]
            node["data"]["variables"] = filtered_vars
            break

    return removed


async def _ensure_plugin_installed(
    client: httpx.AsyncClient,
    console_url: str,
    headers: dict[str, str],
) -> bool:
    """Ensure the openai_api_compatible plugin is installed in Dify.

    1. Check if the plugin is already installed by listing model providers.
    2. If not, upload the .difypkg file and install it.
    3. Wait for the install task to complete.

    Returns:
        True if the plugin is available (already installed or newly installed),
        False if installation failed.
    """
    # Step 1: Check if the plugin is already installed
    try:
        providers_resp = await client.get(
            f"{console_url}/console/api/workspaces/current/model-providers",
            headers=headers,
        )
        if providers_resp.status_code == 200:
            providers = providers_resp.json()
            # providers may be a list or dict depending on Dify version
            if isinstance(providers, list):
                for p in providers:
                    if (
                        p.get("plugin_unique_identifier", "").startswith("langgenius/openai_api_compatible")
                        or p.get("provider") == PROVIDER_NAME
                    ):
                        logger.info("Plugin already installed, skipping upload")
                        return True
            elif isinstance(providers, dict):
                data = providers.get("data", providers)
                if isinstance(data, list):
                    for p in data:
                        if (
                            p.get("plugin_unique_identifier", "").startswith("langgenius/openai_api_compatible")
                            or p.get("provider") == PROVIDER_NAME
                        ):
                            logger.info("Plugin already installed, skipping upload")
                            return True
    except Exception as e:
        logger.warning("Could not check installed plugins: %s", e)

    # Step 2: Upload the .difypkg file
    if not os.path.isfile(DIFYPKG_PATH):
        logger.warning(
            "Plugin package not found at %s — skipping plugin install. "
            "Ensure the plugin is already installed in Dify or mount the file.",
            DIFYPKG_PATH,
        )
        return False

    try:
        with open(DIFYPKG_PATH, "rb") as pkg_file:
            upload_resp = await client.post(
                f"{console_url}/console/api/workspaces/current/plugin/upload/pkg",
                headers=headers,
                files={"pkg": ("openai_api_compatible.difypkg", pkg_file, "application/octet-stream")},
            )
    except Exception as e:
        logger.error("Failed to upload plugin package: %s", e)
        return False

    if upload_resp.status_code not in (200, 201):
        logger.warning(
            "Plugin upload failed (HTTP %d): %s",
            upload_resp.status_code,
            upload_resp.text[:200],
        )
        return False

    upload_data = upload_resp.json()
    plugin_unique_identifier = upload_data.get("plugin_unique_identifier") or upload_data.get("data", {}).get(
        "plugin_unique_identifier"
    )
    if not plugin_unique_identifier:
        logger.warning("Plugin upload succeeded but no unique identifier returned: %s", upload_data)
        return False

    logger.info("Plugin uploaded, unique identifier: %s", plugin_unique_identifier)

    # Step 3: Install the uploaded plugin
    install_resp = await client.post(
        f"{console_url}/console/api/workspaces/current/plugin/install/marketplace",
        headers=headers,
        json={"plugin_unique_identifiers": [plugin_unique_identifier]},
    )
    if install_resp.status_code not in (200, 201):
        logger.warning(
            "Plugin install request failed (HTTP %d): %s",
            install_resp.status_code,
            install_resp.text[:200],
        )
        return False

    install_data = install_resp.json()
    # The install response may contain a task_id to track progress
    task_id = install_data.get("task_id") or install_data.get("data", {}).get("task_id")

    if task_id:
        # Step 4: Poll the install task status until it completes
        max_wait_seconds = 60
        poll_interval = 2
        elapsed = 0
        while elapsed < max_wait_seconds:
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

            task_resp = await client.get(
                f"{console_url}/console/api/workspaces/current/plugin/tasks/{task_id}",
                headers=headers,
            )
            if task_resp.status_code != 200:
                logger.warning("Plugin task status check failed (HTTP %d)", task_resp.status_code)
                continue

            task_data = task_resp.json()
            status = task_data.get("status") or task_data.get("data", {}).get("status", "")
            if status in ("completed", "success", "done"):
                logger.info("Plugin installed successfully")
                return True
            if status in ("failed", "error"):
                logger.error("Plugin install task failed: %s", task_data)
                return False
            # Still in progress (e.g. "pending", "running")
            logger.debug("Plugin install in progress: %s", status)

        logger.warning("Plugin install timed out after %d seconds", max_wait_seconds)
        return False

    # No task_id returned — assume install succeeded immediately
    logger.info("Plugin install request accepted (no task_id to track)")
    return True


async def convert_to_env_variables() -> dict[str, Any]:
    """Convert Start node credential variables to Dify environment variables.

    This is a one-time migration function that:
    1. Logs into the Dify Console API
    2. Gets the current draft workflow
    3. Creates environment variables in graph.environment_variables
       for: iam_username, iam_password, project_id, data_forward_url, db_schema
    4. Replaces all {{#1783697484527.iam_username#}} references with
       {{#env.iam_username#}} etc. throughout the entire graph
    5. Removes credential input variables from the Start node
       (keeps only 'archivo')
    6. Saves the draft and publishes

    Returns:
        Dict with 'success' bool and 'message' str.
    """
    settings = get_settings()
    console_url = settings.dify_console_api_url or "http://dify-api:5001"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Step 1: Login to Dify Console
            headers = await _login_to_dify_console(client, console_url)

            # Step 2: Get current workflow draft
            draft_resp = await client.get(
                f"{console_url}/console/api/apps/{APP_ID}/workflows/draft",
                headers=headers,
            )
            draft_resp.raise_for_status()
            draft_data = draft_resp.json()

            graph = draft_data["graph"]
            features = draft_data.get("features", {})
            hash_val = draft_data.get("hash", "")

            # Step 3: Create environment variables in the graph
            updated_env = _set_environment_variables(graph, ENV_VAR_DEFAULTS)
            logger.info("Created/updated environment variables: %s", ", ".join(updated_env))

            # Step 4: Replace all variable references in the graph
            graph = _replace_variable_references(graph)
            logger.info("Replaced Start node variable references with env var references")

            # Step 5: Remove credential variables from Start node
            removed_vars = _remove_credential_start_variables(graph)
            if removed_vars:
                logger.info("Removed Start node variables: %s", ", ".join(removed_vars))
            else:
                logger.warning("No credential variables found in Start node to remove")

            # Step 6: Fix OCR URL to use env.project_id reference
            for node in graph.get("nodes", []):
                if node.get("id") == OCR_HTTP_NODE_ID:
                    node["data"]["url"] = (
                        "https://ocr.ap-southeast-1.myhuaweicloud.com"
                        "/v2/{{#env.project_id#}}/ocr/smart-document-recognizer"
                    )
                    logger.info("Updated OCR HTTP node URL to use env.project_id reference")
                    break

            # Step 7: Save draft
            save_resp = await client.post(
                f"{console_url}/console/api/apps/{APP_ID}/workflows/draft",
                headers=headers,
                json={"graph": graph, "features": features, "hash": hash_val},
            )
            save_resp.raise_for_status()

            # Step 8: Publish
            publish_resp = await client.post(
                f"{console_url}/console/api/apps/{APP_ID}/workflows/publish",
                headers=headers,
            )
            publish_resp.raise_for_status()

            message_parts = []
            if updated_env:
                message_parts.append(f"env vars: {', '.join(updated_env)}")
            if removed_vars:
                message_parts.append(f"removed Start vars: {', '.join(removed_vars)}")

            logger.info("Converted workflow to use environment variables: %s", "; ".join(message_parts))

            return {
                "success": True,
                "message": f"Converted to env variables: {'; '.join(message_parts)}",
            }

    except httpx.HTTPStatusError as e:
        logger.error("Dify API error: %s %s", e.response.status_code, e.response.text[:200])
        return {"success": False, "message": f"Dify API error: HTTP {e.response.status_code}"}
    except Exception as e:
        logger.error("Failed to convert to env variables: %s", str(e))
        return {"success": False, "message": f"Error: {str(e)}"}


async def apply_settings_to_workflow() -> dict[str, Any]:
    """Apply current app settings to the Dify workflow.

    Updates environment variable values in the Dify workflow graph
    with the current settings from the app configuration.

    Also:
    - Ensures the openai_api_compatible plugin is installed.
    - Configures the model provider and adds the LLM model.
    - Updates the LLM node model reference in the workflow graph.
    - Fixes the OCR HTTP node URL to use the project_id env var.

    Returns:
        Dict with 'success' bool and 'message' str.
    """
    settings = get_settings()

    # Get Dify Console URL from settings
    console_url = settings.dify_console_api_url or "http://dify-api:5001"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Step 1: Login to Dify Console
            headers = await _login_to_dify_console(client, console_url)

            # Step 2: Get current workflow draft
            draft_resp = await client.get(
                f"{console_url}/console/api/apps/{APP_ID}/workflows/draft",
                headers=headers,
            )
            draft_resp.raise_for_status()
            draft_data = draft_resp.json()

            graph = draft_data["graph"]
            features = draft_data.get("features", {})
            hash_val = draft_data.get("hash", "")

            # Step 3: Update environment variable values from settings
            env_var_values: dict[str, str] = {}
            for var_name, setting_attr in ENV_VAR_TO_SETTING.items():
                env_var_values[var_name] = getattr(settings, setting_attr, "") or ""

            # Also set db_schema from the data forward service
            try:
                from app.services.data_forward_service import get_destination_db_schema

                schema_result = get_destination_db_schema()
                if schema_result.get("success") and schema_result.get("schema"):
                    env_var_values["db_schema"] = json.dumps(schema_result["schema"], ensure_ascii=False)
                else:
                    env_var_values["db_schema"] = ""
            except Exception:
                env_var_values["db_schema"] = ""

            updated_vars = _set_environment_variables(graph, env_var_values)

            if not updated_vars:
                return {"success": False, "message": "No environment variables found to update"}

            # Step 4: Configure LLM model (if settings provided)
            if settings.dify_llm_api_key and settings.dify_llm_base_url and settings.dify_llm_model_name:
                # Step 4a: Ensure the plugin is installed
                plugin_ok = await _ensure_plugin_installed(client, console_url, headers)
                if not plugin_ok:
                    logger.warning(
                        "Plugin installation did not succeed — model configuration may fail. "
                        "Continuing anyway in case the plugin was installed manually."
                    )

                # Step 4b: Strip /v1 from endpoint_url (plugin appends /v1 automatically)
                endpoint_url = settings.dify_llm_base_url.rstrip("/")
                if endpoint_url.endswith("/v1"):
                    endpoint_url = endpoint_url[:-3]
                    logger.info(
                        "Stripped /v1 from endpoint_url (plugin appends /v1 automatically): %s",
                        endpoint_url,
                    )

                # Step 4c: Configure the model provider credentials
                provider_payload = {
                    "credentials": {
                        "api_key": settings.dify_llm_api_key,
                        "endpoint_url": endpoint_url,
                    }
                }
                provider_resp = await client.post(
                    f"{console_url}/console/api/workspaces/current/model-providers/{PROVIDER_NAME}",
                    headers=headers,
                    json=provider_payload,
                )
                if provider_resp.status_code in (200, 201):
                    logger.info("Model provider configured successfully")
                else:
                    logger.warning(
                        "Failed to configure model provider (HTTP %d): %s",
                        provider_resp.status_code,
                        provider_resp.text[:200],
                    )

                # Step 4d: Add the specific model via Console API
                # Validation may fail for MaaS (Huawei Cloud) — log warning and continue.
                model_payload = {
                    "model": settings.dify_llm_model_name,
                    "model_type": "llm",
                    "credentials": {
                        "api_key": settings.dify_llm_api_key,
                        "endpoint_url": endpoint_url,
                        "mode": "chat",
                        "context_size": "64000",
                        "max_tokens": "8192",
                    },
                }
                model_resp = await client.post(
                    f"{console_url}/console/api/workspaces/current/model-providers/{PROVIDER_NAME}/models",
                    headers=headers,
                    json=model_payload,
                )
                if model_resp.status_code in (200, 201):
                    logger.info(
                        "Model '%s' added via Console API",
                        settings.dify_llm_model_name,
                    )
                else:
                    # Check if it's a validation failure (common for MaaS) vs. other errors
                    resp_text = model_resp.text
                    if "Credentials validation failed" in resp_text:
                        logger.warning(
                            "Model add failed with credentials validation error (expected for MaaS). "
                            "The model should still be usable if it was manually inserted "
                            "into provider_models with is_valid=true. Response: %s",
                            resp_text[:200],
                        )
                    else:
                        logger.warning(
                            "Model add via Console API failed (HTTP %d): %s",
                            model_resp.status_code,
                            resp_text[:200],
                        )

                # Step 4e: Update LLM node model in workflow graph
                # IMPORTANT: Only update the model field — preserve everything else
                # (especially prompt_template) to avoid overwriting the LLM prompt,
                # unless a custom prompt is configured.
                for node in graph.get("nodes", []):
                    if node.get("id") == LLM_NODE_ID:
                        # Save reference to existing prompt_template before updating
                        prompt_template = node["data"].get("prompt_template", [])

                        # Update only the model reference
                        node["data"]["model"] = {
                            "provider": PROVIDER_NAME,
                            "model": settings.dify_llm_model_name,
                            "mode": "chat",
                        }

                        # Update prompt if a custom prompt is configured
                        if settings.dify_llm_prompt:
                            node["data"]["prompt_template"] = [{"role": "system", "text": settings.dify_llm_prompt}]
                            logger.info(
                                "LLM prompt updated with custom prompt (%d chars)",
                                len(settings.dify_llm_prompt),
                            )
                        else:
                            # Verify prompt is preserved after update
                            if prompt_template:
                                logger.info(
                                    "LLM prompt preserved (%d entries)",
                                    len(prompt_template),
                                )
                            else:
                                logger.warning(
                                    "LLM prompt_template is empty — this may indicate a problem! "
                                    "The LLM node may not have a configured prompt."
                                )
                        break

            # Step 5: Fix OCR URL to use project_id environment variable
            for node in graph.get("nodes", []):
                if node.get("id") == OCR_HTTP_NODE_ID:
                    # Replace with env.project_id reference
                    # Dify syntax: {{#env.project_id#}} — in Python f-string, {{{{ → {{ and #}} → #}}
                    node["data"]["url"] = (
                        "https://ocr.ap-southeast-1.myhuaweicloud.com"
                        "/v2/{{#env.project_id#}}/ocr/smart-document-recognizer"
                    )
                    break

            # Step 6: Save draft
            save_resp = await client.post(
                f"{console_url}/console/api/apps/{APP_ID}/workflows/draft",
                headers=headers,
                json={"graph": graph, "features": features, "hash": hash_val},
            )
            save_resp.raise_for_status()

            # Step 7: Publish
            publish_resp = await client.post(
                f"{console_url}/console/api/apps/{APP_ID}/workflows/publish",
                headers=headers,
            )
            publish_resp.raise_for_status()

            logger.info("Applied settings to Dify workflow: %s", ", ".join(updated_vars))

            return {
                "success": True,
                "message": f"Workflow updated: {', '.join(updated_vars)}",
            }

    except httpx.HTTPStatusError as e:
        logger.error("Dify API error: %s %s", e.response.status_code, e.response.text[:200])
        return {"success": False, "message": f"Dify API error: HTTP {e.response.status_code}"}
    except Exception as e:
        logger.error("Failed to apply settings to workflow: %s", str(e))
        return {"success": False, "message": f"Error: {str(e)}"}


async def fetch_available_models() -> list[dict[str, str]]:
    """Fetch available LLM models from the Dify Console API.

    Logs into the Dify Console, fetches models from the configured
    openai_api_compatible provider, and supplements with models from
    the MaaS /v1/models endpoint as a fallback/supplement.

    Returns:
        List of dicts with keys: id, name, type, status.
    """
    settings = get_settings()
    console_url = settings.dify_console_api_url or "http://dify-api:5001"

    models: list[dict[str, str]] = []
    seen_ids: set = set()

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Login to Dify Console
            headers = await _login_to_dify_console(client, console_url)

            # Fetch models from the openai_api_compatible provider
            try:
                models_resp = await client.get(
                    f"{console_url}/console/api/workspaces/current/model-providers/{PROVIDER_NAME}/models",
                    headers=headers,
                )
                if models_resp.status_code == 200:
                    provider_models = models_resp.json()
                    # The response may be a list directly or wrapped in a "data" key
                    if isinstance(provider_models, dict):
                        provider_models = provider_models.get("data", provider_models.get("models", []))
                    if isinstance(provider_models, list):
                        for m in provider_models:
                            model_id = m.get("model", m.get("id", ""))
                            if model_id and model_id not in seen_ids:
                                seen_ids.add(model_id)
                                models.append(
                                    {
                                        "id": model_id,
                                        "name": m.get("model_name", m.get("name", model_id)),
                                        "type": m.get("model_type", m.get("type", "llm")),
                                        "status": "active" if m.get("status", "active") != "disabled" else "disabled",
                                    }
                                )
                    logger.info(
                        "Fetched %d models from Dify Console provider",
                        len(models),
                    )
                else:
                    logger.warning(
                        "Failed to fetch models from provider (HTTP %d): %s",
                        models_resp.status_code,
                        models_resp.text[:200],
                    )
            except Exception as e:
                logger.warning("Error fetching models from Dify Console provider: %s", e)

            # Supplement with models from the MaaS /v1/models endpoint
            if settings.dify_llm_api_key and settings.dify_llm_base_url:
                try:
                    maas_resp = await client.get(
                        f"{settings.dify_llm_base_url.rstrip('/')}/models",
                        headers={"Authorization": f"Bearer {settings.dify_llm_api_key}"},
                    )
                    if maas_resp.status_code == 200:
                        maas_data = maas_resp.json()
                        maas_model_list = maas_data.get("data", [])
                        if isinstance(maas_model_list, list):
                            for m in maas_model_list:
                                model_id = m.get("id", "")
                                if model_id and model_id not in seen_ids:
                                    seen_ids.add(model_id)
                                    models.append(
                                        {
                                            "id": model_id,
                                            "name": model_id,
                                            "type": m.get("type", "llm"),
                                            "status": "active",
                                        }
                                    )
                        supplemented = [
                            m
                            for m in models
                            if m["id"] not in {m2["id"] for m2 in models[: len(models) - len(maas_model_list)]}
                        ]
                        logger.info(
                            "Supplemented with %d models from MaaS /v1/models",
                            len(supplemented),
                        )
                    else:
                        logger.warning(
                            "Failed to fetch models from MaaS endpoint (HTTP %d)",
                            maas_resp.status_code,
                        )
                except Exception as e:
                    logger.warning("Error fetching models from MaaS endpoint: %s", e)

    except Exception as e:
        logger.error("Failed to fetch Dify models: %s", str(e))
        raise

    return models


async def fetch_llm_default_prompt() -> str:
    """Fetch the current LLM prompt from the Dify workflow.

    Logs into the Dify Console, fetches the workflow draft, and
    extracts the prompt_template from the LLM node.

    Returns:
        The current prompt text from the LLM node, or empty string
        if not found.
    """
    settings = get_settings()
    console_url = settings.dify_console_api_url or "http://dify-api:5001"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Login to Dify Console
            headers = await _login_to_dify_console(client, console_url)

            # Get workflow draft
            draft_resp = await client.get(
                f"{console_url}/console/api/apps/{APP_ID}/workflows/draft",
                headers=headers,
            )
            draft_resp.raise_for_status()
            draft_data = draft_resp.json()

            graph = draft_data.get("graph", {})

            # Find the LLM node and extract the prompt
            for node in graph.get("nodes", []):
                if node.get("id") == LLM_NODE_ID:
                    prompt_template = node.get("data", {}).get("prompt_template", [])
                    if prompt_template:
                        # Extract text from the system prompt entry
                        for entry in prompt_template:
                            if entry.get("role") == "system":
                                return entry.get("text", "")
                        # If no system role, return the first entry's text
                        if prompt_template and "text" in prompt_template[0]:
                            return prompt_template[0].get("text", "")
                    return ""

            logger.warning("LLM node %s not found in workflow draft", LLM_NODE_ID)
            return ""

    except Exception as e:
        logger.error("Failed to fetch LLM default prompt: %s", str(e))
        raise
