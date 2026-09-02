#!/usr/bin/env python3
"""Evaluation script for merge_intervals task."""
import json
import subprocess
import sys


def main():
    result = {"passed": False, "metrics": {}, "details": []}

    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short", "-q"],
            capture_output=True, text=True, timeout=120,
        )
        result["details"].append(proc.stdout)
        if proc.stderr:
            result["details"].append(proc.stderr)
        result["metrics"]["exit_code"] = proc.returncode

        # Parse test count from pytest output
        for line in proc.stdout.splitlines():
            if "passed" in line and "failed" in line:
                result["metrics"]["summary"] = line.strip()
            elif "passed" in line:
                result["metrics"]["summary"] = line.strip()

        result["passed"] = proc.returncode == 0
    except subprocess.TimeoutExpired:
        result["details"].append("Tests timed out after 120s")
    except FileNotFoundError:
        result["details"].append("pytest not found")

    print(json.dumps(result, indent=2))
    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
