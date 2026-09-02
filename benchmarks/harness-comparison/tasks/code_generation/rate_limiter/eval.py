#!/usr/bin/env python3
"""Evaluation script for rate_limiter task."""
import json
import os
import subprocess
import sys


def main():
    result = {"passed": False, "metrics": {}, "details": []}

    if not os.path.exists("rateLimiter.js"):
        result["details"].append("rateLimiter.js not found")
        print(json.dumps(result, indent=2))
        sys.exit(1)

    try:
        proc = subprocess.run(
            ["npx", "jest", "--verbose", "--forceExit"],
            capture_output=True, text=True, timeout=120,
        )
        result["details"].append(proc.stdout)
        if proc.stderr:
            result["details"].append(proc.stderr)
        result["metrics"]["exit_code"] = proc.returncode
        result["passed"] = proc.returncode == 0
    except subprocess.TimeoutExpired:
        result["details"].append("Tests timed out after 120s")
    except FileNotFoundError:
        result["details"].append("jest/npx not found")

    print(json.dumps(result, indent=2))
    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
