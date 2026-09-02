#!/usr/bin/env python3
"""Evaluation script for k8s_manifests task."""
import json
import os
import subprocess
import sys

import yaml


def load_manifests():
    docs = []
    if os.path.exists("k8s.yaml"):
        with open("k8s.yaml") as f:
            docs = list(yaml.safe_load_all(f))
    elif os.path.isdir("k8s"):
        for fn in sorted(os.listdir("k8s")):
            if fn.endswith((".yaml", ".yml")):
                with open(f"k8s/{fn}") as f:
                    docs.extend(list(yaml.safe_load_all(f)))
    return [d for d in docs if d is not None]


def validate_manifests():
    checks = []
    docs = load_manifests()

    if not docs:
        return [("Manifests loaded", False)]
    checks.append(("Manifests loaded", True))

    kinds = {d.get("kind") for d in docs}
    checks.append(("Has Deployment", "Deployment" in kinds))
    checks.append(("Has Service", "Service" in kinds))
    checks.append(("Has Ingress", "Ingress" in kinds))
    checks.append(("Has HPA", "HorizontalPodAutoscaler" in kinds))

    # Check apiVersions
    for d in docs:
        kind = d.get("kind")
        ver = d.get("apiVersion", "")
        if kind == "Deployment":
            checks.append(("Deployment apps/v1", ver == "apps/v1"))
        elif kind == "Ingress":
            checks.append(("Ingress networking.k8s.io/v1", ver == "networking.k8s.io/v1"))
        elif kind == "HorizontalPodAutoscaler":
            checks.append(("HPA autoscaling/v2", ver == "autoscaling/v2"))

    # Check namespace
    for d in docs:
        ns = d.get("metadata", {}).get("namespace", "")
        if ns != "production":
            checks.append((f"{d.get('kind')} namespace=production", False))
            break
    else:
        checks.append(("All resources in production namespace", True))

    return checks


def main():
    result = {"passed": False, "metrics": {}, "details": []}

    checks = validate_manifests()
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
