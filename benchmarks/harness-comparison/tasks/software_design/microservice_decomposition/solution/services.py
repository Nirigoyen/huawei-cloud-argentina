from dataclasses import dataclass, field


@dataclass
class Service:
    name: str
    responsibility: str
    database: str
    endpoints: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)


services = [
    Service(
        name="user-service",
        responsibility="User registration, authentication, profile management",
        database="users_db",
        endpoints=["POST /register", "POST /login", "PUT /profile", "GET /profile"],
        dependencies=["notification-service"],
    ),
    Service(
        name="product-service",
        responsibility="Product catalog, search, category management",
        database="products_db",
        endpoints=["POST /products", "GET /products/{sku}", "GET /products", "GET /products/search"],
        dependencies=[],
    ),
    Service(
        name="inventory-service",
        responsibility="Stock management, reservation, availability checks",
        database="inventory_db",
        endpoints=["PUT /inventory/{sku}", "GET /inventory/{sku}", "POST /inventory/reserve"],
        dependencies=[],
    ),
    Service(
        name="order-service",
        responsibility="Order creation, tracking, cancellation",
        database="orders_db",
        endpoints=["POST /orders", "GET /orders/{id}", "POST /orders/{id}/cancel"],
        dependencies=["inventory-service", "payment-service", "notification-service"],
    ),
    Service(
        name="payment-service",
        responsibility="Payment processing, refunds",
        database="payments_db",
        endpoints=["POST /payments", "POST /payments/{id}/refund"],
        dependencies=["order-service", "notification-service"],
    ),
    Service(
        name="notification-service",
        responsibility="Email and push notifications",
        database="notifications_db",
        endpoints=["POST /notifications", "GET /notifications/{email}"],
        dependencies=[],
    ),
]
