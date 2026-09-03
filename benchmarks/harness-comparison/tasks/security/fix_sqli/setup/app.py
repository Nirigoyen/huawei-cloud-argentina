import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)


def get_db():
    conn = sqlite3.connect("test.db")
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            role TEXT DEFAULT 'user'
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            category TEXT NOT NULL
        )
    """)
    conn.execute("INSERT OR IGNORE INTO users (username, email, role) VALUES ('admin', 'admin@test.com', 'admin')")
    conn.execute("INSERT OR IGNORE INTO users (username, email, role) VALUES ('alice', 'alice@test.com', 'user')")
    conn.execute("INSERT OR IGNORE INTO products (name, price, category) VALUES ('Widget', 9.99, 'gadgets')")
    conn.execute("INSERT OR IGNORE INTO products (name, price, category) VALUES ('Gadget', 19.99, 'gadgets')")
    conn.commit()
    conn.close()


@app.route("/users/<username>")
def get_user(username):
    conn = get_db()
    cursor = conn.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return jsonify({"id": user[0], "username": user[1], "email": user[2], "role": user[3]})
    return jsonify({"error": "User not found"}), 404


@app.route("/users/search")
def search_users():
    role = request.args.get("role", "")
    conn = get_db()
    cursor = conn.execute("SELECT * FROM users WHERE role = ?", (role,))
    users = cursor.fetchall()
    conn.close()
    return jsonify([{"id": u[0], "username": u[1], "email": u[2], "role": u[3]} for u in users])


@app.route("/products")
def get_products():
    category = request.args.get("category", "")
    conn = get_db()
    if category:
        cursor = conn.execute("SELECT * FROM products WHERE category = ?", (category,))
    else:
        cursor = conn.execute("SELECT * FROM products")
    products = cursor.fetchall()
    conn.close()
    return jsonify([{"id": p[0], "name": p[1], "price": p[2], "category": p[3]} for p in products])


@app.route("/products/<int:product_id>")
def get_product(product_id):
    conn = get_db()
    cursor = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    conn.close()
    if product:
        return jsonify({"id": product[0], "name": product[1], "price": product[2], "category": product[3]})
    return jsonify({"error": "Product not found"}), 404


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
