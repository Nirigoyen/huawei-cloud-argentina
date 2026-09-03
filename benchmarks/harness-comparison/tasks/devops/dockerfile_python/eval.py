#!/usr/bin/env python3
"""Evaluation script for dockerfile_python task."""
import json
import os
import re
import subprocess
import sys


def check_dockerfile():
    """Check Dockerfile best practices."""
    checks = []
    if not os.path.exists("Dockerfile"):
        return [("Dockerfile exists", False)]

    with open("Dockerfile") as f:
        content = f.read()

    checks.append(("Dockerfile exists", True))

    # Multi-stage
    from_count = len(re.findall(r"^FROM\s", content, re.MULTILINE))
    checks.append(("Multi-stage build (2+ FROM)", from_count >= 2))
    checks.append(("Builder stage named with AS", bool(re.search(r"\bAS\b", content, re.IGNORECASE))))

    # Base image
    checks.append(("Uses python:3.12-slim", "python:3.12-slim" in content))

    # Non-root user
    checks.append(("Has non-root USER", bool(re.search(r"USER\s+\w+", content))))
    checks.append(("Creates user", bool(re.search(r"(adduser|useradd)", content, re.IGNORECASE))))

    # Working directory
    checks.append(("WORKDIR /app", bool(re.search(r"WORKDIR\s+/app", content))))

    # Port
    checks.append(("EXPOSE 5000", bool(re.search(r"EXPOSE\s+5000", content))))

    # Healthcheck
    checks.append(("HEALTHCHECK present", "HEALTHCHECK" in content))

    # Env vars
    checks.append(("PYTHONUNBUFFERED=1", "PYTHONUNBUFFERED=1" in content))
    checks.append(("PYTHONDONTWRITEBYTECODE=1", "PYTHONDONTWRITEBYTECODE=1" in content))

    # CMD/ENTRYPOINT
    checks.append(("Has CMD or ENTRYPOINT", "CMD" in content or "ENTRYPOINT" in content))

    # .dockerignore
    checks.append((".dockerignore exists", os.path.exists(".dockerignore")))
    if os.path.exists(".dockerignore"):
        with open(".dockerignore") as f:
            di = f.read()
        checks.append((".dockerignore excludes tests", "test" in di.lower()))
        checks.append((".dockerignore excludes .git", ".git" in di))
        checks.append((".dockerignore excludes __pycache__", "__pycache__" in di))

    return checks


def run_hadolint():
    """Run hadolint if available."""
    try:
        proc = subprocess.run(
            ["hadolint", "Dockerfile"],
            capture_output=True, text=True, timeout=30,
        )
        return proc.returncode == 0, proc.stdout + proc.stderr
    except FileNotFoundError:
        return None, "hadolint not installed (skipped)"
    except subprocess.TimeoutExpired:
        return False, "hadolint timed out"


def main():
    result = {"passed": False, "metrics": {}, "details": []}

    checks = check_dockerfile()
    passed = sum(1 for _, ok in checks if ok)
    result["metrics"]["checks_passed"] = passed
    result["metrics"]["checks_total"] = len(checks)
    for name, ok in checks:
        if not ok:
            result["details"].append(f"FAIL: {name}")

    # Hadolint
    hado_ok, hado_out = run_hadolint()
    if hado_ok is not None:
        result["metrics"]["hadolint_passed"] = hado_ok
        if not hado_ok:
            result["details"].append(f"hadolint: {hado_out}")
    else:
        result["details"].append(hado_out)

    # Run tests
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short", "-q"],
            capture_output=True, text=True, timeout=120,
        )
        result["details"].append(proc.stdout)
        if proc.stderr:
            result["details"].append(proc.stderr)
        result["metrics"]["test_exit_code"] = proc.returncode
        result["passed"] = proc.returncode == 0 and passed == len(checks)
    except subprocess.TimeoutExpired:
        result["details"].append("Tests timed out")
    except FileNotFoundError:
        result["details"].append("pytest not found")

    print(json.dumps(result, indent=2))
    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
