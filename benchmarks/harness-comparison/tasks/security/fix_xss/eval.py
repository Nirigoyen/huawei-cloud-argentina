#!/usr/bin/env python3
"""Evaluation script for fix_xss task."""
import json
import os
import re
import subprocess
import sys


def check_sanitization():
    checks = []
    if not os.path.exists("server.js"):
        return [("server.js exists", False)]

    with open("server.js") as f:
        content = f.read()

    checks.append(("server.js exists", True))

    # Check for sanitization/escaping
    has_sanitize = any(term in content for term in [
        "escapeHtml", "sanitize", "DOMPurify", "encodeURI",
        "replace", "&lt;", "&amp;", "helmet", "xss",
    ])
    checks.append(("Has sanitization/escaping", has_sanitize))

    # Check for security headers
    has_csp = "Content-Security-Policy" in content or "helmet" in content
    checks.append(("Has Content-Security-Policy", has_csp))

    has_nosniff = "nosniff" in content or "helmet" in content
    checks.append(("Has X-Content-Type-Options", has_nosniff))

    # Check that raw template literals with user input are not used unsanitized
    # Look for ${req.query without any wrapping function
    raw_injections = re.findall(r"\$\{req\.query\.\w+\}", content)
    checks.append(("No raw req.query in templates", len(raw_injections) == 0))

    return checks


def main():
    result = {"passed": False, "metrics": {}, "details": []}

    checks = check_sanitization()
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
        result["metrics"]["test_exit_code"] = proc.returncode
        result["passed"] = proc.returncode == 0 and passed == len(checks)
    except subprocess.TimeoutExpired:
        result["details"].append("Tests timed out")
    except FileNotFoundError:
        result["details"].append("jest/npx not found")

    print(json.dumps(result, indent=2))
    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
