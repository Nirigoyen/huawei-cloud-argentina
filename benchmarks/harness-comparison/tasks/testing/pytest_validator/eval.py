#!/usr/bin/env python3
"""Evaluation script for pytest_validator task."""
import json
import os
import re
import subprocess
import sys


def main():
    result = {"passed": False, "metrics": {}, "details": []}

    if not os.path.exists("test_user.py"):
        result["details"].append("test_user.py not found")
        print(json.dumps(result, indent=2))
        sys.exit(1)

    # Check test file content
    with open("test_user.py") as f:
        content = f.read()
    checks = [
        ("Has parametrize", "parametrize" in content or "param" in content),
        ("Has fixture", "@pytest.fixture" in content or "fixture" in content),
        ("Has 10+ tests", content.count("def test_") >= 10),
    ]
    passed = sum(1 for _, ok in checks if ok)
    result["metrics"]["checks_passed"] = passed
    result["metrics"]["checks_total"] = len(checks)
    for name, ok in checks:
        if not ok:
            result["details"].append(f"FAIL: {name}")

    # Run tests with coverage
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "test_user.py", "--cov=user",
             "--cov-report=term", "-v", "--tb=short"],
            capture_output=True, text=True, timeout=120,
        )
        output = proc.stdout + proc.stderr
        result["details"].append(output)

        # Extract coverage
        match = re.search(r"user\.py\s+\d+\s+\d+\s+(\d+)%", output)
        if not match:
            match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", output)
        if match:
            coverage = int(match.group(1))
            result["metrics"]["coverage"] = coverage
            if coverage < 90:
                result["details"].append(f"FAIL: Coverage {coverage}% < 90%")
                passed -= 1

        result["metrics"]["test_exit_code"] = proc.returncode
        result["passed"] = proc.returncode == 0 and passed == len(checks)
    except subprocess.TimeoutExpired:
        result["details"].append("Tests timed out")
    except FileNotFoundError:
        result["details"].append("pytest not found")

    # Also run the meta-tests
    try:
        proc2 = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short", "-q"],
            capture_output=True, text=True, timeout=120,
        )
        result["details"].append(proc2.stdout)
        if proc2.returncode != 0:
            result["passed"] = False
    except Exception:
        pass

    print(json.dumps(result, indent=2))
    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
