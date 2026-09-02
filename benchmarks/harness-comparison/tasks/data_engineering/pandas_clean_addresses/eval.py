#!/usr/bin/env python3
"""Evaluation script for pandas_clean_addresses task."""
import json
import os
import subprocess
import sys


def main():
    result = {"passed": False, "metrics": {}, "details": []}

    if not os.path.exists("clean_addresses.py"):
        result["details"].append("clean_addresses.py not found")
        print(json.dumps(result, indent=2))
        sys.exit(1)

    # Check for required function
    with open("clean_addresses.py") as f:
        content = f.read()
    checks = [
        ("Has clean_data function", "def clean_data" in content),
        ("Uses pandas", "pandas" in content or "pd" in content),
        ("Handles duplicates", "duplicate" in content.lower() or "drop_duplicates" in content),
        ("Handles email", "email" in content.lower()),
        ("Handles phone", "phone" in content.lower()),
    ]
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
