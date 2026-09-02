#!/usr/bin/env python3
"""Evaluation script for python_docstrings task."""
import ast
import json
import os
import subprocess
import sys


def check_docstrings():
    checks = []
    if not os.path.exists("calculator.py"):
        return [("calculator.py exists", False)]

    with open("calculator.py") as f:
        source = f.read()

    checks.append(("calculator.py exists", True))

    tree = ast.parse(source)
    items = [n for n in ast.walk(tree)
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]

    missing = [n.name for n in items if not ast.get_docstring(n)]
    checks.append(("All functions/classes have docstrings", len(missing) == 0))
    if missing:
        checks.append((f"Missing: {missing}", False))

    # Google style checks
    checks.append(("Has Args: section", "Args:" in source))
    checks.append(("Has Returns: section", "Returns:" in source))
    checks.append(("Has Raises: section", "Raises:" in source))

    return checks


def run_pydocstyle():
    """Run pydocstyle if available."""
    try:
        proc = subprocess.run(
            ["pydocstyle", "calculator.py"],
            capture_output=True, text=True, timeout=30,
        )
        return proc.returncode == 0, proc.stdout + proc.stderr
    except FileNotFoundError:
        return None, "pydocstyle not installed (skipped)"
    except subprocess.TimeoutExpired:
        return False, "pydocstyle timed out"


def main():
    result = {"passed": False, "metrics": {}, "details": []}

    checks = check_docstrings()
    passed = sum(1 for _, ok in checks if ok)
    result["metrics"]["checks_passed"] = passed
    result["metrics"]["checks_total"] = len(checks)
    for name, ok in checks:
        if not ok:
            result["details"].append(f"FAIL: {name}")

    style_ok, style_out = run_pydocstyle()
    if style_ok is not None:
        result["metrics"]["pydocstyle_passed"] = style_ok
        if not style_ok:
            result["details"].append(f"pydocstyle: {style_out}")
    else:
        result["details"].append(style_out)

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
