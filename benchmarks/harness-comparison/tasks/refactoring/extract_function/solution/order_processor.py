from datetime import datetime


def validate_order(order, customer, inventory):
    if not order or "items" not in order:
        raise ValueError("Order must contain items")
    if not customer or "id" not in customer:
        raise ValueError("Customer must have an id")
    if not isinstance(order["items"], list) or len(order["items"]) == 0:
        raise ValueError("Order must have at least one item")
    for item in order["items"]:
        if "sku" not in item or "quantity" not in item:
            raise ValueError("Each item must have sku and quantity")
        if item["quantity"] <= 0:
            raise ValueError("Item quantity must be positive")
        if item["sku"] not in inventory:
            raise ValueError(f"Unknown SKU: {item['sku']}")
        if inventory[item["sku"]]["stock"] < item["quantity"]:
            raise ValueError(f"Insufficient stock for {item['sku']}")


def calculate_subtotal(order, inventory):
    return sum(inventory[item["sku"]]["price"] * item["quantity"] for item in order["items"])


def calculate_discount(subtotal, customer, order):
    tier_rates = {"gold": 0.15, "silver": 0.10, "bronze": 0.05}
    discount = subtotal * tier_rates.get(customer.get("tier"), 0)
    if order.get("coupon") == "SAVE10":
        discount += subtotal * 0.10
    return discount


def calculate_tax(discounted_subtotal, customer, config):
    if customer.get("tax_exempt"):
        return 0
    return discounted_subtotal * config.get("tax_rate", 0.08)


def calculate_shipping(order, inventory, customer, discounted_subtotal):
    total_weight = sum(
        inventory[item["sku"]].get("weight", 1) * item["quantity"]
        for item in order["items"]
    )
    if total_weight < 5:
        cost = 5.99
    elif total_weight < 20:
        cost = 12.99
    elif total_weight < 50:
        cost = 24.99
    else:
        cost = 49.99
    if customer.get("tier") == "gold" and discounted_subtotal > 100:
        cost = 0
    return cost


def update_inventory(order, inventory):
    for item in order["items"]:
        inventory[item["sku"]]["stock"] -= item["quantity"]


def generate_receipt(order, customer, inventory, subtotal, discount, tax, shipping, total):
    lines = [
        f"Order Receipt - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Customer: {customer.get('name', 'Unknown')} (ID: {customer['id']})",
        "-" * 50,
    ]
    for item in order["items"]:
        product = inventory[item["sku"]]
        lines.append(f"  {product['name']} x{item['quantity']} = ${product['price'] * item['quantity']:.2f}")
    lines.extend(["-" * 50, f"  Subtotal: ${subtotal:.2f}"])
    if discount > 0:
        lines.append(f"  Discount: -${discount:.2f}")
    lines.extend([f"  Tax: ${tax:.2f}", f"  Shipping: ${shipping:.2f}", f"  Total: ${total:.2f}"])
    return "\n".join(lines)


def create_order_record(order, customer, subtotal, discount, tax, shipping, total, receipt):
    return {
        "order_id": f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "customer_id": customer["id"],
        "items": order["items"],
        "subtotal": round(subtotal, 2),
        "discount": round(discount, 2),
        "tax": round(tax, 2),
        "shipping": round(shipping, 2),
        "total": round(total, 2),
        "status": "processed",
        "timestamp": datetime.now().isoformat(),
        "receipt": receipt,
    }


def create_audit_log(order_record, customer):
    return {
        "action": "order_processed",
        "order_id": order_record["order_id"],
        "customer_id": customer["id"],
        "total": order_record["total"],
        "timestamp": datetime.now().isoformat(),
    }


def process_order(order, customer, inventory, config):
    validate_order(order, customer, inventory)

    subtotal = calculate_subtotal(order, inventory)
    discount = calculate_discount(subtotal, customer, order)
    discounted_subtotal = subtotal - discount
    tax = calculate_tax(discounted_subtotal, customer, config)
    shipping = calculate_shipping(order, inventory, customer, discounted_subtotal)
    total = discounted_subtotal + tax + shipping

    update_inventory(order, inventory)
    receipt = generate_receipt(order, customer, inventory, subtotal, discount, tax, shipping, total)
    order_record = create_order_record(order, customer, subtotal, discount, tax, shipping, total, receipt)
    audit = create_audit_log(order_record, customer)

    return {"order": order_record, "audit": audit}
