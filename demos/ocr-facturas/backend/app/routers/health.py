"""Health check API router."""

import logging

from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", include_in_schema=False)
async def health_check_no_slash(
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Health check without trailing slash (for Docker healthcheck compatibility)."""
    return await health_check(response, db)


@router.get("/")
async def health_check(
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Health check endpoint for monitoring.

    Tests:
    - Database connectivity (SELECT 1)
    - Dify API availability (if configured)
    - MaaS API availability (if configured)

    Returns 200 if healthy, 503 if any critical service is down.
    """
    settings = get_settings()
    services = {}
    is_healthy = True

    # Check database
    try:
        await db.execute(text("SELECT 1"))
        services["database"] = "ok"
    except Exception as e:
        logger.error("Database health check failed: %s", str(e))
        services["database"] = "error"
        is_healthy = False

    # Check Dify (if configured)
    if settings.is_dify_configured:
        try:
            import httpx

            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    f"{settings.dify_base_url}/v1/workflows/run",
                    headers={"Authorization": f"Bearer {settings.dify_api_key}"},
                )
                if resp.status_code < 500:
                    services["dify"] = "ok"
                else:
                    services["dify"] = "error"
                    is_healthy = False
        except Exception:
            services["dify"] = "error"
            # Dify being down is not critical for health check
    else:
        services["dify"] = "not_configured"

    # Check MaaS (if configured) — lightweight check: just verify the API is reachable
    if settings.is_maas_configured:
        try:
            import httpx

            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    f"{settings.maas_base_url}/models",
                    headers={"Authorization": f"Bearer {settings.maas_api_key}"},
                )
                if resp.status_code < 500:
                    services["maas"] = "ok"
                else:
                    services["maas"] = "error"
        except Exception:
            services["maas"] = "error"
            # MaaS being down is not critical for health check
    else:
        services["maas"] = "not_configured"

    if not is_healthy:
        response.status_code = 503
        return {"status": "unhealthy", "services": services}

    return {"status": "healthy", "services": services}
