#!/usr/bin/env python3
"""Evaluation script for ansible_harden task."""
import json
import os
import subprocess
import sys

import yaml


def check_role():
    checks = []
    files = [
        "roles/harden/tasks/main.yml",
        "roles/harden/handlers/main.yml",
        "roles/harden/defaults/main.yml",
        "roles/harden/meta/main.yml",
    ]
    for f in files:
        checks.append((f"{f} exists", os.path.exists(f)))

    # Check tasks content
    tasks_path = "roles/harden/tasks/main.yml"
    if os.path.exists(tasks_path):
        with open(tasks_path) as f:
            content = f.read()
        checks.append(("Updates packages", "apt" in content or "yum" in content or "package" in content))
        checks.append(("Configures UFW", "ufw" in content))
        checks.append(("Disables root SSH", "PermitRootLogin" in content))
        checks.append(("Disables password auth", "PasswordAuthentication" in content))
        checks.append(("Sets SSH port 2222", "2222" in content))
        checks.append(("Installs fail2ban", "fail2ban" in content))
        checks.append(("Removes telnet", "telnet" in content))
        checks.append(("Sets file permissions", "/etc/shadow" in content))

    # Check defaults
    defaults_path = "roles/harden/defaults/main.yml"
    if os.path.exists(defaults_path):
        with open(defaults_path) as f:
            defaults = yaml.safe_load(f)
        if isinstance(defaults, dict):
            checks.append(("ssh_port=2222", defaults.get("ssh_port") == 2222))
            checks.append(("has allowed_ports", "allowed_ports" in defaults))

    return checks


def run_ansible_lint():
    try:
        proc = subprocess.run(
            ["ansible-lint", "roles/harden/"],
            capture_output=True, text=True, timeout=60,
        )
        return proc.returncode == 0, proc.stdout + proc.stderr
    except FileNotFoundError:
        return None, "ansible-lint not installed (skipped)"
    except subprocess.TimeoutExpired:
        return False, "ansible-lint timed out"


def main():
    result = {"passed": False, "metrics": {}, "details": []}

    checks = check_role()
    passed = sum(1 for _, ok in checks if ok)
    result["metrics"]["checks_passed"] = passed
    result["metrics"]["checks_total"] = len(checks)
    for name, ok in checks:
        if not ok:
            result["details"].append(f"FAIL: {name}")

    lint_ok, lint_out = run_ansible_lint()
    if lint_ok is not None:
        result["metrics"]["ansible_lint_passed"] = lint_ok
        if not lint_ok:
            result["details"].append(f"ansible-lint: {lint_out}")
    else:
        result["details"].append(lint_out)

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
