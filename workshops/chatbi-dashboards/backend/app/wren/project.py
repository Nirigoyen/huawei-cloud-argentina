"""Manage Wren projects, connection profiles, and toolkit singletons."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from threading import Lock

import yaml

from app.config import settings


def wren_bin() -> str:
    """Path to the `wren` CLI inside the active venv."""
    return str(Path(sys.executable).parent / "wren")


def profiles_file() -> Path:
    p = (
        Path(os.environ.get("WREN_HOME", str(settings.wren_home.resolve())))
        / "profiles.yml"
    )
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def project_path_for(workshop_id: str) -> Path:
    return settings.wren_projects_dir.resolve() / str(workshop_id)


# --------------------------------------------------------------------------- #
# Profiles
# --------------------------------------------------------------------------- #


def add_profile(
    name: str,
    *,
    host: str,
    port: int,
    database: str,
    user: str,
    password: str,
) -> None:
    """Add or replace a Wren connection profile in WREN_HOME/profiles.yml."""
    p = profiles_file()
    data: dict = {"active": name, "profiles": {}}
    if p.exists():
        loaded = yaml.safe_load(p.read_text()) or {}
        data["profiles"] = loaded.get("profiles", {}) or {}
        data["active"] = name
    data["profiles"][name] = {
        "datasource": "postgres",
        "host": host,
        "port": port,
        "database": database,
        "user": user,
        "password": password,
    }
    p.write_text(yaml.safe_dump(data, sort_keys=False))


def remove_profile(name: str) -> None:
    p = profiles_file()
    if not p.exists():
        return
    data = yaml.safe_load(p.read_text()) or {}
    data.get("profiles", {}).pop(name, None)
    if data.get("active") == name:
        remaining = list(data.get("profiles", {}))
        data["active"] = remaining[0] if remaining else None
    p.write_text(yaml.safe_dump(data, sort_keys=False))


# --------------------------------------------------------------------------- #
# Build
# --------------------------------------------------------------------------- #


def build_project(project_path: Path) -> str:
    """Run `wren context build` to compile YAML -> target/mdl.json."""
    r = subprocess.run(
        [wren_bin(), "context", "build"],
        cwd=str(project_path),
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"wren context build failed:\n{r.stderr}\n{r.stdout}")
    invalidate_toolkit(project_path)
    return r.stdout


# --------------------------------------------------------------------------- #
# Toolkit singleton (one per workshop project; reused across participants)
# --------------------------------------------------------------------------- #

_toolkit_cache: dict[str, object] = {}
_lock = Lock()


def get_toolkit(project_path: Path, profile: str):
    """Return a cached WrenToolkit for the project (built once, reused)."""
    key = str(Path(project_path).resolve())
    with _lock:
        if key not in _toolkit_cache:
            from wren_langchain import WrenToolkit

            _toolkit_cache[key] = WrenToolkit.from_project(key, profile=profile)
        return _toolkit_cache[key]


def invalidate_toolkit(project_path: Path) -> None:
    key = str(Path(project_path).resolve())
    with _lock:
        _toolkit_cache.pop(key, None)
