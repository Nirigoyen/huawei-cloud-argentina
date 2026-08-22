\c scenario
-- Sample e-commerce scenario for the workshop.
BEGIN;

CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    city VARCHAR(100),
    signup_date DATE
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    price DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    order_date DATE NOT NULL,
    status VARCHAR(32) NOT NULL
);

CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL,
    unit_price DOUBLE PRECISION NOT NULL
);

INSERT INTO customers VALUES
  (1, 'Ada Lovelace',   'ada@example.com',   'London',    '2024-01-15'),
  (2, 'Alan Turing',    'alan@example.com',  'London',    '2024-02-20'),
  (3, 'Grace Hopper',   'grace@example.com', 'New York',  '2024-03-10'),
  (4, 'Linus Torvalds', 'linus@example.com', 'Helsinki',  '2024-04-01'),
  (5, 'Margaret Hamilton', 'margaret@example.com', 'Boston', '2024-05-22');

INSERT INTO products VALUES
  (1, 'Mechanical Keyboard', 'Electronics', 120.00),
  (2, 'Wireless Mouse',      'Electronics', 35.50),
  (3, '4K Monitor',          'Electronics', 320.00),
  (4, 'Notebook',            'Stationery',  12.00),
  (5, 'Coffee Mug',          'Kitchen',     8.50),
  (6, 'Desk Lamp',           'Furniture',  45.00);

INSERT INTO orders VALUES
  (1, 1, '2024-06-01', 'completed'),
  (2, 1, '2024-06-15', 'completed'),
  (3, 2, '2024-07-02', 'completed'),
  (4, 3, '2024-07-10', 'pending'),
  (5, 3, '2024-08-01', 'completed'),
  (6, 4, '2024-08-05', 'completed'),
  (7, 5, '2024-09-12', 'cancelled'),
  (8, 2, '2024-09-20', 'completed');

INSERT INTO order_items VALUES
  (1, 1, 1, 1, 120.00),
  (2, 1, 2, 2, 35.50),
  (3, 2, 3, 1, 320.00),
  (4, 3, 4, 3, 12.00),
  (5, 3, 5, 2, 8.50),
  (6, 4, 6, 1, 45.00),
  (7, 5, 1, 1, 120.00),
  (8, 5, 3, 1, 320.00),
  (9, 6, 2, 2, 35.50),
  (10, 6, 4, 5, 12.00),
  (11, 8, 6, 1, 45.00),
  (12, 8, 5, 3, 8.50);

COMMIT;
