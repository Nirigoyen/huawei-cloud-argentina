import os
import sqlite3

import pytest
from app import app, init_db, get_db


@pytest.fixture
def client():
    if os.path.exists("test.db"):
        os.remove("test.db")
    init_db()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client
    if os.path.exists("test.db"):
        os.remove("test.db")


def test_get_user_normal(client):
    resp = client.get("/users/admin")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["username"] == "admin"


def test_get_user_not_found(client):
    resp = client.get("/users/nonexistent")
    assert resp.status_code == 404


def test_get_user_sqli_union(client):
    # Classic UNION-based SQL injection
    resp = client.get("/users/' UNION SELECT 1,2,3,4--")
    assert resp.status_code == 404


def test_get_user_sqli_or_true(client):
    # ' OR '1'='1 injection
    resp = client.get("/users/' OR '1'='1")
    assert resp.status_code == 404


def test_get_user_sqli_comment(client):
    # Comment-based injection
    resp = client.get("/users/admin'--")
    assert resp.status_code == 404


def test_search_users_normal(client):
    resp = client.get("/users/search?role=admin")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 1
    assert data[0]["username"] == "admin"


def test_search_users_sqli(client):
    resp = client.get("/users/search?role=' OR '1'='1")
    assert resp.status_code == 200
    data = resp.get_json()
    # Should NOT return all users (injection should fail)
    assert len(data) == 0


def test_products_normal(client):
    resp = client.get("/products?category=gadgets")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 2


def test_products_sqli(client):
    resp = client.get("/products?category=' OR '1'='1")
    assert resp.status_code == 200
    data = resp.get_json()
    # Should not return all products
    assert len(data) == 0


def test_get_product_normal(client):
    resp = client.get("/products/1")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["name"] == "Widget"


def test_no_string_format_in_queries():
    """Check that app.py doesn't use f-strings or .format() for SQL queries."""
    with open("app.py") as f:
        content = f.read()
    # Should not have f-string SQL queries
    import re
    # Look for f"SELECT or f'SELECT patterns
    fstring_sql = re.findall(r"f['\"].*SELECT", content)
    assert len(fstring_sql) == 0, f"Found f-string SQL queries: {fstring_sql}"
    # Look for .format() with SELECT
    format_sql = re.findall(r"\.format\(\).*SELECT|SELECT.*\.format\(\)", content)
    assert len(format_sql) == 0, f"Found .format() SQL queries: {format_sql}"


def test_uses_parameterized_queries():
    """Check that queries use ? placeholders."""
    with open("app.py") as f:
        content = f.read()
    # Should have parameterized queries with ? placeholders
    assert "WHERE username = ?" in content or "WHERE username=?" in content, \
        "Must use parameterized query for username lookup"
