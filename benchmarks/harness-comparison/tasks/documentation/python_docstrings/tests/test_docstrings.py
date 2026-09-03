import ast
import inspect
import re

import pytest


def get_functions_and_classes(filename):
    with open(filename) as f:
        tree = ast.parse(f.read())
    items = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            items.append(node)
    return items


def test_calculator_importable():
    import calculator
    assert hasattr(calculator, "Calculator")


def test_all_functions_have_docstrings():
    items = get_functions_and_classes("calculator.py")
    missing = [node.name for node in items if not ast.get_docstring(node)]
    assert not missing, f"Missing docstrings: {missing}"


def test_docstrings_have_summary():
    import calculator
    for name, obj in inspect.getmembers(calculator):
        if inspect.isfunction(obj) and obj.__doc__:
            first_line = obj.__doc__.strip().split("\n")[0]
            assert len(first_line) > 10, f"Docstring for {name} has short summary"
            assert first_line.endswith("."), f"Summary for {name} should end with period"


def test_class_has_docstring():
    import calculator
    assert calculator.Calculator.__doc__ is not None
    assert len(calculator.Calculator.__doc__.strip()) > 10


def test_google_style_args_section():
    with open("calculator.py") as f:
        content = f.read()
    # Functions with parameters should have Args section
    assert "Args:" in content, "No Args: section found (Google style)"


def test_google_style_returns_section():
    with open("calculator.py") as f:
        content = f.read()
    assert "Returns:" in content, "No Returns: section found (Google style)"


def test_google_style_raises_section():
    with open("calculator.py") as f:
        content = f.read()
    assert "Raises:" in content, "No Raises: section found (Google style)"


def test_init_has_docstring():
    import calculator
    assert calculator.Calculator.__init__.__doc__ is not None


def test_divide_docstring_mentions_zero():
    import calculator
    assert calculator.Calculator.divide.__doc__ is not None
    doc = calculator.Calculator.divide.__doc__.lower()
    assert "zero" in doc, "divide docstring should mention zero division"


def test_format_result_has_docstring():
    import calculator
    assert calculator.format_result.__doc__ is not None


def test_parse_expression_has_docstring():
    import calculator
    assert calculator.parse_expression.__doc__ is not None
