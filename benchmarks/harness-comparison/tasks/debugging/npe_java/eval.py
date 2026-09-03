#!/usr/bin/env python3
"""Evaluation script for npe_java task."""
import json
import os
import re
import subprocess
import sys


def check_optional_usage():
    checks = []
    if not os.path.exists("UserService.java"):
        return [("UserService.java exists", False)]

    with open("UserService.java") as f:
        content = f.read()

    checks.append(("UserService.java exists", True))
    checks.append(("Uses Optional", "Optional" in content))
    checks.append(("Uses Optional.map or flatMap", "map(" in content or "flatMap(" in content))
    checks.append(("Uses orElse or orElseGet", "orElse" in content))
    checks.append(("findUser returns Optional", "Optional<User> findUser" in content))
    checks.append(("getUserEmail returns Optional", "Optional<String> getUserEmail" in content))
    checks.append(("getUserCity returns Optional", "Optional<String> getUserCity" in content))

    # Check no raw .get() without isPresent() or direct null returns from findUser
    checks.append(("No direct null return from findUser",
                   not re.search(r"return\s+null\s*;", content) or "Optional.empty()" in content))

    return checks


def main():
    result = {"passed": False, "metrics": {}, "details": []}

    checks = check_optional_usage()
    passed = sum(1 for _, ok in checks if ok)
    result["metrics"]["checks_passed"] = passed
    result["metrics"]["checks_total"] = len(checks)
    for name, ok in checks:
        if not ok:
            result["details"].append(f"FAIL: {name}")

    # Try to compile and run tests
    if os.path.exists("UserService.java"):
        try:
            proc = subprocess.run(
                ["javac", "UserService.java"],
                capture_output=True, text=True, timeout=30,
            )
            result["metrics"]["compiles"] = proc.returncode == 0
            if proc.returncode != 0:
                result["details"].append(f"Compilation error: {proc.stderr}")
        except FileNotFoundError:
            result["details"].append("javac not found (skipping compilation)")
        except subprocess.TimeoutExpired:
            result["details"].append("Compilation timed out")

    result["passed"] = passed == len(checks)

    print(json.dumps(result, indent=2))
    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
