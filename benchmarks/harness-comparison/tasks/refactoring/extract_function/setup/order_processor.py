import json
from datetime import datetime
from typing import Any


def process_order(order: dict, customer: dict, inventory: dict, config: dict) -> dict:
    # Input validation
    if not order or "items" not in order:
        raise ValueError("Order must contain items")
    if not customer or "id" not in customer:
        raise ValueError("Customer must have an id")
    if not isinstance(order["items"], list) or len(order["items"]) == 0:
        raise ValueError("Order must have at least one item")

    # Validate each item
    for item in order["items"]:
        if "sku" not in item or "quantity" not in item:
            raise ValueError("Each item must have sku and quantity")
        if item["quantity"] <= 0:
            raise ValueError("Item quantity must be positive")
        if item["sku"] not in inventory:
            raise ValueError(f"Unknown SKU: {item['sku']}")
        if inventory[item["sku"]]["stock"] < item["quantity"]:
            raise ValueError(f"Insufficient stock for {item['sku']}")

    # Calculate subtotal
    subtotal = 0
    for item in order["items"]:
        product = inventory[item["sku"]]
        subtotal += product["price"] * item["quantity"]

    # Apply discounts
    discount = 0
    if customer.get("tier") == "gold":
        discount = subtotal * 0.15
    elif customer.get("tier") == "silver":
        discount = subtotal * 0.10
    elif customer.get("tier") == "bronze":
        discount = subtotal * 0.05

    if order.get("coupon") == "SAVE10":
        additional_discount = subtotal * 0.10
        discount += additional_discount

    discounted_subtotal = subtotal - discount

    # Calculate tax
    tax_rate = config.get("tax_rate", 0.08)
    if customer.get("tax_exempt"):
        tax = 0
    else:
        tax = discounted_subtotal * tax_rate

    # Calculate shipping
    total_weight = 0
    for item in order["items"]:
        product = inventory[item["sku"]]
        total_weight += product.get("weight", 1) * item["quantity"]

    if total_weight < 5:
        shipping_cost = 5.99
    elif total_weight < 20:
        shipping_cost = 12.99
    elif total_weight < 50:
        shipping_cost = 24.99
    else:
        shipping_cost = 49.99

    if customer.get("tier") == "gold" and discounted_subtotal > 100:
        shipping_cost = 0

    # Calculate total
    total = discounted_subtotal + tax + shipping_cost

    # Update inventory
    for item in order["items"]:
        inventory[item["sku"]]["stock"] -= item["quantity"]

    # Generate receipt
    receipt_lines = []
    receipt_lines.append(f"Order Receipt - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    receipt_lines.append(f"Customer: {customer.get('name', 'Unknown')} (ID: {customer['id']})")
    receipt_lines.append("-" * 50)
    for item in order["items"]:
        product = inventory[item["sku"]]
        line_total = product["price"] * item["quantity"]
        receipt_lines.append(f"  {product['name']} x{item['quantity']} = ${line_total:.2f}")
    receipt_lines.append("-" * 50)
    receipt_lines.append(f"  Subtotal: ${subtotal:.2f}")
    if discount > 0:
        receipt_lines.append(f"  Discount: -${discount:.2f}")
    receipt_lines.append(f"  Tax: ${tax:.2f}")
    receipt_lines.append(f"  Shipping: ${shipping_cost:.2f}")
    receipt_lines.append(f"  Total: ${total:.2f}")
    receipt_text = "\n".join(receipt_lines)

    # Create order record
    order_record = {
        "order_id": f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "customer_id": customer["id"],
        "items": order["items"],
        "subtotal": round(subtotal, 2),
        "discount": round(discount, 2),
        "tax": round(tax, 2),
        "shipping": round(shipping_cost, 2),
        "total": round(total, 2),
        "status": "processed",
        "timestamp": datetime.now().isoformat(),
        "receipt": receipt_text,
    }

    # Audit log
    audit_entry = {
        "action": "order_processed",
        "order_id": order_record["order_id"],
        "customer_id": customer["id"],
        "total": order_record["total"],
        "timestamp": datetime.now().isoformat(),
    }

    return {
        "order": order_record,
        "audit": audit_entry,
    }
