import os
import sqlite3
import subprocess
import sys
from datetime import datetime, timedelta

import pytest


@pytest.fixture
def db():
    conn = sqlite3.connect(":memory:")
    with open("schema.sql") as f:
        conn.executescript(f.read())

    # Insert test data
    now = datetime.now()
    recent = (now - timedelta(days=30)).strftime("%Y-%m-%d")
    old = (now - timedelta(days=400)).strftime("%Y-%m-%d")

    customers = [
        (1, "Alice", "alice@test.com", "2023-01-01"),
        (2, "Bob", "bob@test.com", "2023-02-01"),
        (3, "Charlie", "charlie@test.com", "2023-03-01"),
        (4, "Dave", "dave@test.com", "2023-04-01"),
    ]
    conn.executemany("INSERT INTO customers VALUES (?,?,?,?)", customers)

    orders = [
        (1, 1, recent, "completed"),
        (2, 1, recent, "completed"),
        (3, 1, old, "completed"),  # too old, should be excluded
        (4, 2, recent, "completed"),
        (5, 2, recent, "completed"),
        (6, 2, recent, "completed"),
        (7, 3, recent, "completed"),  # only 1 order, should be excluded
        (8, 4, recent, "cancelled"),  # cancelled, excluded
        (9, 4, recent, "completed"),
        (10, 4, recent, "completed"),
    ]
    conn.executemany("INSERT INTO orders VALUES (?,?,?,?)", orders)

    items = [
        (1, 1, "Widget", 2, 10.00),
        (2, 2, "Gadget", 1, 50.00),
        (3, 3, "Widget", 3, 10.00),
        (4, 4, "Gizmo", 5, 5.00),
        (5, 5, "Widget", 2, 10.00),
        (6, 6, "Gadget", 1, 50.00),
        (7, 7, "Widget", 10, 10.00),
        (8, 8, "Gizmo", 2, 5.00),
        (9, 9, "Widget", 1, 10.00),
        (10, 10, "Gadget", 2, 50.00),
    ]
    conn.executemany("INSERT INTO order_items VALUES (?,?,?,?,?)", items)
    conn.commit()
    yield conn
    conn.close()


def test_query_file_exists():
    assert os.path.exists("query.sql"), "query.sql not found"


def test_query_returns_results(db):
    with open("query.sql") as f:
        query = f.read()
    cursor = db.execute(query)
    rows = cursor.fetchall()
    assert len(rows) > 0, "Query should return results"


def test_query_excludes_old_orders(db):
    with open("query.sql") as f:
        query = f.read()
    cursor = db.execute(query)
    rows = cursor.fetchall()
    # Alice should have total from 2 recent orders (20 + 50 = 70), not 3
    alice = [r for r in rows if r[1] == "Alice"]
    if alice:
        assert alice[0][2] == 70.0, f"Alice total should be 70.0, got {alice[0][2]}"


def test_query_excludes_single_order_customers(db):
    with open("query.sql") as f:
        query = f.read()
    cursor = db.execute(query)
    rows = cursor.fetchall()
    names = [r[1] for r in rows]
    assert "Charlie" not in names, "Charlie has only 1 order, should be excluded"


def test_query_excludes_cancelled_orders(db):
    with open("query.sql") as f:
        query = f.read()
    cursor = db.execute(query)
    rows = cursor.fetchall()
    dave = [r for r in rows if r[1] == "Dave"]
    if dave:
        # Dave: 2 completed orders (10 + 100 = 110), cancelled order excluded
        assert dave[0][2] == 110.0, f"Dave total should be 110.0, got {dave[0][2]}"


def test_query_ordered_by_total_desc(db):
    with open("query.sql") as f:
        query = f.read()
    cursor = db.execute(query)
    rows = cursor.fetchall()
    totals = [r[2] for r in rows]
    assert totals == sorted(totals, reverse=True), "Results should be ordered by total descending"


def test_query_has_required_columns(db):
    with open("query.sql") as f:
        query = f.read()
    cursor = db.execute(query)
    columns = [desc[0] for desc in cursor.description]
    required = ["customer_id", "customer_name", "total_amount",
                "order_count", "avg_order_value", "last_order_date"]
    for col in required:
        assert col in columns, f"Missing column: {col}"


def test_query_limits_to_10(db):
    with open("query.sql") as f:
        query = f.read()
    cursor = db.execute(query)
    rows = cursor.fetchall()
    assert len(rows) <= 10, "Query should return at most 10 rows"


def test_bob_has_correct_totals(db):
    with open("query.sql") as f:
        query = f.read()
    cursor = db.execute(query)
    rows = cursor.fetchall()
    bob = [r for r in rows if r[1] == "Bob"]
    assert len(bob) == 1
    bob = bob[0]
    # Order 4: 5*5=25, Order 5: 2*10=20, Order 6: 1*50=50 -> total=95
    assert bob[2] == 95.0, f"Bob total should be 95.0, got {bob[2]}"
    assert bob[3] == 3  # 3 completed orders
