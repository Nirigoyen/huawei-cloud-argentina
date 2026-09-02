import os
import subprocess
import sys

import pytest


def test_test_file_exists():
    assert os.path.exists("test_user.py"), "test_user.py not found"


def test_achieves_90_percent_coverage():
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "test_user.py", "--cov=user", "--cov-report=term", "-q"],
        capture_output=True, text=True, timeout=120,
    )
    output = proc.stdout + proc.stderr
    # Look for coverage percentage
    assert "user.py" in output, "Coverage report not found"
    # Extract percentage
    import re
    match = re.search(r"user\.py\s+\d+\s+\d+\s+(\d+)%", output)
    if not match:
        match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", output)
    assert match, f"Could not parse coverage from output:\n{output}"
    coverage = int(match.group(1))
    assert coverage >= 90, f"Coverage {coverage}% is below 90%"


def test_uses_parametrize():
    with open("test_user.py") as f:
        content = f.read()
    assert "parametrize" in content or "param" in content, \
        "Must use parametrized tests"


def test_uses_fixture():
    with open("test_user.py") as f:
        content = f.read()
    assert "@pytest.fixture" in content or "fixture" in content, \
        "Must use at least one fixture"


def test_has_at_least_10_tests():
    with open("test_user.py") as f:
        content = f.read()
    test_count = content.count("def test_")
    assert test_count >= 10, f"Expected at least 10 tests, found {test_count}"
