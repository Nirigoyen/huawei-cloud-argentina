#!/usr/bin/env python3
"""Template evaluation script. Copy this and adapt for your task."""
import json
import subprocess
import sys
from pathlib import Path


def run_tests() -> dict:
    """Run the test suite and return structured results."""
    result = {
        "passed": False,
        "metrics": {},
        "details": [],
    }

    # Example: run pytest
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        result["details"].append(proc.stdout)
        if proc.returncode == 0:
            result["passed"] = True
            result["metrics"]["test_exit_code"] = 0
        else:
            result["details"].append(proc.stderr)
            result["metrics"]["test_exit_code"] = proc.returncode
    except subprocess.TimeoutExpired:
        result["details"].append("Tests timed out after 120s")
    except FileNotFoundError:
        result["details"].append("pytest not found")

    return result


def main():
    result = run_tests()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
