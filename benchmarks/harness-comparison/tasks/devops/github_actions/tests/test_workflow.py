import os

import pytest
import yaml


def load_workflow():
    path = ".github/workflows/ci.yml"
    assert os.path.exists(path), f"{path} not found"
    with open(path) as f:
        return yaml.safe_load(f)


def test_file_exists():
    assert os.path.exists(".github/workflows/ci.yml")


def test_valid_yaml():
    data = load_workflow()
    assert isinstance(data, dict)


def test_triggers():
    data = load_workflow()
    on = data.get("on", data.get(True, {}))  # yaml may parse 'on' as True
    assert "push" in on, "Must trigger on push"
    assert "pull_request" in on, "Must trigger on pull_request"
    push_branches = on["push"].get("branches", [])
    assert "main" in push_branches, "Push must include main branch"
    pr_branches = on["pull_request"].get("branches", [])
    assert "main" in pr_branches, "PR must target main branch"


def test_ci_job():
    data = load_workflow()
    jobs = data.get("jobs", {})
    assert "ci" in jobs, "Must have 'ci' job"
    ci = jobs["ci"]
    assert ci.get("runs-on") == "ubuntu-latest"


def test_ci_steps():
    data = load_workflow()
    ci = data["jobs"]["ci"]
    steps = ci.get("steps", [])
    assert len(steps) >= 6, f"Expected at least 6 steps, found {len(steps)}"

    actions_used = [s.get("uses", "") for s in steps if "uses" in s]
    assert any("checkout" in a for a in actions_used), "Must use actions/checkout"
    assert any("setup-python" in a for a in actions_used), "Must use setup-python"
    assert any("codecov" in a for a in actions_used), "Must use codecov-action"

    run_commands = [s.get("run", "") for s in steps if "run" in s]
    assert any("pytest" in r for r in run_commands), "Must run pytest"
    assert any("ruff" in r for r in run_commands), "Must run ruff"


def test_pip_caching():
    data = load_workflow()
    ci = data["jobs"]["ci"]
    steps = ci.get("steps", [])
    has_cache = any("cache" in str(s) for s in steps)
    assert has_cache, "Must use pip caching"


def test_security_job():
    data = load_workflow()
    jobs = data.get("jobs", {})
    assert "security" in jobs, "Must have 'security' job"
    security = jobs["security"]
    assert security.get("needs") == "ci", "security job must need ci"
    steps = security.get("steps", [])
    run_commands = [s.get("run", "") for s in steps if "run" in s]
    assert any("bandit" in r for r in run_commands), "Must run bandit"
    assert any("pip-audit" in r for r in run_commands), "Must run pip-audit"


def test_requirements_txt():
    assert os.path.exists("requirements.txt")
    with open("requirements.txt") as f:
        content = f.read()
    assert "flask" in content.lower()
    assert "pytest" in content.lower()
    assert "ruff" in content.lower()
