import os
import re

import pytest


def read_dockerfile():
    assert os.path.exists("Dockerfile"), "Dockerfile not found"
    with open("Dockerfile") as f:
        return f.read()


def test_multi_stage_build():
    content = read_dockerfile()
    assert "FROM" in content
    from_count = len(re.findall(r"^FROM\s", content, re.MULTILINE))
    assert from_count >= 2, f"Multi-stage build requires 2+ FROM, found {from_count}"
    assert "AS" in content or "as" in content, "Builder stage must be named with AS"


def test_uses_slim_base():
    content = read_dockerfile()
    assert "python:3.12-slim" in content, "Must use python:3.12-slim"


def test_non_root_user():
    content = read_dockerfile()
    assert re.search(r"USER\s+\w+", content), "Must create and use non-root user"
    assert re.search(r"(adduser|useradd|groupadd|addgroup)", content, re.IGNORECASE), "Must create user"


def test_working_directory():
    content = read_dockerfile()
    assert re.search(r"WORKDIR\s+/app", content), "Must set WORKDIR /app"


def test_exposes_port():
    content = read_dockerfile()
    assert re.search(r"EXPOSE\s+5000", content), "Must EXPOSE 5000"


def test_healthcheck():
    content = read_dockerfile()
    assert "HEALTHCHECK" in content, "Must have HEALTHCHECK"


def test_env_vars():
    content = read_dockerfile()
    assert "PYTHONUNBUFFERED=1" in content, "Must set PYTHONUNBUFFERED=1"
    assert "PYTHONDONTWRITEBYTECODE=1" in content, "Must set PYTHONDONTWRITEBYTECODE=1"


def test_requirements_before_source():
    content = read_dockerfile()
    req_pos = content.find("requirements.txt")
    app_pos = content.find("app.py")
    if app_pos == -1:
        app_pos = content.find(".")
    assert req_pos != -1, "Must copy requirements.txt"
    assert req_pos < app_pos or "COPY . ." in content, "Requirements should be copied before source"


def test_dockerignore_exists():
    assert os.path.exists(".dockerignore"), ".dockerignore not found"


def test_dockerignore_excludes_tests():
    with open(".dockerignore") as f:
        content = f.read()
    assert "test" in content.lower(), ".dockerignore should exclude tests"
    assert ".git" in content, ".dockerignore should exclude .git"
    assert "__pycache__" in content, ".dockerignore should exclude __pycache__"


def test_cmd_or_entrypoint():
    content = read_dockerfile()
    assert "CMD" in content or "ENTRYPOINT" in content, "Must have CMD or ENTRYPOINT"
