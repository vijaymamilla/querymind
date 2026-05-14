# QueryMind AI — Text-to-SQL Analytics Engine

> **Codebasics AI Engineering Bootcamp — Capstone Project (Assignment 3)**
>
> Natural language querying over a PostgreSQL e-commerce database, powered by a 7-stage pipeline, Qdrant vector search, and OpenAI GPT-4o.

---

## Demo

> 📹 _Demo video link: [https://youtu.be/L4pgpwKwABo]_
>
> 🔗 _GitHub: [https://github.com/vijaymamilla/querymind](https://github.com/vijaymamilla/querymind)_

---

## Approach

QueryMind converts natural language questions into SQL through a **7-stage modular pipeline**:

```
User Question
    ↓
[1] Classifier      — detects intent type (SELECT_SIMPLE / SELECT_AGGREGATE / SELECT_JOIN / SELECT_TEMPORAL / BLOCKED)
    ↓
[2] Schema Linker   — maps entities in the question to real table/column names
    ↓
[3] Retriever       — fetches top-4 similar Q→SQL examples from Qdrant (few-shot prompting)
    ↓
[4] Generator       — builds a prompt with schema + examples → calls GPT-4o → returns SQL
    ↓
[5] Validator       — syntax check (sqlglot AST) + schema validation + guardrail enforcement
    ↓
[6] Executor        — runs SQL against PostgreSQL; self-heals on error (retries with error injected back to LLM)
    ↓
[7] Formatter       — returns rows as structured JSON + natural-language summary
```

**Key design decisions:**
- **Few-shot retrieval via Qdrant** — semantically similar past examples improve SQL accuracy without fine-tuning
- **Guardrails at the validator layer** — configurable allow/deny for SELECT/INSERT/UPDATE/DELETE; never bypassed
- **Self-healing SQL** — on execution failure, the error message is fed back to GPT-4o for one retry
- **Docling document ingestion** — upload schema docs / data dictionaries; chunks are embedded and used as additional context
- **Admin panel** — full React UI to manage examples, schema annotations, guardrails, model config, and query logs

---

## Stack

| Layer | Tech |
|---|---|
| Backend | FastAPI, SQLAlchemy async, asyncpg |
| Package manager | `uv` + `pyproject.toml` |
| LLM | OpenAI `gpt-4o` / `gpt-4o-mini` (configurable) |
| Embeddings | OpenAI `text-embedding-3-small` (1536-dim) |
| Document parsing | Docling (PDF, DOCX, HTML, Markdown) |
| Vector database | Qdrant |
| Relational DB | PostgreSQL 16 |
| Frontend | Next.js 14, TypeScript, Tailwind CSS |

## Domain

**E-commerce** — 7 tables, 1 000+ synthetic rows each:
`customers`, `orders`, `order_items`, `products`, `categories`, `suppliers`, `reviews`

---

## Quick Start

### 1. Prerequisites
- Python 3.11+
- Node.js 20+
- [uv](https://github.com/astral-sh/uv) — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Docker Desktop (for Postgres + Qdrant)

### 2. Clone & configure
```bash
git clone https://github.com/vijaymamilla/querymind.git
cd querymind

cp backend/.env.example backend/.env
# Open backend/.env and set:
#   OPENAI_API_KEY=sk-...
#   DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/querymind
#   QDRANT_URL=http://localhost:6333
```

### 3. Start Postgres and Qdrant
```bash
docker compose up -d
```

### 4. Backend setup & seed
```bash
cd backend
uv sync

# Seed the database with synthetic e-commerce data + admin config
uv run python ../scripts/seed_db.py

# Seed 30 few-shot examples into Postgres + Qdrant
uv run python ../scripts/seed_examples.py
```

### 5. Run the backend
```bash
cd backend
uv run uvicorn app.main:app --reload --port 8000
```
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs

### 6. Frontend setup
```bash
cd frontend
npm install
npm run dev
```
- App: http://localhost:3000

---

## Project Structure

```
querymind/
├── backend/
│   ├── pyproject.toml           # uv/hatchling dependencies
│   ├── .env.example             # Environment variable template
│   ├── app/
│   │   ├── main.py              # FastAPI entry point + router mounts
│   │   ├── config.py            # Settings (pydantic-settings)
│   │   ├── db/session.py        # Async SQLAlchemy engine
│   │   ├── models/admin.py      # ORM models (admin tables)
│   │   ├── schemas/pipeline.py  # Pydantic I/O contracts for each stage
│   │   ├── pipeline/
│   │   │   ├── orchestrator.py  # Wires all 7 stages together
│   │   │   ├── classifier.py    # Stage 1: intent classification
│   │   │   ├── schema_linker.py # Stage 2: entity → schema mapping
│   │   │   ├── retriever.py     # Stage 3: Qdrant few-shot retrieval
│   │   │   ├── ingester.py      # Docling document parser + Qdrant indexer
│   │   │   ├── generator.py     # Stage 4: OpenAI SQL generation
│   │   │   ├── validator.py     # Stage 5: guardrails + syntax check
│   │   │   ├── executor.py      # Stage 6: safe SQL execution + self-heal
│   │   │   └── formatter.py     # Stage 7: JSON table + NL summary
│   │   └── admin/
│   │       ├── query_route.py   # POST /query
│   │       └── routes.py        # All admin panel CRUD routes
│   └── tests/
│       └── test_validator.py    # Guardrails & validator unit tests
├── frontend/
│   └── src/app/
│       ├── query/page.tsx        # Chat query interface
│       └── admin/
│           ├── schema/           # Schema Manager UI
│           ├── examples/         # Examples Manager UI
│           ├── logs/             # Query Logs UI
│           ├── guardrails/       # Guardrails Config UI
│           └── config/           # Model Config UI
├── scripts/
│   ├── seed_db.py               # Generates synthetic e-commerce data
│   └── seed_examples.py         # Seeds 30 few-shot examples via API
├── eval/
│   ├── ground_truth.py          # 25 ground-truth Q+SQL pairs
│   ├── run_eval.py              # Evaluation harness (exec accuracy + exact match)
│   └── report.json              # Latest evaluation report (generated)
└── docker-compose.yml           # Postgres 16 + Qdrant
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/query` | Natural language → SQL → result |
| GET | `/admin/schema/introspect` | Live schema from DB |
| GET/POST/PATCH/DELETE | `/admin/schema/columns` | Column descriptions & synonyms |
| GET/POST/PATCH/DELETE | `/admin/examples` | Few-shot examples CRUD |
| POST | `/admin/examples/sync-embeddings` | Re-index all examples into Qdrant |
| GET | `/admin/logs` | Query audit log with pagination |
| GET/PATCH | `/admin/guardrails` | Guardrail toggles (allow_select, allow_insert, etc.) |
| GET/PATCH | `/admin/config` | Model configuration (dialect, model, temperature) |
| POST | `/admin/documents/upload` | Upload and index a document via Docling |
| DELETE | `/admin/documents/{doc_name}` | Remove a document's chunks from Qdrant |
| GET | `/admin/documents/search?q=` | Semantic search over indexed documents |

---

## Vector Collections (Qdrant)

| Collection | Purpose | Indexed by |
|---|---|---|
| `few_shot_examples` | Question → SQL pairs for few-shot prompting | `retriever.py` |
| `schema_docs` | Parsed chunks from uploaded schema/data-dictionary docs | `ingester.py` |

Both collections use OpenAI `text-embedding-3-small` (1536 dimensions, cosine similarity).

---

## Guardrails

Configurable at runtime via the Admin UI or `PATCH /admin/guardrails`:

| Key | Default | Description |
|---|---|---|
| `allow_select` | `true` | Allow SELECT queries |
| `allow_insert` | `false` | Allow INSERT queries |
| `allow_update` | `false` | Allow UPDATE queries |
| `allow_delete` | `false` | Allow DELETE queries |
| `max_rows` | `500` | Maximum rows returned per query |

---

## Evaluation

Run the evaluation harness against the live API:

```bash
# Backend must be running on localhost:8000
cd querymind
python eval/run_eval.py --output eval/report.json
```

**Latest results** (25 queries, 4 query types):

| Metric | Score |
|---|---|
| Execution Accuracy | **100%** (25/25) |
| Exact Match Rate | **8%** (2/25) |

> **Note on Exact Match:** The low exact match rate is expected — the pipeline appends `LIMIT 500` (the configured `max_rows` guardrail) to all queries for safety, which differs from the bare ground-truth SQL. All 25 queries executed correctly and returned the right results.

Breakdown by query type:

| Type | Count | Exec Accuracy | Exact Match |
|---|---|---|---|
| SELECT_SIMPLE | 6 | 100% | 16.7% |
| SELECT_AGGREGATE | 7 | 100% | 0% |
| SELECT_JOIN | 7 | 100% | 14.3% |
| SELECT_TEMPORAL | 5 | 100% | 0% |

---

## Few-Shot Examples

Seed 30 curated examples covering all query types:

```bash
python scripts/seed_examples.py
```

Manage examples via the Admin UI at http://localhost:3000/admin/examples or via the API.

---

## Document Ingestion (Docling)

Upload PDFs, DOCX, HTML, or Markdown files containing schema documentation or data dictionaries:

```bash
curl -X POST http://localhost:8000/admin/documents/upload \
  -F "file=@schema_docs.pdf"
```

Docling converts the document to structured markdown, which is chunked and indexed into the `schema_docs` Qdrant collection for context-aware SQL generation.

Supported formats: `.pdf`, `.docx`, `.html`, `.htm`, `.md`, `.txt`

---

## Running Tests

```bash
cd backend
uv run pytest tests/ -v
```

---

## Sample Queries to Try

```
How many customers do we have?
What is the total revenue from delivered orders?
Show all orders with customer names
List the top 5 customers by total amount spent
How many orders were placed this year?
Show monthly order counts for this year
Which products have been ordered more than 10 times?
What is the average product rating?
Show products that are out of stock
List all pending orders
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | _(required)_ | OpenAI API key |
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/querymind` | PostgreSQL connection string |
| `QDRANT_URL` | `http://localhost:6333` | Qdrant server URL |
| `QDRANT_API_KEY` | _(empty)_ | Qdrant API key (for cloud) |


## Evalution results

======================================================================
  QueryMind Evaluation Harness
  Target: http://localhost:8000
  Dataset: 25 queries
  Started: 2026-05-14 13:20:07
======================================================================

[01/25] [SELECT_SIMPLE] List all customers
         Exec: ✓  ExactMatch: ✓  Status: success  Latency: 3634ms
         SQL: SELECT * FROM customers LIMIT 100

[02/25] [SELECT_SIMPLE] Show all product categories
         Exec: ✓  ExactMatch: ~  Status: success  Latency: 2433ms
         SQL: SELECT id, name FROM categories ORDER BY name LIMIT 500

[03/25] [SELECT_SIMPLE] List all pending orders
         Exec: ✓  ExactMatch: ~  Status: success  Latency: 3489ms
         SQL: SELECT id, customer_id, total_amount, created_at FROM orders WHERE status = 'pen...

[04/25] [SELECT_SIMPLE] Show products that are out of stock
         Exec: ✓  ExactMatch: ~  Status: success  Latency: 3308ms
         SQL: SELECT id, name, unit_price FROM products WHERE stock_quantity = 0 LIMIT 100

[05/25] [SELECT_SIMPLE] Find customers from the United States
         Exec: ✓  ExactMatch: ~  Status: success  Latency: 2134ms
         SQL: SELECT id, first_name, last_name, email FROM customers WHERE country = 'United S...

[06/25] [SELECT_SIMPLE] List all suppliers
         Exec: ✓  ExactMatch: ~  Status: success  Latency: 3586ms
         SQL: SELECT id, name, country, email, created_at FROM suppliers ORDER BY name LIMIT 5...

[07/25] [SELECT_AGGREGATE] How many customers do we have?
         Exec: ✓  ExactMatch: ~  Status: success  Latency: 2675ms
         SQL: SELECT COUNT(*) AS total_customers FROM customers LIMIT 500

[08/25] [SELECT_AGGREGATE] What is the total revenue from delivered orders?
         Exec: ✓  ExactMatch: ~  Status: success  Latency: 2668ms
         SQL: SELECT SUM(total_amount) AS total_revenue FROM orders WHERE status = 'delivered'...

[09/25] [SELECT_AGGREGATE] What is the average order value?
         Exec: ✓  ExactMatch: ~  Status: success  Latency: 2883ms
         SQL: SELECT AVG(total_amount) AS avg_order_value FROM orders LIMIT 500

[10/25] [SELECT_AGGREGATE] How many orders are there per status?
         Exec: ✓  ExactMatch: ~  Status: success  Latency: 2660ms
         SQL: SELECT status, COUNT(*) AS order_count FROM orders GROUP BY status ORDER BY orde...

[11/25] [SELECT_AGGREGATE] What is the most expensive product?
         Exec: ✓  ExactMatch: ~  Status: success  Latency: 2565ms
         SQL: SELECT name, unit_price FROM products ORDER BY unit_price DESC LIMIT 1

[12/25] [SELECT_AGGREGATE] What is the average product rating?
         Exec: ✓  ExactMatch: ~  Status: success  Latency: 2666ms
         SQL: SELECT AVG(rating) AS avg_rating FROM reviews LIMIT 500

[13/25] [SELECT_AGGREGATE] How many products does each category have?
         Exec: ✓  ExactMatch: ~  Status: success  Latency: 3761ms
         SQL: SELECT category_id, COUNT(*) AS product_count FROM products GROUP BY category_id...

[14/25] [SELECT_JOIN] Show all orders with customer names
         Exec: ✓  ExactMatch: ~  Status: success  Latency: 5704ms
         SQL: SELECT o.id AS order_id, c.first_name, c.last_name, o.total_amount, o.status FRO...

[15/25] [SELECT_JOIN] List products with their category names
         Exec: ✓  ExactMatch: ~  Status: success  Latency: 3665ms
         SQL: SELECT p.name AS product_name, c.name AS category_name FROM products p JOIN cate...

[16/25] [SELECT_JOIN] Show order details with product names
         Exec: ✓  ExactMatch: ~  Status: success  Latency: 10285ms
         SQL: SELECT o.id AS order_id, p.name AS product_name, oi.quantity, oi.unit_price FROM...

[17/25] [SELECT_JOIN] List top 5 customers by total amount spent
         Exec: ✓  ExactMatch: ✓  Status: success  Latency: 3927ms
         SQL: SELECT c.first_name, c.last_name, SUM(o.total_amount) AS total_spent FROM custom...

[18/25] [SELECT_JOIN] Show products with their supplier names
         Exec: ✓  ExactMatch: ~  Status: success  Latency: 3131ms
         SQL: SELECT p.name AS product_name, s.name AS supplier_name FROM products p JOIN supp...

[19/25] [SELECT_JOIN] Show reviews with product names
         Exec: ✓  ExactMatch: ~  Status: success  Latency: 3211ms
         SQL: SELECT r.rating, r.body, p.name AS product_name FROM reviews r JOIN products p O...

[20/25] [SELECT_JOIN] Which products have been ordered more than 10 times?
         Exec: ✓  ExactMatch: ~  Status: success  Latency: 4782ms
         SQL: SELECT p.name, SUM(oi.quantity) AS total_ordered FROM products p JOIN order_item...

[21/25] [SELECT_TEMPORAL] How many orders were placed this year?
         Exec: ✓  ExactMatch: ~  Status: success  Latency: 2707ms
         SQL: SELECT COUNT(*) AS orders_this_year FROM orders WHERE EXTRACT(YEAR FROM created_...

[22/25] [SELECT_TEMPORAL] Show orders placed in the last 30 days
         Exec: ✓  ExactMatch: ~  Status: success  Latency: 3747ms
         SQL: SELECT id, customer_id, total_amount, status, created_at FROM orders WHERE creat...

[23/25] [SELECT_TEMPORAL] Show monthly order counts for this year
         Exec: ✓  ExactMatch: ~  Status: success  Latency: 2569ms
         SQL: SELECT EXTRACT(MONTH FROM created_at) AS month, COUNT(*) AS order_count FROM ord...

[24/25] [SELECT_TEMPORAL] Show all orders placed in 2023
         Exec: ✓  ExactMatch: ~  Status: success  Latency: 1896ms
         SQL: SELECT id, customer_id, total_amount, status FROM orders WHERE EXTRACT(YEAR FROM...

[25/25] [SELECT_TEMPORAL] How many customers registered each year?
         Exec: ✓  ExactMatch: ~  Status: success  Latency: 3840ms
         SQL: SELECT EXTRACT(YEAR FROM joined_at) AS year, COUNT(*) AS new_customers FROM cust...

======================================================================
  EVALUATION RESULTS
======================================================================
  Total queries:        25
  Execution Accuracy:   25/25  (100.0%)
  Exact Match Rate:     2/25  (8.0%)

  Per-type breakdown:
  Type                    Total    Exec%   Exact%
  ---------------------- ------ -------- --------
  SELECT_SIMPLE               6   100.0%    16.7%
  SELECT_AGGREGATE            7   100.0%     0.0%
  SELECT_JOIN                 7   100.0%    14.3%
  SELECT_TEMPORAL             5   100.0%     0.0%
======================================================================