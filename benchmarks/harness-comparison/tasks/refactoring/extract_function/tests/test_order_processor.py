import pytest
from order_processor import process_order


@pytest.fixture
def inventory():
    return {
        "SKU001": {"name": "Widget", "price": 9.99, "stock": 100, "weight": 2},
        "SKU002": {"name": "Gadget", "price": 19.99, "stock": 50, "weight": 5},
        "SKU003": {"name": "Gizmo", "price": 4.99, "stock": 200, "weight": 1},
    }


@pytest.fixture
def customer():
    return {"id": "CUST001", "name": "Alice", "tier": "gold"}


@pytest.fixture
def config():
    return {"tax_rate": 0.08}


@pytest.fixture
def order():
    return {"items": [{"sku": "SKU001", "quantity": 2}, {"sku": "SKU003", "quantity": 3}]}


def test_basic_order(order, customer, inventory, config):
    result = process_order(order, customer, inventory, config)
    assert "order" in result
    assert "audit" in result
    assert result["order"]["status"] == "processed"


def test_order_has_total(order, customer, inventory, config):
    result = process_order(order, customer, inventory, config)
    assert result["order"]["total"] > 0
    assert result["order"]["subtotal"] == pytest.approx(9.99 * 2 + 4.99 * 3)


def test_gold_discount(order, customer, inventory, config):
    result = process_order(order, customer, inventory, config)
    assert result["order"]["discount"] > 0
    expected_discount = (9.99 * 2 + 4.99 * 3) * 0.15
    assert result["order"]["discount"] == pytest.approx(expected_discount, rel=0.01)


def test_silver_discount(order, inventory, config):
    customer = {"id": "CUST002", "name": "Bob", "tier": "silver"}
    result = process_order(order, customer, inventory, config)
    expected_discount = (9.99 * 2 + 4.99 * 3) * 0.10
    assert result["order"]["discount"] == pytest.approx(expected_discount, rel=0.01)


def test_no_discount(order, inventory, config):
    customer = {"id": "CUST003", "name": "Charlie", "tier": "none"}
    result = process_order(order, customer, inventory, config)
    assert result["order"]["discount"] == 0


def test_coupon_discount(order, customer, inventory, config):
    order["coupon"] = "SAVE10"
    result = process_order(order, customer, inventory, config)
    subtotal = 9.99 * 2 + 4.99 * 3
    expected_discount = subtotal * 0.15 + subtotal * 0.10
    assert result["order"]["discount"] == pytest.approx(expected_discount, rel=0.01)


def test_tax_exempt(order, inventory, config):
    customer = {"id": "CUST004", "name": "Dave", "tier": "gold", "tax_exempt": True}
    result = process_order(order, customer, inventory, config)
    assert result["order"]["tax"] == 0


def test_inventory_updated(order, customer, inventory, config):
    process_order(order, customer, inventory, config)
    assert inventory["SKU001"]["stock"] == 98
    assert inventory["SKU003"]["stock"] == 197


def test_receipt_generated(order, customer, inventory, config):
    result = process_order(order, customer, inventory, config)
    assert "Order Receipt" in result["order"]["receipt"]
    assert "Alice" in result["order"]["receipt"]


def test_audit_log(order, customer, inventory, config):
    result = process_order(order, customer, inventory, config)
    assert result["audit"]["action"] == "order_processed"
    assert result["audit"]["customer_id"] == "CUST001"


def test_invalid_order_no_items(inventory, config):
    with pytest.raises(ValueError):
        process_order({}, {"id": "C001"}, inventory, config)


def test_invalid_order_empty_items(inventory, config):
    with pytest.raises(ValueError):
        process_order({"items": []}, {"id": "C001"}, inventory, config)


def test_insufficient_stock(inventory, config):
    order = {"items": [{"sku": "SKU001", "quantity": 1000}]}
    with pytest.raises(ValueError, match="Insufficient stock"):
        process_order(order, {"id": "C001"}, inventory, config)


def test_unknown_sku(inventory, config):
    order = {"items": [{"sku": "UNKNOWN", "quantity": 1}]}
    with pytest.raises(ValueError, match="Unknown SKU"):
        process_order(order, {"id": "C001"}, inventory, config)


def test_gold_free_shipping(order, inventory, config):
    customer = {"id": "CUST005", "name": "Eve", "tier": "gold"}
    order["items"] = [{"sku": "SKU002", "quantity": 10}]  # $199.90
    result = process_order(order, customer, inventory, config)
    assert result["order"]["shipping"] == 0


def test_multiple_functions_exist():
    """Check that the module has multiple extracted functions."""
    import order_processor
    import inspect
    functions = [name for name, obj in inspect.getmembers(order_processor, inspect.isfunction)
                 if not name.startswith("_")]
    assert len(functions) >= 6, f"Expected 6+ functions, found {len(functions)}: {functions}"
