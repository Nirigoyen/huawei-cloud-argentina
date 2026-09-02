#!/usr/bin/env python3
"""Evaluation script for terraform_vpc task."""
import json
import os
import re
import subprocess
import sys


def check_files():
    checks = []
    for f in ["modules/vpc/main.tf", "modules/vpc/variables.tf", "modules/vpc/outputs.tf"]:
        checks.append((f"{f} exists", os.path.exists(f)))
    return checks


def check_content():
    checks = []
    main_path = "modules/vpc/main.tf"
    if not os.path.exists(main_path):
        return checks

    with open(main_path) as f:
        content = f.read()

    checks.append(("Has aws_vpc", "aws_vpc" in content))
    checks.append(("Has DNS support", "enable_dns_support" in content))
    checks.append(("Has DNS hostnames", "enable_dns_hostnames" in content))
    checks.append(("Has 4+ subnets", len(re.findall(r"aws_subnet\b", content)) >= 4))
    checks.append(("Has Internet Gateway", "aws_internet_gateway" in content))
    checks.append(("Has NAT Gateway", "aws_nat_gateway" in content))
    checks.append(("Has route tables", "aws_route_table" in content))
    checks.append(("Has route table associations", "aws_route_table_association" in content))
    checks.append(("Routes 0.0.0.0/0", "0.0.0.0/0" in content))
    checks.append(("Has tags", "tags" in content))

    return checks


def run_terraform_validate():
    """Run terraform validate if available."""
    if not os.path.exists("modules/vpc/main.tf"):
        return None, "main.tf not found"
    try:
        subprocess.run(["terraform", "fmt", "-check", "modules/vpc/"],
                       capture_output=True, timeout=30)
        proc = subprocess.run(
            ["terraform", "init", "-backend=false"],
            capture_output=True, text=True, timeout=60,
            cwd="modules/vpc/",
        )
        proc2 = subprocess.run(
            ["terraform", "validate", "-json"],
            capture_output=True, text=True, timeout=30,
            cwd="modules/vpc/",
        )
        if proc2.returncode == 0:
            data = json.loads(proc2.stdout)
            return data.get("valid", False), proc2.stdout
        return False, proc2.stderr
    except FileNotFoundError:
        return None, "terraform not installed (skipped)"
    except subprocess.TimeoutExpired:
        return False, "terraform timed out"
    except json.JSONDecodeError:
        return False, "Could not parse terraform output"


def main():
    result = {"passed": False, "metrics": {}, "details": []}

    checks = check_files() + check_content()
    passed = sum(1 for _, ok in checks if ok)
    result["metrics"]["checks_passed"] = passed
    result["metrics"]["checks_total"] = len(checks)
    for name, ok in checks:
        if not ok:
            result["details"].append(f"FAIL: {name}")

    # Terraform validate
    tf_ok, tf_out = run_terraform_validate()
    if tf_ok is not None:
        result["metrics"]["terraform_valid"] = tf_ok
        if not tf_ok:
            result["details"].append(f"terraform: {tf_out}")
    else:
        result["details"].append(tf_out)

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
