"""
Seed script for an e-commerce domain database.
Generates realistic synthetic data:
  - customers, products, categories, orders, order_items, reviews, suppliers

Run: uv run python scripts/seed_db.py
"""

import random
import string
from datetime import datetime, timedelta
from decimal import Decimal

import psycopg2
from faker import Faker

# ── Connection ──────────────────────────────────────────────────────────────
DB_URL = "postgresql://querymind:querymind@localhost:5432/querymind"

DDL = """
-- E-commerce Domain Schema

CREATE TABLE IF NOT EXISTS suppliers (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(128) NOT NULL,
    country     VARCHAR(64),
    email       VARCHAR(128),
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS categories (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(64) NOT NULL UNIQUE,
    parent_id   INT REFERENCES categories(id)
);

CREATE TABLE IF NOT EXISTS products (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(256) NOT NULL,
    sku             VARCHAR(64) UNIQUE NOT NULL,
    category_id     INT REFERENCES categories(id),
    supplier_id     INT REFERENCES suppliers(id),
    unit_price      NUMERIC(10,2) NOT NULL,
    stock_quantity  INT DEFAULT 0,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS customers (
    id          SERIAL PRIMARY KEY,
    first_name  VARCHAR(64) NOT NULL,
    last_name   VARCHAR(64) NOT NULL,
    email       VARCHAR(128) UNIQUE NOT NULL,
    country     VARCHAR(64),
    segment     VARCHAR(32) DEFAULT 'standard',  -- standard | premium | enterprise
    joined_at   TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS orders (
    id              SERIAL PRIMARY KEY,
    customer_id     INT NOT NULL REFERENCES customers(id),
    status          VARCHAR(32) DEFAULT 'pending',  -- pending | shipped | delivered | cancelled
    total_amount    NUMERIC(12,2) NOT NULL,
    discount_amount NUMERIC(10,2) DEFAULT 0,
    created_at      TIMESTAMP DEFAULT NOW(),
    shipped_at      TIMESTAMP,
    delivered_at    TIMESTAMP
);

CREATE TABLE IF NOT EXISTS order_items (
    id          SERIAL PRIMARY KEY,
    order_id    INT NOT NULL REFERENCES orders(id),
    product_id  INT NOT NULL REFERENCES products(id),
    quantity    INT NOT NULL,
    unit_price  NUMERIC(10,2) NOT NULL,
    line_total  NUMERIC(12,2) GENERATED ALWAYS AS (quantity * unit_price) STORED
);

CREATE TABLE IF NOT EXISTS reviews (
    id          SERIAL PRIMARY KEY,
    product_id  INT NOT NULL REFERENCES products(id),
    customer_id INT NOT NULL REFERENCES customers(id),
    rating      SMALLINT CHECK (rating BETWEEN 1 AND 5),
    body        TEXT,
    created_at  TIMESTAMP DEFAULT NOW()
);
"""

GUARDRAIL_DEFAULTS = [
    ("allow_select", "true", "Allow SELECT queries"),
    ("allow_insert", "false", "Allow INSERT queries"),
    ("allow_update", "false", "Allow UPDATE queries"),
    ("allow_delete", "false", "Allow DELETE queries"),
    ("max_rows", "500", "Maximum rows returned per query"),
    ("restrict_to_schema", "public", "Restrict queries to this schema"),
]

MODEL_CONFIG_DEFAULTS = [
    ("model", "gpt-4o", "OpenAI model to use"),
    ("temperature", "0.0", "LLM temperature"),
    ("max_tokens", "1000", "Max tokens for SQL generation"),
    ("dialect", "postgresql", "SQL dialect"),
]


