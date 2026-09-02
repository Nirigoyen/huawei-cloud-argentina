#!/usr/bin/env python3
"""Evaluation script for async_bug task."""
import json
import os
import subprocess
import sys


def main():
    result = {"passed": False, "metrics": {}, "details": []}

    if not os.path.exists("fetchData.js"):
        result["details"].append("fetchData.js not found")
        print(json.dumps(result, indent=2))
        sys.exit(1)

    # Check for Promise.allSettled or proper error handling
    with open("fetchData.js") as f:
        content = f.read()
    has_error_handling = "catch" in content or "allSettled" in content or ".catch" in content
    result["metrics"]["has_error_handling"] = has_error_handling
    if not has_error_handling:
        result["details"].append("FAIL: No error handling found")

    try:
        proc = subprocess.run(
            ["npx", "jest", "--verbose", "--forceExit"],
            capture_output=True, text=True, timeout=120,
        )
        result["details"].append(proc.stdout)
        if proc.stderr:
            result["details"].append(proc.stderr)
        result["metrics"]["exit_code"] = proc.returncode
        result["passed"] = proc.returncode == 0 and has_error_handling
    except subprocess.TimeoutExpired:
        result["details"].append("Tests timed out")
    except FileNotFoundError:
        result["details"].append("jest/npx not found")

    print(json.dumps(result, indent=2))
    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
