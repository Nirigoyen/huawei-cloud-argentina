#!/usr/bin/env python3
"""Evaluation script for sql_top_customers task."""
import json
import os
import subprocess
import sys


def main():
    result = {"passed": False, "metrics": {}, "details": []}

    if not os.path.exists("query.sql"):
        result["details"].append("query.sql not found")
        print(json.dumps(result, indent=2))
        sys.exit(1)

    # Validate SQL syntax by running through sqlite3
    with open("query.sql") as f:
        query = f.read()
    result["metrics"]["query_length"] = len(query)

    # Check for required SQL elements
    checks = [
        ("Has SELECT", "SELECT" in query.upper()),
        ("Has JOIN or subquery", "JOIN" in query.upper() or "IN (" in query.upper()),
        ("Has GROUP BY", "GROUP BY" in query.upper()),
        ("Has ORDER BY", "ORDER BY" in query.upper()),
        ("Has LIMIT", "LIMIT" in query.upper()),
        ("Has completed status filter", "completed" in query.lower()),
    ]
    passed = sum(1 for _, ok in checks if ok)
    result["metrics"]["sql_checks_passed"] = passed
    result["metrics"]["sql_checks_total"] = len(checks)
    for name, ok in checks:
        if not ok:
            result["details"].append(f"FAIL: {name}")

    # Run tests
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
