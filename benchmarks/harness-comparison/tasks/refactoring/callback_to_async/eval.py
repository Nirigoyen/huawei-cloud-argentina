#!/usr/bin/env python3
"""Evaluation script for callback_to_async task."""
import json
import os
import re
import subprocess
import sys


def check_async_refactor():
    checks = []
    if not os.path.exists("callbackHell.js"):
        return [("callbackHell.js exists", False)]

    with open("callbackHell.js") as f:
        content = f.read()

    checks.append(("callbackHell.js exists", True))
    checks.append(("Uses async", "async " in content))
    checks.append(("Uses await", "await " in content))
    checks.append(("Uses Promise.all", "Promise.all" in content))
    checks.append(("Exports fetchUserOrderHistory", "fetchUserOrderHistory" in content))

    # Check no deeply nested callbacks (no 4+ levels of nesting)
    # Look for callback-style function calls that should be gone
    nested_callbacks = re.findall(r"function\s*\([^)]*\)\s*\{[^}]*function\s*\([^)]*\)\s*\{[^}]*function\s*\([^)]*\)", content, re.DOTALL)
    checks.append(("No deeply nested callbacks", len(nested_callbacks) == 0))

    # Check for try/catch
    checks.append(("Has try/catch", "try" in content and "catch" in content))

    return checks


def main():
    result = {"passed": False, "metrics": {}, "details": []}

    checks = check_async_refactor()
    passed = sum(1 for _, ok in checks if ok)
    result["metrics"]["checks_passed"] = passed
    result["metrics"]["checks_total"] = len(checks)
    for name, ok in checks:
        if not ok:
            result["details"].append(f"FAIL: {name}")

    try:
        proc = subprocess.run(
            ["npx", "jest", "--verbose", "--forceExit"],
            capture_output=True, text=True, timeout=120,
        )
        result["details"].append(proc.stdout)
        if proc.stderr:
            result["details"].append(proc.stderr)
        result["metrics"]["exit_code"] = proc.returncode
        result["passed"] = proc.returncode == 0 and passed == len(checks)
    except subprocess.TimeoutExpired:
        result["details"].append("Tests timed out")
    except FileNotFoundError:
        result["details"].append("jest/npx not found")

    print(json.dumps(result, indent=2))
    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
