#!/usr/bin/env python3
"""Evaluation script for fix_sqli task."""
import json
import os
import re
import subprocess
import sys


def check_no_sqli():
    """Check that the code doesn't use string formatting for SQL."""
    checks = []
    if not os.path.exists("app.py"):
        return [("app.py exists", False)]

    with open("app.py") as f:
        content = f.read()

    checks.append(("app.py exists", True))

    # Check for f-string SQL
    fstring_sql = re.findall(r"f['\"].*SELECT", content)
    checks.append(("No f-string SQL queries", len(fstring_sql) == 0))

    # Check for .format() SQL
    format_sql = re.findall(r"SELECT.*\.format\(\)", content, re.DOTALL)
    checks.append(("No .format() SQL queries", len(format_sql) == 0))

    # Check for % formatting SQL
    pct_sql = re.findall(r"SELECT.*%.*\(", content)
    checks.append(("No %-format SQL queries", len(pct_sql) == 0))

    # Check for parameterized queries
    checks.append(("Uses ? placeholders", "?" in content and "execute" in content))

    return checks


def main():
    result = {"passed": False, "metrics": {}, "details": []}

    checks = check_no_sqli()
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