def seed(conn):
    fake = Faker()
    cur = conn.cursor()

    cur.execute(DDL)

    # Guardrails
    for key, value, desc in GUARDRAIL_DEFAULTS:
        cur.execute(
            "INSERT INTO guardrail_config (key, value, description, updated_at) VALUES (%s, %s, %s, NOW()) ON CONFLICT DO NOTHING",
            (key, value, desc),
        )

    # Model config
    for key, value, desc in MODEL_CONFIG_DEFAULTS:
        cur.execute(
            "INSERT INTO model_config (key, value, description, updated_at) VALUES (%s, %s, %s, NOW()) ON CONFLICT DO NOTHING",
            (key, value, desc),
        )

    # Suppliers (20)
    supplier_ids = []
    for _ in range(20):
        cur.execute(
            "INSERT INTO suppliers (name, country, email) VALUES (%s, %s, %s) RETURNING id",
            (fake.company(), fake.country(), fake.company_email()),
        )
        supplier_ids.append(cur.fetchone()[0])

    # Categories
    top_cats = ["Electronics", "Clothing", "Home & Garden", "Sports", "Books", "Toys", "Food & Beverage"]
    cat_ids = {}
    for cat in top_cats:
        cur.execute(
            "INSERT INTO categories (name) VALUES (%s) ON CONFLICT (name) DO UPDATE SET name=EXCLUDED.name RETURNING id",
            (cat,),
        )
        cat_ids[cat] = cur.fetchone()[0]

    # Products (500)
    product_ids = []
    for i in range(500):
        cat = random.choice(list(cat_ids.values()))
        sku = "SKU-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
        price = round(random.uniform(4.99, 999.99), 2)
        stock = random.randint(0, 500)
        cur.execute(
            """INSERT INTO products (name, sku, category_id, supplier_id, unit_price, stock_quantity, is_active)
               VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id""",
            (fake.catch_phrase(), sku, cat, random.choice(supplier_ids), price, stock, random.random() > 0.05),
        )
        product_ids.append(cur.fetchone()[0])

    # Customers (1000)
    customer_ids = []
    segments = ["standard"] * 70 + ["premium"] * 20 + ["enterprise"] * 10
    for _ in range(1000):
        cur.execute(
            """INSERT INTO customers (first_name, last_name, email, country, segment, joined_at)
               VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
            (
                fake.first_name(), fake.last_name(),
                fake.unique.email(), fake.country(),
                random.choice(segments),
                fake.date_time_between(start_date="-3y", end_date="now"),
            ),
        )
        customer_ids.append(cur.fetchone()[0])

    # Orders (3000) + order_items
    statuses = ["delivered"] * 60 + ["shipped"] * 20 + ["pending"] * 15 + ["cancelled"] * 5
    for _ in range(3000):
        customer_id = random.choice(customer_ids)
        status = random.choice(statuses)
        created = fake.date_time_between(start_date="-2y", end_date="now")
        shipped = created + timedelta(days=random.randint(1, 5)) if status in ("shipped", "delivered") else None
        delivered = shipped + timedelta(days=random.randint(1, 10)) if status == "delivered" else None
        discount = round(random.uniform(0, 50), 2) if random.random() > 0.7 else 0

        # Placeholder total — we'll update after inserting items
        cur.execute(
            """INSERT INTO orders (customer_id, status, total_amount, discount_amount, created_at, shipped_at, delivered_at)
               VALUES (%s, %s, 0, %s, %s, %s, %s) RETURNING id""",
            (customer_id, status, discount, created, shipped, delivered),
        )
        order_id = cur.fetchone()[0]

        total = Decimal("0")
        n_items = random.randint(1, 6)
        for _ in range(n_items):
            product_id = random.choice(product_ids)
            cur.execute("SELECT unit_price FROM products WHERE id = %s", (product_id,))
            unit_price = cur.fetchone()[0]
            quantity = random.randint(1, 5)
            cur.execute(
                "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (%s, %s, %s, %s)",
                (order_id, product_id, quantity, unit_price),
            )
            total += Decimal(str(unit_price)) * quantity

        cur.execute(
            "UPDATE orders SET total_amount = %s WHERE id = %s",
            (float(total) - discount, order_id),
        )

    # Reviews (2000)
    for _ in range(2000):
        cur.execute(
            """INSERT INTO reviews (product_id, customer_id, rating, body, created_at)
               VALUES (%s, %s, %s, %s, %s)""",
            (
                random.choice(product_ids),
                random.choice(customer_ids),
                random.randint(1, 5),
                fake.sentence(nb_words=20),
                fake.date_time_between(start_date="-2y", end_date="now"),
            ),
        )

    conn.commit()
    cur.close()
    print("✅ Seed complete.")
    print(f"   Suppliers: 20 | Categories: {len(top_cats)} | Products: 500")
    print(f"   Customers: 1000 | Orders: 3000 | Reviews: 2000")


if __name__ == "__main__":
    conn = psycopg2.connect(DB_URL)
    try:
        seed(conn)
    finally:
        conn.close()
