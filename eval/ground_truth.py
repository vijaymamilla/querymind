"""
Ground-truth dataset for QueryMind evaluation.
25 queries covering all four query types against the e-commerce schema.

Each entry has:
  question   – natural language question
  expected_sql – canonical SQL (used for exact-match scoring)
  query_type  – SELECT_SIMPLE | SELECT_AGGREGATE | SELECT_JOIN | SELECT_TEMPORAL
  description – what this test validates
"""

GROUND_TRUTH = [
    # ── SELECT_SIMPLE (6) ────────────────────────────────────────────────────
    {
        "id": 1,
        "question": "List all customers",
        "expected_sql": "SELECT * FROM customers LIMIT 100",
        "query_type": "SELECT_SIMPLE",
        "description": "Full table scan with limit",
    },
    {
        "id": 2,
        "question": "Show all product categories",
        "expected_sql": "SELECT id, name, description FROM categories ORDER BY name",
        "query_type": "SELECT_SIMPLE",
        "description": "Simple projection from categories",
    },
    {
        "id": 3,
        "question": "List all pending orders",
        "expected_sql": "SELECT id, customer_id, total_amount, created_at FROM orders WHERE status = 'pending' ORDER BY created_at DESC",
        "query_type": "SELECT_SIMPLE",
        "description": "Filtered select on status column",
    },
    {
        "id": 4,
        "question": "Show products that are out of stock",
        "expected_sql": "SELECT id, name, price FROM products WHERE stock_quantity = 0",
        "query_type": "SELECT_SIMPLE",
        "description": "Filter on numeric zero value",
    },
    {
        "id": 5,
        "question": "Find customers from the United States",
        "expected_sql": "SELECT id, first_name, last_name, email FROM customers WHERE country = 'United States'",
        "query_type": "SELECT_SIMPLE",
        "description": "String equality filter",
    },
    {
        "id": 6,
        "question": "List all suppliers",
        "expected_sql": "SELECT id, name, contact_email, country FROM suppliers ORDER BY name",
        "query_type": "SELECT_SIMPLE",
        "description": "Simple listing from suppliers table",
    },

    # ── SELECT_AGGREGATE (7) ─────────────────────────────────────────────────
    {
        "id": 7,
        "question": "How many customers do we have?",
        "expected_sql": "SELECT COUNT(*) AS total_customers FROM customers",
        "query_type": "SELECT_AGGREGATE",
        "description": "Simple COUNT(*)",
    },
    {
        "id": 8,
        "question": "What is the total revenue from delivered orders?",
        "expected_sql": "SELECT SUM(total_amount) AS total_revenue FROM orders WHERE status = 'delivered'",
        "query_type": "SELECT_AGGREGATE",
        "description": "SUM with WHERE filter",
    },
    {
        "id": 9,
        "question": "What is the average order value?",
        "expected_sql": "SELECT AVG(total_amount) AS avg_order_value FROM orders",
        "query_type": "SELECT_AGGREGATE",
        "description": "Simple AVG aggregate",
    },
    {
        "id": 10,
        "question": "How many orders are there per status?",
        "expected_sql": "SELECT status, COUNT(*) AS order_count FROM orders GROUP BY status ORDER BY order_count DESC",
        "query_type": "SELECT_AGGREGATE",
        "description": "GROUP BY with COUNT",
    },
    {
        "id": 11,
        "question": "What is the most expensive product?",
        "expected_sql": "SELECT name, price FROM products ORDER BY price DESC LIMIT 1",
        "query_type": "SELECT_AGGREGATE",
        "description": "MAX via ORDER BY + LIMIT",
    },
    {
        "id": 12,
        "question": "What is the average product rating?",
        "expected_sql": "SELECT AVG(rating) AS avg_rating FROM reviews",
        "query_type": "SELECT_AGGREGATE",
        "description": "AVG on reviews table",
    },
    {
        "id": 13,
        "question": "How many products does each category have?",
        "expected_sql": "SELECT category_id, COUNT(*) AS product_count FROM products GROUP BY category_id ORDER BY product_count DESC",
        "query_type": "SELECT_AGGREGATE",
        "description": "GROUP BY with COUNT on products",
    },

    # ── SELECT_JOIN (7) ──────────────────────────────────────────────────────
    {
        "id": 14,
        "question": "Show all orders with customer names",
        "expected_sql": (
            "SELECT o.id AS order_id, c.first_name, c.last_name, o.total_amount, o.status "
            "FROM orders o "
            "JOIN customers c ON o.customer_id = c.id "
            "ORDER BY o.created_at DESC"
        ),
        "query_type": "SELECT_JOIN",
        "description": "Two-table join: orders + customers",
    },
    {
        "id": 15,
        "question": "List products with their category names",
        "expected_sql": (
            "SELECT p.name AS product_name, p.price, c.name AS category_name "
            "FROM products p "
            "JOIN categories c ON p.category_id = c.id "
            "ORDER BY c.name, p.name"
        ),
        "query_type": "SELECT_JOIN",
        "description": "Two-table join: products + categories",
    },
    {
        "id": 16,
        "question": "Show order details with product names",
        "expected_sql": (
            "SELECT o.id AS order_id, p.name AS product_name, oi.quantity, oi.unit_price "
            "FROM orders o "
            "JOIN order_items oi ON o.id = oi.order_id "
            "JOIN products p ON oi.product_id = p.id "
            "ORDER BY o.id"
        ),
        "query_type": "SELECT_JOIN",
        "description": "Three-table join: orders + order_items + products",
    },
    {
        "id": 17,
        "question": "List top 5 customers by total amount spent",
        "expected_sql": (
            "SELECT c.first_name, c.last_name, SUM(o.total_amount) AS total_spent "
            "FROM customers c "
            "JOIN orders o ON c.id = o.customer_id "
            "GROUP BY c.id, c.first_name, c.last_name "
            "ORDER BY total_spent DESC "
            "LIMIT 5"
        ),
        "query_type": "SELECT_JOIN",
        "description": "JOIN with GROUP BY, ORDER BY, LIMIT",
    },
    {
        "id": 18,
        "question": "Show products with their supplier names",
        "expected_sql": (
            "SELECT p.name AS product_name, p.price, s.name AS supplier_name "
            "FROM products p "
            "JOIN suppliers s ON p.supplier_id = s.id "
            "ORDER BY s.name, p.name"
        ),
        "query_type": "SELECT_JOIN",
        "description": "Two-table join: products + suppliers",
    },
    {
        "id": 19,
        "question": "Show reviews with product names",
        "expected_sql": (
            "SELECT r.rating, r.comment, p.name AS product_name "
            "FROM reviews r "
            "JOIN products p ON r.product_id = p.id "
            "ORDER BY r.created_at DESC"
        ),
        "query_type": "SELECT_JOIN",
        "description": "Two-table join: reviews + products",
    },
    {
        "id": 20,
        "question": "Which products have been ordered more than 10 times?",
        "expected_sql": (
            "SELECT p.name, SUM(oi.quantity) AS total_ordered "
            "FROM products p "
            "JOIN order_items oi ON p.id = oi.product_id "
            "GROUP BY p.id, p.name "
            "HAVING SUM(oi.quantity) > 10 "
            "ORDER BY total_ordered DESC"
        ),
        "query_type": "SELECT_JOIN",
        "description": "JOIN with HAVING clause",
    },

    # ── SELECT_TEMPORAL (5) ──────────────────────────────────────────────────
    {
        "id": 21,
        "question": "How many orders were placed this year?",
        "expected_sql": (
            "SELECT COUNT(*) AS orders_this_year "
            "FROM orders "
            "WHERE EXTRACT(YEAR FROM created_at) = EXTRACT(YEAR FROM CURRENT_DATE)"
        ),
        "query_type": "SELECT_TEMPORAL",
        "description": "Current year filter with EXTRACT",
    },
    {
        "id": 22,
        "question": "Show orders placed in the last 30 days",
        "expected_sql": (
            "SELECT id, customer_id, total_amount, status, created_at "
            "FROM orders "
            "WHERE created_at >= CURRENT_DATE - INTERVAL '30 days' "
            "ORDER BY created_at DESC"
        ),
        "query_type": "SELECT_TEMPORAL",
        "description": "Rolling 30-day window with INTERVAL",
    },
    {
        "id": 23,
        "question": "Show monthly order counts for this year",
        "expected_sql": (
            "SELECT EXTRACT(MONTH FROM created_at) AS month, COUNT(*) AS order_count "
            "FROM orders "
            "WHERE EXTRACT(YEAR FROM created_at) = EXTRACT(YEAR FROM CURRENT_DATE) "
            "GROUP BY month "
            "ORDER BY month"
        ),
        "query_type": "SELECT_TEMPORAL",
        "description": "Monthly breakdown using EXTRACT + GROUP BY",
    },
    {
        "id": 24,
        "question": "Show all orders placed in 2023",
        "expected_sql": (
            "SELECT id, customer_id, total_amount, status "
            "FROM orders "
            "WHERE EXTRACT(YEAR FROM created_at) = 2023 "
            "ORDER BY created_at DESC"
        ),
        "query_type": "SELECT_TEMPORAL",
        "description": "Specific year filter",
    },
    {
        "id": 25,
        "question": "How many customers registered each year?",
        "expected_sql": (
            "SELECT EXTRACT(YEAR FROM created_at) AS year, COUNT(*) AS new_customers "
            "FROM customers "
            "GROUP BY year "
            "ORDER BY year"
        ),
        "query_type": "SELECT_TEMPORAL",
        "description": "Year-over-year customer growth",
    },
]
