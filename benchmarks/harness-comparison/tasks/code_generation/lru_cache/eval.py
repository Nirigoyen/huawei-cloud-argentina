#!/usr/bin/env python3
"""Evaluation script for lru_cache task."""
import json
import os
import subprocess
import sys


def main():
    result = {"passed": False, "metrics": {}, "details": []}

    if not os.path.exists("Cargo.toml"):
        result["details"].append("Cargo.toml not found")
        print(json.dumps(result, indent=2))
        sys.exit(1)

    try:
        proc = subprocess.run(
            ["cargo", "test", "--", "--nocapture"],
            capture_output=True, text=True, timeout=300,
        )
        result["details"].append(proc.stdout)
        if proc.stderr:
            result["details"].append(proc.stderr)
        result["metrics"]["exit_code"] = proc.returncode
        result["passed"] = proc.returncode == 0
    except subprocess.TimeoutExpired:
        result["details"].append("Tests timed out after 300s")
    except FileNotFoundError:
        result["details"].append("cargo not found")

    print(json.dumps(result, indent=2))
    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
