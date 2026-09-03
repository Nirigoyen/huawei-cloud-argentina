"""
Monolithic e-commerce application.
All functionality in a single module.
"""


class ECommerceApp:
    def __init__(self):
        self.users = {}
        self.products = {}
        self.orders = {}
        self.payments = {}
        self.inventory = {}
        self.notifications = []

    # --- User Management ---
    def register_user(self, email, password, name):
        if email in self.users:
            raise ValueError("User already exists")
        self.users[email] = {"password": password, "name": name, "email": email}
        self._send_welcome_email(email, name)
        return email

    def authenticate_user(self, email, password):
        user = self.users.get(email)
        if user and user["password"] == password:
            return True
        return False

    def update_profile(self, email, name):
        self.users[email]["name"] = name

    # --- Product Catalog ---
    def add_product(self, sku, name, price, description, category):
        self.products[sku] = {
            "name": name, "price": price,
            "description": description, "category": category,
        }
        self.inventory[sku] = 0

    def get_product(self, sku):
        return self.products.get(sku)

    def list_products_by_category(self, category):
        return [p for p in self.products.values() if p["category"] == category]

    def search_products(self, query):
        return [p for p in self.products.values() if query.lower() in p["name"].lower()]

    # --- Inventory ---
    def update_inventory(self, sku, quantity):
        self.inventory[sku] = quantity

    def check_stock(self, sku):
        return self.inventory.get(sku, 0)

    def reserve_stock(self, sku, quantity):
        if self.inventory.get(sku, 0) >= quantity:
            self.inventory[sku] -= quantity
            return True
        return False

    # --- Order Management ---
    def create_order(self, user_email, items):
        order_id = f"order_{len(self.orders) + 1}"
        total = 0
        for sku, qty in items.items():
            if not self.reserve_stock(sku, qty):
                raise ValueError(f"Insufficient stock for {sku}")
            total += self.products[sku]["price"] * qty
        self.orders[order_id] = {
            "user": user_email, "items": items,
            "total": total, "status": "pending",
        }
        self._process_payment(order_id, total, user_email)
        return order_id

    def get_order(self, order_id):
        return self.orders.get(order_id)

    def cancel_order(self, order_id):
        order = self.orders.get(order_id)
        if order and order["status"] != "cancelled":
            for sku, qty in order["items"].items():
                self.inventory[sku] = self.inventory.get(sku, 0) + qty
            order["status"] = "cancelled"
            self._send_notification(order["user"], f"Order {order_id} cancelled")

    # --- Payment Processing ---
    def _process_payment(self, order_id, amount, user_email):
        payment_id = f"pay_{len(self.payments) + 1}"
        self.payments[payment_id] = {
            "order_id": order_id, "amount": amount, "status": "completed",
        }
        self.orders[order_id]["status"] = "paid"
        self._send_notification(user_email, f"Payment of ${amount} processed for {order_id}")

    def refund_payment(self, payment_id):
        payment = self.payments.get(payment_id)
        if payment and payment["status"] == "completed":
            payment["status"] = "refunded"
            order = self.orders[payment["order_id"]]
            self.cancel_order(payment["order_id"])
            self._send_notification(order["user"], f"Refund processed for {payment_id}")

    # --- Notifications ---
    def _send_welcome_email(self, email, name):
        self.notifications.append({"to": email, "subject": "Welcome!", "body": f"Hello {name}"})

    def _send_notification(self, email, message):
        self.notifications.append({"to": email, "subject": "Notification", "body": message})

    def get_notifications(self, email):
        return [n for n in self.notifications if n["to"] == email]
