SELECT
    c.id AS customer_id,
    c.name AS customer_name,
    SUM(oi.quantity * oi.unit_price) AS total_amount,
    COUNT(DISTINCT o.id) AS order_count,
    SUM(oi.quantity * oi.unit_price) / COUNT(DISTINCT o.id) AS avg_order_value,
    MAX(o.order_date) AS last_order_date
FROM customers c
JOIN orders o ON o.customer_id = c.id
JOIN order_items oi ON oi.order_id = o.id
WHERE o.status = 'completed'
  AND o.order_date >= date(
      (SELECT MAX(order_date) FROM orders WHERE status = 'completed'),
      '-12 months'
  )
GROUP BY c.id, c.name
HAVING COUNT(DISTINCT o.id) >= 2
ORDER BY total_amount DESC
LIMIT 10;
