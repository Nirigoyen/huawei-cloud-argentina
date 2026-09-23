"""FastAPI application entry point.

Creates the FastAPI app with:
- CORS middleware for frontend communication
- All API routers mounted at /api/v1/
- Startup/shutdown lifespan handlers
- Structured logging configuration
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select

from app.core.auth import security
from app.core.config import clear_settings, get_settings
from app.core.database import close_db, init_db
from app.core.exceptions import AppException

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def _load_settings_from_db() -> None:
    """Load credentials from the app_settings database table into environment variables.

    This ensures that credentials set via the Settings UI persist across app restarts.
    For each row in app_settings, the value is set as an environment variable,
    overriding any value from the .env file. After loading, the cached Settings
    singleton is cleared so the next get_settings() call picks up the new values.
    """
    from app.models.settings import AppSettings

    try:
        # Use the async session factory directly (get_db is a generator dependency,
        # so we use the session factory from the database module instead).
        from app.core.database import _get_session_factory

        session_factory = _get_session_factory()
        async with session_factory() as session:
            result = await session.execute(select(AppSettings))
            settings_rows = result.scalars().all()

            loaded_keys: list[str] = []
            for row in settings_rows:
                if row.value is not None:
                    os.environ[row.key] = row.value
                    loaded_keys.append(row.key)

            if loaded_keys:
                logger.info(
                    "Loaded %d settings from database into environment: %s",
                    len(loaded_keys),
                    ", ".join(loaded_keys),
                )
            else:
                logger.info("No settings found in app_settings table")

        # Clear cached Settings so the next get_settings() call reloads from env
        clear_settings()
        logger.info("Settings cache cleared — will reload on next access")

    except Exception as e:
        logger.warning(
            "Failed to load settings from database (non-fatal): %s",
            str(e),
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    settings = get_settings()
    logger.info("Starting %s v%s", settings.app_name, settings.app_version)

    # Initialize database connection
    try:
        await init_db()
        logger.info("Database connection established")
    except Exception as e:
        logger.error("Failed to initialize database: %s", str(e))

    # Load persisted settings from the app_settings table into env vars.
    # This must happen after init_db() so the session factory is ready.
    await _load_settings_from_db()

    # Ensure upload directory exists
    import pathlib

    upload_dir = pathlib.Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Upload directory: %s", upload_dir.resolve())

    yield  # Application is running

    # Shutdown
    logger.info("Shutting down %s", settings.app_name)
    await close_db()
    logger.info("Database connections closed")


# Create FastAPI application
app = FastAPI(
    title="OCR Facturas",
    description="Argentine Invoice OCR Processing and Query API",
    version="0.1.0",
    lifespan=lifespan,
    redirect_slashes=False,  # Prevent 307 redirects that break proxied API calls
)


# =============================================================================
# CORS Middleware
# =============================================================================

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# =============================================================================
# Custom Exception Handlers
# =============================================================================


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle all custom application exceptions with consistent error format."""
    import uuid

    correlation_id = str(uuid.uuid4())

    logger.error(
        "AppException: %s (code=%s, correlation_id=%s)",
        exc.message,
        exc.error_code,
        correlation_id,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "error_code": exc.error_code,
            "correlation_id": correlation_id,
        },
    )


# =============================================================================
# API Routers
# =============================================================================

from app.routers import auth, chatbot, dashboard, data_forward, health, invoices, settings

app.include_router(
    invoices.router,
    prefix="/api/v1",
)
app.include_router(
    chatbot.router,
    prefix="/api/v1",
)
app.include_router(
    settings.router,
    prefix="/api/v1",
)
app.include_router(
    dashboard.router,
    prefix="/api/v1",
)
app.include_router(
    health.router,
    prefix="/api/v1",
)
app.include_router(
    auth.router,
    prefix="/api/v1",
)
app.include_router(
    data_forward.router,
    prefix="/api/v1",
)


# =============================================================================
# Auth Middleware
# =============================================================================

from app.core.auth import ADMIN_USERNAME, ALGORITHM, SECRET_KEY
from app.core.auth import jwt as jwt_module


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """Check JWT authentication for protected API endpoints.

    Skips auth for:
    - CORS preflight requests (OPTIONS method)
    - Health check endpoint (/api/v1/health and /api/v1/health/)
    - Auth endpoints (/api/v1/auth/*)
    - Data forward endpoints (/api/v1/data-forward/*) — called by Dify without JWT
    - Non-API routes (e.g. docs, openapi.json, root)
    """
    path = request.url.path

    # Skip auth for CORS preflight requests (browsers send OPTIONS without auth headers)
    if request.method == "OPTIONS":
        return await call_next(request)

    # Skip auth for health check, auth endpoints, data-forward endpoints, and non-API routes
    if (
        path in ("/api/v1/health", "/api/v1/health/")
        or path.startswith("/api/v1/auth/")
        or path.startswith("/api/v1/data-forward/")
        or not path.startswith("/api/v1/")
    ):
        return await call_next(request)

    # Check for valid JWT token
    try:
        credentials = await security(request)
        payload = jwt_module.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None or username != ADMIN_USERNAME:
            return JSONResponse(status_code=401, content={"detail": "Invalid authentication credentials"})
    except Exception:
        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})

    return await call_next(request)


# =============================================================================
# Root endpoint
# =============================================================================


@app.get("/")
async def root() -> dict:
    """Root endpoint returning API information."""
    return {
        "name": "OCR Facturas API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
