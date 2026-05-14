#!/usr/bin/env python3
"""
Seed 30 few-shot examples into QueryMind via the Admin API.
Covers all four query types required by the capstone rubric:
  - SELECT_SIMPLE   (8 examples)
  - SELECT_AGGREGATE (8 examples)
  - SELECT_JOIN      (8 examples)
  - SELECT_TEMPORAL  (6 examples)

Usage:
    python scripts/seed_examples.py [--base-url http://localhost:8000]
"""

import argparse
import sys
import time
import requests

# ──────────────────────────────────────────────────────────────────────────────
# 30 high-quality few-shot examples for the e-commerce schema
# Tables: customers, orders, order_items, products, categories, reviews, suppliers
# ──────────────────────────────────────────────────────────────────────────────
EXAMPLES = [
    # ── SELECT_SIMPLE (8) ────────────────────────────────────────────────────
    {
        "question": "Show all customers",
        "sql": "SELECT * FROM customers LIMIT 100;",
        "query_type": "SELECT_SIMPLE",
        "notes": "Basic full-table scan",
    },
    {
        "question": "List all products with their prices",
        "sql": "SELECT name, price FROM products ORDER BY price DESC;",
        "query_type": "SELECT_SIMPLE",
        "notes": "Simple projection with ordering",
    },
    {
        "question": "Show all product categories",
        "sql": "SELECT id, name, description FROM categories ORDER BY name;",
        "query_type": "SELECT_SIMPLE",
        "notes": "Simple select from categories",
    },
    {
        "question": "Get all orders with their status",
        "sql": "SELECT id, customer_id, status, total_amount FROM orders ORDER BY created_at DESC;",
        "query_type": "SELECT_SIMPLE",
        "notes": "Simple order listing",
    },
    {
        "question": "List all suppliers",
        "sql": "SELECT id, name, contact_email, country FROM suppliers ORDER BY name;",
        "query_type": "SELECT_SIMPLE",
        "notes": "Simple supplier listing",
    },
    {
        "question": "Find customers from the United States",
        "sql": "SELECT id, first_name, last_name, email FROM customers WHERE country = 'United States';",
        "query_type": "SELECT_SIMPLE",
        "notes": "Filtered select with country",
    },
    {
        "question": "Show products that are out of stock",
        "sql": "SELECT id, name, price FROM products WHERE stock_quantity = 0;",
        "query_type": "SELECT_SIMPLE",
        "notes": "Filter on stock_quantity",
    },
    {
        "question": "List all pending orders",
        "sql": "SELECT id, customer_id, total_amount, created_at FROM orders WHERE status = 'pending' ORDER BY created_at DESC;",
        "query_type": "SELECT_SIMPLE",
        "notes": "Filter orders by status",
    },

    # ── SELECT_AGGREGATE (8) ─────────────────────────────────────────────────
    {
        "question": "How many customers do we have?",
        "sql": "SELECT COUNT(*) AS total_customers FROM customers;",
        "query_type": "SELECT_AGGREGATE",
        "notes": "Basic COUNT",
    },
    {
        "question": "What is the total revenue from all orders?",
        "sql": "SELECT SUM(total_amount) AS total_revenue FROM orders WHERE status = 'delivered';",
        "query_type": "SELECT_AGGREGATE",
        "notes": "SUM aggregate on delivered orders",
    },
    {
        "question": "What is the average order value?",
        "sql": "SELECT AVG(total_amount) AS avg_order_value FROM orders;",
        "query_type": "SELECT_AGGREGATE",
        "notes": "AVG aggregate",
    },
    {
        "question": "How many orders are there per status?",
        "sql": "SELECT status, COUNT(*) AS order_count FROM orders GROUP BY status ORDER BY order_count DESC;",
        "query_type": "SELECT_AGGREGATE",
        "notes": "GROUP BY with COUNT",
    },
    {
        "question": "What is the most expensive product?",
        "sql": "SELECT name, price FROM products ORDER BY price DESC LIMIT 1;",
        "query_type": "SELECT_AGGREGATE",
        "notes": "MAX using ORDER BY + LIMIT",
    },
    {
        "question": "How many products does each category have?",
        "sql": "SELECT category_id, COUNT(*) AS product_count FROM products GROUP BY category_id ORDER BY product_count DESC;",
        "query_type": "SELECT_AGGREGATE",
        "notes": "GROUP BY category",
    },
    {
        "question": "What is the average product rating?",
        "sql": "SELECT AVG(rating) AS avg_rating FROM reviews;",
        "query_type": "SELECT_AGGREGATE",
        "notes": "AVG on reviews rating",
    },
    {
        "question": "What is the total number of items sold?",
        "sql": "SELECT SUM(quantity) AS total_items_sold FROM order_items;",
        "query_type": "SELECT_AGGREGATE",
        "notes": "SUM quantity from order_items",
    },

    # ── SELECT_JOIN (8) ──────────────────────────────────────────────────────
    {
        "question": "Show all orders with customer names",
        "sql": (
            "SELECT o.id AS order_id, c.first_name, c.last_name, o.total_amount, o.status "
            "FROM orders o "
            "JOIN customers c ON o.customer_id = c.id "
            "ORDER BY o.created_at DESC;"
        ),
        "query_type": "SELECT_JOIN",
        "notes": "orders JOIN customers",
    },
    {
        "question": "List products with their category names",
        "sql": (
            "SELECT p.name AS product_name, p.price, c.name AS category_name "
            "FROM products p "
            "JOIN categories c ON p.category_id = c.id "
            "ORDER BY c.name, p.name;"
        ),
        "query_type": "SELECT_JOIN",
        "notes": "products JOIN categories",
    },
    {
        "question": "Show order details including product names and quantities",
        "sql": (
            "SELECT o.id AS order_id, p.name AS product_name, oi.quantity, oi.unit_price "
            "FROM orders o "
            "JOIN order_items oi ON o.id = oi.order_id "
            "JOIN products p ON oi.product_id = p.id "
            "ORDER BY o.id;"
        ),
        "query_type": "SELECT_JOIN",
        "notes": "Three-table join: orders, order_items, products",
    },
    {
        "question": "Which customers have placed orders?",
        "sql": (
            "SELECT DISTINCT c.id, c.first_name, c.last_name, c.email "
            "FROM customers c "
            "JOIN orders o ON c.id = o.customer_id "
            "ORDER BY c.last_name;"
        ),
        "query_type": "SELECT_JOIN",
        "notes": "DISTINCT customers who have orders",
    },
    {
        "question": "Show reviews with product names and reviewer emails",
        "sql": (
            "SELECT r.rating, r.comment, p.name AS product_name, c.email AS reviewer_email "
            "FROM reviews r "
            "JOIN products p ON r.product_id = p.id "
            "JOIN customers c ON r.customer_id = c.id "
            "ORDER BY r.created_at DESC;"
        ),
        "query_type": "SELECT_JOIN",
        "notes": "reviews joined with products and customers",
    },
    {
        "question": "List the top 5 customers by total amount spent",
        "sql": (
            "SELECT c.first_name, c.last_name, SUM(o.total_amount) AS total_spent "
            "FROM customers c "
            "JOIN orders o ON c.id = o.customer_id "
            "GROUP BY c.id, c.first_name, c.last_name "
            "ORDER BY total_spent DESC "
            "LIMIT 5;"
        ),
        "query_type": "SELECT_JOIN",
        "notes": "JOIN with GROUP BY and ORDER BY",
    },
    {
        "question": "Show products with their supplier names",
        "sql": (
            "SELECT p.name AS product_name, p.price, s.name AS supplier_name "
            "FROM products p "
            "JOIN suppliers s ON p.supplier_id = s.id "
            "ORDER BY s.name, p.name;"
        ),
        "query_type": "SELECT_JOIN",
        "notes": "products JOIN suppliers",
    },
    {
        "question": "Which products have been ordered more than 10 times?",
        "sql": (
            "SELECT p.name, SUM(oi.quantity) AS total_ordered "
            "FROM products p "
            "JOIN order_items oi ON p.id = oi.product_id "
            "GROUP BY p.id, p.name "
            "HAVING SUM(oi.quantity) > 10 "
            "ORDER BY total_ordered DESC;"
        ),
        "query_type": "SELECT_JOIN",
        "notes": "JOIN with HAVING clause",
    },

    # ── SELECT_TEMPORAL (6) ──────────────────────────────────────────────────
    {
        "question": "How many orders were placed this year?",
        "sql": (
            "SELECT COUNT(*) AS orders_this_year "
            "FROM orders "
            "WHERE EXTRACT(YEAR FROM created_at) = EXTRACT(YEAR FROM CURRENT_DATE);"
        ),
        "query_type": "SELECT_TEMPORAL",
        "notes": "Current year filter using EXTRACT",
    },
    {
        "question": "Show monthly order counts for the current year",
        "sql": (
            "SELECT EXTRACT(MONTH FROM created_at) AS month, COUNT(*) AS order_count "
            "FROM orders "
            "WHERE EXTRACT(YEAR FROM created_at) = EXTRACT(YEAR FROM CURRENT_DATE) "
            "GROUP BY month "
            "ORDER BY month;"
        ),
        "query_type": "SELECT_TEMPORAL",
        "notes": "Monthly breakdown using EXTRACT",
    },
    {
        "question": "What was the total revenue last month?",
        "sql": (
            "SELECT SUM(total_amount) AS revenue_last_month "
            "FROM orders "
            "WHERE status = 'delivered' "
            "AND EXTRACT(YEAR FROM created_at) = EXTRACT(YEAR FROM CURRENT_DATE - INTERVAL '1 month') "
            "AND EXTRACT(MONTH FROM created_at) = EXTRACT(MONTH FROM CURRENT_DATE - INTERVAL '1 month');"
        ),
        "query_type": "SELECT_TEMPORAL",
        "notes": "Last month revenue using INTERVAL",
    },
    {
        "question": "Show all orders placed in the last 30 days",
        "sql": (
            "SELECT id, customer_id, total_amount, status, created_at "
            "FROM orders "
            "WHERE created_at >= CURRENT_DATE - INTERVAL '30 days' "
            "ORDER BY created_at DESC;"
        ),
        "query_type": "SELECT_TEMPORAL",
        "notes": "Rolling 30-day window",
    },
    {
        "question": "How many customers registered each year?",
        "sql": (
            "SELECT EXTRACT(YEAR FROM created_at) AS year, COUNT(*) AS new_customers "
            "FROM customers "
            "GROUP BY year "
            "ORDER BY year;"
        ),
        "query_type": "SELECT_TEMPORAL",
        "notes": "Year-over-year customer growth",
    },
    {
        "question": "Show orders placed in 2023",
        "sql": (
            "SELECT id, customer_id, total_amount, status "
            "FROM orders "
            "WHERE EXTRACT(YEAR FROM created_at) = 2023 "
            "ORDER BY created_at DESC;"
        ),
        "query_type": "SELECT_TEMPORAL",
        "notes": "Specific year filter",
    },
]


