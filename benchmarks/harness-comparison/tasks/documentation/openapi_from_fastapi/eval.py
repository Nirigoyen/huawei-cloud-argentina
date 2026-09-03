#!/usr/bin/env python3
"""Evaluation script for openapi_from_fastapi task."""
import json
import os
import subprocess
import sys


def validate_spec():
    checks = []
    if not os.path.exists("openapi.json"):
        return [("openapi.json exists", False)]

    try:
        with open("openapi.json") as f:
            spec = json.load(f)
        checks.append(("openapi.json exists", True))
        checks.append(("Valid JSON", True))
    except json.JSONDecodeError as e:
        checks.append(("openapi.json exists", True))
        checks.append(("Valid JSON", False))
        checks.append((f"JSON error: {e}", False))
        return checks

    # Version
    version = spec.get("openapi", "")
    checks.append(("OpenAPI 3.0.x", version.startswith("3.0")))

    # Info
    info = spec.get("info", {})
    checks.append(("Has info.title", "title" in info))
    checks.append(("Has info.version", "version" in info))

    # Paths
    paths = spec.get("paths", {})
    checks.append(("Has /books", "/books" in paths))
    checks.append(("Has /books/{book_id}", "/books/{book_id}" in paths))

    # Methods
    if "/books" in paths:
        checks.append(("GET /books", "get" in paths["/books"]))
        checks.append(("POST /books", "post" in paths["/books"]))
    if "/books/{book_id}" in paths:
        p = paths["/books/{book_id}"]
        checks.append(("GET /books/{book_id}", "get" in p))
        checks.append(("PUT /books/{book_id}", "put" in p))
        checks.append(("DELETE /books/{book_id}", "delete" in p))

    # Schemas
    schemas = spec.get("components", {}).get("schemas", {})
    checks.append(("Has Book schema", "Book" in schemas))
    checks.append(("Has BookCreate schema", "BookCreate" in schemas))

    return checks


def main():
    result = {"passed": False, "metrics": {}, "details": []}

    checks = validate_spec()
    passed = sum(1 for _, ok in checks if ok)
    result["metrics"]["checks_passed"] = passed
    result["metrics"]["checks_total"] = len(checks)
    for name, ok in checks:
        if not ok:
            result["details"].append(f"FAIL: {name}")

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
