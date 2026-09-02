#!/usr/bin/env python3
"""Evaluation script for payment_strategy task."""
import importlib
import inspect
import json
import subprocess
import sys


def check_types():
    """Check that required classes exist with correct base types."""
    checks = []
    try:
        mod = importlib.import_module("solution")
        # Check abstract base
        checks.append(("PaymentStrategy exists", hasattr(mod, "PaymentStrategy")))
        checks.append(("CreditCardPayment exists", hasattr(mod, "CreditCardPayment")))
        checks.append(("PayPalPayment exists", hasattr(mod, "PayPalPayment")))
        checks.append(("CryptoPayment exists", hasattr(mod, "CryptoPayment")))
        checks.append(("PaymentContext exists", hasattr(mod, "PaymentContext")))
        checks.append(("PaymentProcessor exists", hasattr(mod, "PaymentProcessor")))

        # Check inheritance
        if hasattr(mod, "CreditCardPayment") and hasattr(mod, "PaymentStrategy"):
            checks.append(("CreditCardPayment inherits PaymentStrategy",
                           issubclass(mod.CreditCardPayment, mod.PaymentStrategy)))
        if hasattr(mod, "PayPalPayment") and hasattr(mod, "PaymentStrategy"):
            checks.append(("PayPalPayment inherits PaymentStrategy",
                           issubclass(mod.PayPalPayment, mod.PaymentStrategy)))
        if hasattr(mod, "CryptoPayment") and hasattr(mod, "PaymentStrategy"):
            checks.append(("CryptoPayment inherits PaymentStrategy",
                           issubclass(mod.CryptoPayment, mod.PaymentStrategy)))

        # Check abstract method
        if hasattr(mod, "PaymentStrategy"):
            checks.append(("PaymentStrategy.pay is abstract",
                           getattr(mod.PaymentStrategy.pay, "__isabstractmethod__", False)))
    except Exception as e:
        checks.append(("import succeeded", False))
        checks.append((f"import error: {e}", False))
    return checks


def main():
    result = {"passed": False, "metrics": {}, "details": []}

    # Type checks
    type_checks = check_types()
    passed_types = sum(1 for _, ok in type_checks if ok)
    result["metrics"]["type_checks_passed"] = passed_types
    result["metrics"]["type_checks_total"] = len(type_checks)
    for name, ok in type_checks:
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
        result["passed"] = proc.returncode == 0 and passed_types == len(type_checks)
    except subprocess.TimeoutExpired:
        result["details"].append("Tests timed out after 120s")
    except FileNotFoundError:
        result["details"].append("pytest not found")

    print(json.dumps(result, indent=2))
    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
