#!/usr/bin/env python3
"""Evaluation script for microservice_decomposition task."""
import json
import os
import re
import subprocess
import sys


def check_mermaid():
    """Check Mermaid syntax validity."""
    checks = []
    if not os.path.exists("architecture.md"):
        return [("architecture.md exists", False)]

    with open("architecture.md") as f:
        content = f.read()

    checks.append(("architecture.md exists", True))
    checks.append(("Mermaid block present", "```mermaid" in content))

    match = re.search(r"```mermaid\n(.*?)```", content, re.DOTALL)
    if match:
        diagram = match.group(1).strip()
        checks.append(("Mermaid has graph declaration", diagram.splitlines()[0].strip().startswith("graph")))
        # Check for nodes (at least 4)
        node_pattern = re.findall(r"(\w+)\[", diagram)
        checks.append(("At least 4 nodes in diagram", len(set(node_pattern)) >= 4))
        # Check for edges
        checks.append(("Has communication edges", "-->" in diagram or "---" in diagram))
    else:
        checks.append(("Mermaid has graph declaration", False))
        checks.append(("At least 4 nodes in diagram", False))
        checks.append(("Has communication edges", False))

    return checks


def check_service_boundaries():
    """Check that services.py defines proper boundaries."""
    checks = []
    if not os.path.exists("services.py"):
        return [("services.py exists", False)]

    with open("services.py") as f:
        content = f.read()

    checks.append(("services.py exists", True))
    # Check for at least 4 service definitions
    service_mentions = re.findall(r"(?:class\s+\w+Service|name\s*=\s*[\"']\w+[\"'])", content)
    checks.append(("At least 4 service definitions", len(service_mentions) >= 4))

    # Check for required fields
    for field in ["responsibility", "database", "endpoints", "dependencies"]:
        checks.append((f"Has {field} field", field in content))

    return checks


def main():
    result = {"passed": False, "metrics": {}, "details": []}

    # Static checks
    mermaid_checks = check_mermaid()
    boundary_checks = check_service_boundaries()
    all_checks = mermaid_checks + boundary_checks

    passed_checks = sum(1 for _, ok in all_checks if ok)
    result["metrics"]["static_checks_passed"] = passed_checks
    result["metrics"]["static_checks_total"] = len(all_checks)
    for name, ok in all_checks:
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
        result["passed"] = proc.returncode == 0 and passed_checks == len(all_checks)
    except subprocess.TimeoutExpired:
        result["details"].append("Tests timed out after 120s")
    except FileNotFoundError:
        result["details"].append("pytest not found")

    print(json.dumps(result, indent=2))
    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
