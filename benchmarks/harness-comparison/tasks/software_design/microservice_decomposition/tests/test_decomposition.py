import importlib
import os
import re

import pytest


def test_services_file_exists():
    assert os.path.exists("services.py"), "services.py not found"


def test_architecture_md_exists():
    assert os.path.exists("architecture.md"), "architecture.md not found"


def test_services_importable():
    mod = importlib.import_module("services")
    assert hasattr(mod, "services") or any(
        hasattr(mod, attr) for attr in ["UserService", "ProductService", "OrderService", "PaymentService"]
    )


def test_at_least_four_services():
    mod = importlib.import_module("services")
    # Try to find a list of services or individual service classes
    service_count = 0
    for attr_name in dir(mod):
        obj = getattr(mod, attr_name)
        if isinstance(obj, type) and attr_name.endswith("Service"):
            service_count += 1
    if hasattr(mod, "services") and isinstance(mod.services, list):
        service_count = max(service_count, len(mod.services))
    assert service_count >= 4, f"Expected at least 4 services, found {service_count}"


def test_service_has_required_fields():
    mod = importlib.import_module("services")
    required_fields = {"name", "responsibility", "database", "endpoints", "dependencies"}

    services = []
    if hasattr(mod, "services") and isinstance(mod.services, list):
        services = mod.services
    else:
        for attr_name in dir(mod):
            obj = getattr(mod, attr_name)
            if isinstance(obj, type) and attr_name.endswith("Service"):
                try:
                    instance = obj()
                    services.append(instance)
                except Exception:
                    pass

    assert len(services) > 0, "No services found"
    for svc in services:
        if hasattr(svc, "__dict__"):
            attrs = set(vars(svc).keys())
        elif isinstance(svc, dict):
            attrs = set(svc.keys())
        else:
            attrs = set(dir(svc))
        missing = required_fields - attrs
        assert not missing, f"Service missing fields: {missing}"


def test_mermaid_diagram_present():
    with open("architecture.md") as f:
        content = f.read()
    assert "```mermaid" in content, "No Mermaid diagram found"
    assert "graph" in content, "No graph declaration in Mermaid"


def test_mermaid_valid_syntax():
    with open("architecture.md") as f:
        content = f.read()
    match = re.search(r"```mermaid\n(.*?)```", content, re.DOTALL)
    assert match, "No mermaid code block found"
    diagram = match.group(1).strip()
    first_line = diagram.splitlines()[0].strip()
    assert first_line.startswith("graph"), f"Mermaid must start with graph, got: {first_line}"


def test_service_table_present():
    with open("architecture.md") as f:
        content = f.read()
    assert "|" in content, "No table found in architecture.md"
    # Check for table headers
    assert "name" in content.lower() or "service" in content.lower(), "No service table headers"
