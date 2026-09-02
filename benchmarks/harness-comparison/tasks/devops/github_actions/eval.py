#!/usr/bin/env python3
"""Evaluation script for github_actions task."""
import json
import os
import subprocess
import sys

import yaml


def validate_workflow():
    """Validate the GitHub Actions workflow YAML."""
    checks = []
    path = ".github/workflows/ci.yml"

    if not os.path.exists(path):
        return [("Workflow file exists", False)]

    checks.append(("Workflow file exists", True))

    try:
        with open(path) as f:
            data = yaml.safe_load(f)
        checks.append(("Valid YAML", isinstance(data, dict)))
    except yaml.YAMLError as e:
        checks.append(("Valid YAML", False))
        checks.append((f"YAML error: {e}", False))
        return checks

    # Triggers
    on = data.get("on", data.get(True, {}))
    checks.append(("Has push trigger", "push" in on))
    checks.append(("Has pull_request trigger", "pull_request" in on))

    # Jobs
    jobs = data.get("jobs", {})
    checks.append(("Has ci job", "ci" in jobs))
    checks.append(("Has security job", "security" in jobs))

    if "security" in jobs:
        checks.append(("security needs ci", jobs["security"].get("needs") == "ci"))

    # Steps
    if "ci" in jobs:
        steps = jobs["ci"].get("steps", [])
        checks.append(("ci has 6+ steps", len(steps) >= 6))
        actions = [s.get("uses", "") for s in steps if "uses" in s]
        checks.append(("Uses checkout", any("checkout" in a for a in actions)))
        checks.append(("Uses setup-python", any("setup-python" in a for a in actions)))
        checks.append(("Uses codecov", any("codecov" in a for a in actions)))
        runs = [s.get("run", "") for s in steps if "run" in s]
        checks.append(("Runs pytest", any("pytest" in r for r in runs)))
        checks.append(("Runs ruff", any("ruff" in r for r in runs)))
        checks.append(("Uses pip cache", any("cache" in str(s) for s in steps)))

    return checks


def main():
    result = {"passed": False, "metrics": {}, "details": []}

    checks = validate_workflow()
    passed = sum(1 for _, ok in checks if ok)
    result["metrics"]["checks_passed"] = passed
    result["metrics"]["checks_total"] = len(checks)
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
