"""Application settings loaded from environment / .env."""

from __future__ import annotations

import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # OpenAI-compatible endpoint (provided by the workshop organizers)
    openai_base_url: str = "http://localhost:8000/v1"
    openai_api_key: str = "changeme"
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    openai_streaming: bool = True

    # Metadata DB (app state)
    database_url: str = (
        "postgresql+asyncpg://workshop:workshop@localhost:5432/app_metadata"
    )

    # Wren home (profiles + projects). Per-app to avoid clobbering ~/.wren
    wren_home: Path = Path("./.wren")
    wren_projects_dir: Path = Path("./wren_projects")

    # CORS
    cors_origins: str = "http://localhost:3000"

    # Session
    session_secret: str = "changeme-to-a-long-random-string"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()

# Make WREN_HOME visible to the wren CLI / toolkit (they read this env var).
os.environ.setdefault("WREN_HOME", str(settings.wren_home.resolve()))
# Ensure the dirs exist.
settings.wren_home.mkdir(parents=True, exist_ok=True)
settings.wren_projects_dir.mkdir(parents=True, exist_ok=True)
