#!/usr/bin/env python3
"""Evaluation script for jest_usefetch task."""
import json
import os
import subprocess
import sys


def main():
    result = {"passed": False, "metrics": {}, "details": []}

    if not os.path.exists("useFetch.test.js"):
        result["details"].append("useFetch.test.js not found")
        print(json.dumps(result, indent=2))
        sys.exit(1)

    # Check test file content
    with open("useFetch.test.js") as f:
        content = f.read()

    checks = [
        ("Mocks fetch", "fetch" in content and ("mock" in content.lower() or "jest.fn" in content)),
        ("Tests initial state", "loading" in content.lower() or "initial" in content.lower()),
        ("Tests success", "resolve" in content.lower() or "data" in content.lower()),
        ("Tests error", "error" in content.lower() or "reject" in content.lower()),
        ("Has 4+ test cases", len(__import__("re").findall(r"test\(|it\(", content)) >= 4),
        ("Uses renderHook or testing-library", "renderHook" in content or "testing-library" in content),
    ]
    passed = sum(1 for _, ok in checks if ok)
    result["metrics"]["checks_passed"] = passed
    result["metrics"]["checks_total"] = len(checks)
    for name, ok in checks:
        if not ok:
            result["details"].append(f"FAIL: {name}")

    # Run the useFetch tests
    try:
        proc = subprocess.run(
            ["npx", "jest", "useFetch.test.js", "--verbose", "--forceExit"],
            capture_output=True, text=True, timeout=120,
        )
        result["details"].append(proc.stdout)
        if proc.stderr:
            result["details"].append(proc.stderr)
        result["metrics"]["usefetch_test_exit_code"] = proc.returncode
    except subprocess.TimeoutExpired:
        result["details"].append("useFetch tests timed out")
    except FileNotFoundError:
        result["details"].append("jest/npx not found")

    # Run meta-tests
    try:
        proc2 = subprocess.run(
            ["npx", "jest", "tests/", "--verbose", "--forceExit"],
            capture_output=True, text=True, timeout=120,
        )
        result["details"].append(proc2.stdout)
        if proc2.stderr:
            result["details"].append(proc2.stderr)
        result["metrics"]["meta_test_exit_code"] = proc2.returncode
        result["passed"] = proc2.returncode == 0 and passed == len(checks)
    except subprocess.TimeoutExpired:
        result["details"].append("Meta tests timed out")
    except FileNotFoundError:
        result["details"].append("jest/npx not found")

    print(json.dumps(result, indent=2))
    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
