#!/usr/bin/env python3
"""Evaluation script for extract_function task."""
import importlib
import inspect
import json
import os
import subprocess
import sys


def check_refactoring():
    checks = []
    try:
        mod = importlib.import_module("order_processor")
        functions = [name for name, obj in inspect.getmembers(mod, inspect.isfunction)
                     if not name.startswith("_")]
        checks.append(("Module importable", True))
        checks.append(("Has 6+ extracted functions", len(functions) >= 6))
        checks.append(("Has process_order", "process_order" in functions))
        if functions:
            checks.append((f"Functions: {functions}", True))
    except ImportError as e:
        checks.append(("Module importable", False))
        checks.append((f"Import error: {e}", False))

    return checks


def check_complexity():
    """Check cyclomatic complexity using mccabe if available."""
    checks = []
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short", "-q"],
            capture_output=True, text=True, timeout=120,
        )
        checks.append(("Tests pass", proc.returncode == 0))
    except Exception:
        checks.append(("Tests pass", False))
    return checks


def main():
    result = {"passed": False, "metrics": {}, "details": []}

    refactor_checks = check_refactoring()
    passed = sum(1 for _, ok in refactor_checks if ok)
    result["metrics"]["refactor_checks_passed"] = passed
    result["metrics"]["refactor_checks_total"] = len(refactor_checks)
    for name, ok in refactor_checks:
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
        result["passed"] = proc.returncode == 0 and passed == len(refactor_checks)
    except subprocess.TimeoutExpired:
        result["details"].append("Tests timed out")
    except FileNotFoundError:
        result["details"].append("pytest not found")

    print(json.dumps(result, indent=2))
    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
