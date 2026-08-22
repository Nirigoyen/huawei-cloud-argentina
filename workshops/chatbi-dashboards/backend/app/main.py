"""FastAPI application entrypoint."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create metadata tables on startup (dev). Safe to call repeatedly.
    await init_db()
    yield


app = FastAPI(title="ChatBI Workshop API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


# Routers are registered here as they are implemented.
def _register_routers() -> None:
    try:
        from app.routers import participants, chat, dashboards, workshops, setup

        for r in (workshops.router, setup.router, participants.router, chat.router, dashboards.router):
            app.include_router(r)
    except ImportError:
        # Routers not implemented yet; app still boots for /health.
        pass


_register_routers()