def seed(base_url: str):
    url = f"{base_url}/admin/examples"
    print(f"Seeding {len(EXAMPLES)} examples to {url}\n")

    ok = 0
    fail = 0
    for i, ex in enumerate(EXAMPLES, 1):
        payload = {
            "question": ex["question"],
            "sql": ex["sql"],
            "query_type": ex["query_type"],
        }
        try:
            r = requests.post(url, json=payload, timeout=30)
            if r.status_code in (200, 201):
                print(f"  [{i:02d}] ✓  [{ex['query_type']}] {ex['question'][:60]}")
                ok += 1
            else:
                print(f"  [{i:02d}] ✗  [{ex['query_type']}] {ex['question'][:60]}")
                print(f"        Status {r.status_code}: {r.text[:120]}")
                fail += 1
        except requests.exceptions.ConnectionError:
            print(f"\n  ERROR: Cannot connect to {base_url}")
            print("  Make sure the backend is running: cd backend && uvicorn app.main:app --reload")
            sys.exit(1)
        time.sleep(0.3)  # small delay to avoid hammering OpenAI embeddings API

    print(f"\n{'─'*60}")
    print(f"Done: {ok} seeded, {fail} failed out of {len(EXAMPLES)} examples.")

    if ok > 0:
        print("\nSyncing embeddings to Qdrant...")
        r = requests.post(f"{base_url}/admin/examples/sync-embeddings", timeout=60)
        if r.status_code == 202:
            print("  ✓ Sync triggered successfully.")
        else:
            print(f"  ✗ Sync failed: {r.status_code} {r.text}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed 30 few-shot examples into QueryMind")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Backend API base URL (default: http://localhost:8000)",
    )
    args = parser.parse_args()
    seed(args.base_url)
