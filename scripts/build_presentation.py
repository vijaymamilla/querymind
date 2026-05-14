"""
Generate QueryMind AI capstone presentation (PPTX + instructions for PDF export).
Run: python3 scripts/build_presentation.py
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
import copy

# ── Brand colours ────────────────────────────────────────────────────────────
SKY    = RGBColor(0x0E, 0xA5, 0xE9)   # sky-500  (accent)
DARK   = RGBColor(0x0F, 0x17, 0x2A)   # near-black (bg)
WHITE  = RGBColor(0xFF, 0xFF, 0xFF)
GRAY   = RGBColor(0x94, 0xA3, 0xB8)   # slate-400
GREEN  = RGBColor(0x22, 0xC5, 0x5E)   # green-500
YELLOW = RGBColor(0xF5, 0x9E, 0x0B)   # amber-500

SLIDE_W = Inches(13.33)
SLIDE_H = Inches(7.5)

prs = Presentation()
prs.slide_width  = SLIDE_W
prs.slide_height = SLIDE_H

BLANK = prs.slide_layouts[6]   # completely blank layout


# ── Helpers ──────────────────────────────────────────────────────────────────

def add_slide():
    return prs.slides.add_slide(BLANK)

def bg(slide, color=DARK):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color

def box(slide, left, top, width, height,
        fill_color=None, line_color=None, line_width=Pt(0)):
    shape = slide.shapes.add_shape(
        1,  # MSO_SHAPE_TYPE.RECTANGLE
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    shape.line.width = line_width
    if fill_color:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill_color
    else:
        shape.fill.background()
    if line_color:
        shape.line.color.rgb = line_color
    return shape

def txt(slide, text, left, top, width, height,
        size=20, bold=False, color=WHITE, align=PP_ALIGN.LEFT,
        italic=False, wrap=True):
    txb = slide.shapes.add_textbox(
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    txb.word_wrap = wrap
    tf  = txb.text_frame
    tf.word_wrap = wrap
    p   = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size   = Pt(size)
    run.font.bold   = bold
    run.font.italic = italic
    run.font.color.rgb = color
    return txb

def accent_bar(slide, top=0.55, height=0.06):
    box(slide, 0, top, 13.33, height, fill_color=SKY)

def heading(slide, title, subtitle=None):
    accent_bar(slide)
    txt(slide, title, 0.5, 0.7, 12, 0.7, size=32, bold=True, color=WHITE)
    if subtitle:
        txt(slide, subtitle, 0.5, 1.35, 12, 0.45, size=16, color=GRAY, italic=True)

def bullet_block(slide, items, left, top, width, height,
                 size=17, color=WHITE, bullet="▸  "):
    txb = slide.shapes.add_textbox(
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    txb.word_wrap = True
    tf = txb.text_frame
    tf.word_wrap = True
    first = True
    for item in items:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.space_before = Pt(4)
        run = p.add_run()
        run.text = f"{bullet}{item}"
        run.font.size = Pt(size)
        run.font.color.rgb = color

def pill(slide, label, left, top, width=2.2, height=0.42,
         bg_color=SKY, text_color=WHITE, size=15):
    b = box(slide, left, top, width, height, fill_color=bg_color)
    b.line.fill.background()
    # rounded via adding text on top
    txb = slide.shapes.add_textbox(
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    tf = txb.text_frame
    p  = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = label
    run.font.size  = Pt(size)
    run.font.bold  = True
    run.font.color.rgb = text_color

def divider(slide, top):
    box(slide, 0.5, top, 12.33, 0.02, fill_color=RGBColor(0x1E, 0x3A, 0x5F))


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 1 — Title
# ═══════════════════════════════════════════════════════════════════════════
s = add_slide(); bg(s)
box(s, 0, 0, 13.33, 7.5, fill_color=DARK)
box(s, 0, 0, 13.33, 0.5, fill_color=SKY)           # top stripe
box(s, 0, 7.0, 13.33, 0.5, fill_color=SKY)          # bottom stripe

txt(s, "⚡ QueryMind AI", 1, 1.6, 11, 1.2,
    size=52, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
txt(s, "Text-to-SQL Analytics Engine", 1, 2.8, 11, 0.7,
    size=26, color=SKY, align=PP_ALIGN.CENTER, bold=True)
txt(s, "Codebasics AI Engineering Bootcamp  •  Assignment 3  •  Capstone Project",
    1, 3.55, 11, 0.5, size=15, color=GRAY, align=PP_ALIGN.CENTER)
txt(s, "Vijay Mamilla  |  vijay.mamilla@gmail.com",
    1, 5.5, 11, 0.4, size=14, color=GRAY, align=PP_ALIGN.CENTER)
txt(s, "github.com/vijaymamilla/querymind",
    1, 5.95, 11, 0.4, size=14, color=SKY, align=PP_ALIGN.CENTER)


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 2 — Problem Statement
# ═══════════════════════════════════════════════════════════════════════════
s = add_slide(); bg(s)
heading(s, "Problem Statement", "Why does QueryMind exist?")

problems = [
    "Business analysts need data insights but can't write SQL",
    "Data teams are bottlenecked by ad-hoc query requests",
    "Traditional BI tools require pre-built dashboards — no flexibility",
    "Natural language interfaces exist but lack guardrails and auditability",
]
solutions = [
    "Type a question in plain English → get SQL + results instantly",
    "Configurable guardrails prevent dangerous queries (DELETE, DROP)",
    "Every query logged with generated SQL, latency, and status",
    "Admin panel to tune behavior without touching code",
]

box(s, 0.4, 1.85, 5.9, 4.8, fill_color=RGBColor(0x1E, 0x29, 0x3B))
box(s, 6.9, 1.85, 5.9, 4.8, fill_color=RGBColor(0x0C, 0x2A, 0x1F))

txt(s, "❌  The Problem", 0.7, 1.95, 5.3, 0.45, size=16, bold=True, color=RGBColor(0xF8, 0x71, 0x71))
txt(s, "✅  QueryMind Solves It", 7.2, 1.95, 5.3, 0.45, size=16, bold=True, color=GREEN)

bullet_block(s, problems, 0.7, 2.5, 5.3, 3.8, size=15, color=RGBColor(0xF8, 0xD7, 0xDA))
bullet_block(s, solutions, 7.2, 2.5, 5.3, 3.8, size=15, color=RGBColor(0xD1, 0xFA, 0xE5))


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 3 — Architecture Overview
# ═══════════════════════════════════════════════════════════════════════════
s = add_slide(); bg(s)
heading(s, "Architecture — 7-Stage Pipeline", "Natural language → validated SQL → formatted results")

stages = [
    ("1", "Classifier",     "Intent type\ndetection"),
    ("2", "Schema\nLinker", "Entity →\ntable mapping"),
    ("3", "Retriever",      "Qdrant\nfew-shot RAG"),
    ("4", "Generator",      "GPT-4o\nSQL synthesis"),
    ("5", "Validator",      "Syntax +\nguardrails"),
    ("6", "Executor",       "Safe SQL run\n+ self-heal"),
    ("7", "Formatter",      "JSON table\n+ NL summary"),
]

box_w = 1.55
gap   = 0.18
start = 0.35
top_box = 2.1

for i, (num, name, desc) in enumerate(stages):
    lft = start + i * (box_w + gap)
    # Main box
    b = box(s, lft, top_box, box_w, 1.5, fill_color=SKY)
    b.line.fill.background()
    txt(s, f"[{num}]", lft, top_box + 0.05, box_w, 0.35,
        size=13, bold=True, color=DARK, align=PP_ALIGN.CENTER)
    txt(s, name, lft, top_box + 0.35, box_w, 0.55,
        size=14, bold=True, color=DARK, align=PP_ALIGN.CENTER)
    # Arrow (not after last)
    if i < len(stages) - 1:
        arr_left = lft + box_w + 0.01
        txt(s, "→", arr_left, top_box + 0.55, gap + 0.05, 0.4,
            size=14, bold=True, color=SKY, align=PP_ALIGN.CENTER)
    # Description below
    txt(s, desc, lft, top_box + 1.6, box_w, 0.7,
        size=11, color=GRAY, align=PP_ALIGN.CENTER)

# Self-heal note
box(s, 3.8, 4.5, 5.6, 0.65, fill_color=RGBColor(0x1E, 0x3A, 0x5F))
txt(s, "🔄  Self-Healing SQL: on execution error, the error is fed back to GPT-4o for one automatic retry",
    4.0, 4.55, 5.2, 0.55, size=13, color=SKY, align=PP_ALIGN.CENTER)

# Input / Output labels
txt(s, "User Question  ▶", 0.3, 2.35, 1.6, 0.35, size=12, color=GRAY)
txt(s, "▶  Results + NL Summary", 11.15, 2.35, 2.0, 0.35, size=12, color=GRAY)


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 4 — Tech Stack
# ═══════════════════════════════════════════════════════════════════════════
s = add_slide(); bg(s)
heading(s, "Technology Stack", "Modern async Python backend + React frontend")

layers = [
    ("LLM & Embeddings",  "OpenAI GPT-4o (SQL generation) • text-embedding-3-small (1536-dim, cosine)"),
    ("Vector Database",   "Qdrant — two collections: few_shot_examples  &  schema_docs"),
    ("Document Parsing",  "Docling — PDF, DOCX, HTML → chunked markdown → Qdrant index"),
    ("Backend",           "FastAPI (async) • SQLAlchemy async + asyncpg • pydantic-settings"),
    ("Relational DB",     "PostgreSQL 16 — e-commerce domain, 7 tables, 1 000+ rows each"),
    ("SQL Tooling",       "sqlglot v30 — syntax validation, AST-based table extraction"),
    ("Frontend",          "Next.js 14 • TypeScript • Tailwind CSS"),
    ("Infrastructure",    "Docker Compose (Postgres + Qdrant) • uv package manager"),
]

for i, (layer, detail) in enumerate(layers):
    top = 1.9 + i * 0.62
    box(s, 0.4, top, 2.5, 0.5, fill_color=SKY)
    txt(s, layer, 0.45, top + 0.04, 2.4, 0.44, size=13, bold=True,
        color=DARK, align=PP_ALIGN.LEFT)
    txt(s, detail, 3.1, top + 0.06, 9.8, 0.44, size=13, color=WHITE)
    if i < len(layers) - 1:
        box(s, 0.4, top + 0.5, 12.5, 0.01, fill_color=RGBColor(0x1E, 0x3A, 0x5F))


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 5 — Domain & Data
# ═══════════════════════════════════════════════════════════════════════════
s = add_slide(); bg(s)
heading(s, "Domain & Database Schema", "E-commerce PostgreSQL database — synthetic data")

tables = [
    ("customers",    "id, first_name, last_name, email, country, joined_at"),
    ("orders",       "id, customer_id, status, total_amount, created_at"),
    ("order_items",  "id, order_id, product_id, quantity, unit_price"),
    ("products",     "id, name, category_id, supplier_id, unit_price, stock_quantity"),
    ("categories",   "id, name, description"),
    ("suppliers",    "id, name, email, country"),
    ("reviews",      "id, product_id, customer_id, rating, body, created_at"),
]

for i, (tbl, cols) in enumerate(tables):
    row = i % 4
    col = i // 4
    left = 0.4 + col * 6.6
    top  = 2.0 + row * 1.3
    box(s, left, top, 6.2, 1.1, fill_color=RGBColor(0x0F, 0x2A, 0x46))
    txt(s, f"🗃  {tbl}", left + 0.15, top + 0.07, 5.8, 0.38,
        size=15, bold=True, color=SKY)
    txt(s, cols, left + 0.15, top + 0.48, 5.8, 0.55,
        size=11, color=GRAY)

txt(s, "1 000+ synthetic rows per table  •  Generated with Faker",
    0.4, 7.1, 12.5, 0.35, size=13, color=GRAY, align=PP_ALIGN.CENTER)


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 6 — Key Features
# ═══════════════════════════════════════════════════════════════════════════
s = add_slide(); bg(s)
heading(s, "Key Features", "What makes QueryMind production-ready")

features = [
    ("⚡", "Few-Shot RAG",
     "Top-4 semantically similar Q→SQL examples retrieved from Qdrant at query time. "
     "30 curated examples covering 4 query types."),
    ("🛡", "Guardrails",
     "Runtime toggles for SELECT / INSERT / UPDATE / DELETE. "
     "Max-rows limit (default 500). Validated before execution — never bypassed."),
    ("🔄", "Self-Healing SQL",
     "On execution error, the SQL + error message is injected back into GPT-4o for one automatic retry. "
     "Transparent in query logs."),
    ("📋", "Full Audit Log",
     "Every query logged: NL question, generated SQL, status, row count, latency. "
     "Filterable by success / error / blocked."),
    ("🗂", "Document Ingestion",
     "Upload PDF/DOCX/HTML schema docs via Docling. "
     "Chunks indexed to Qdrant schema_docs collection for context-aware generation."),
    ("⚙️", "Runtime Config",
     "Switch LLM model (gpt-4o ↔ gpt-4o-mini), SQL dialect, temperature — "
     "all via Admin UI without restarting the server."),
]

for i, (icon, title, desc) in enumerate(features):
    col = i % 2
    row = i // 2
    left = 0.4 + col * 6.5
    top  = 2.0 + row * 1.7
    box(s, left, top, 6.2, 1.55, fill_color=RGBColor(0x0D, 0x1F, 0x38))
    txt(s, f"{icon}  {title}", left + 0.2, top + 0.1, 5.8, 0.45,
        size=16, bold=True, color=SKY)
    txt(s, desc, left + 0.2, top + 0.55, 5.7, 0.9,
        size=12, color=GRAY)


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 7 — Admin Panel
# ═══════════════════════════════════════════════════════════════════════════
s = add_slide(); bg(s)
heading(s, "Admin Panel — 5 Management Screens", "Full React UI — no code changes needed")

screens = [
    ("🗃  Schema Manager",
     ["Browse live DB schema (7 tables)", "Add descriptions & synonyms per column",
      "Mark sensitive columns (masked in output)", "Refresh from live DB at any time"]),
    ("📚  Examples Manager",
     ["Add / edit / delete Q→SQL pairs", "Filter by query type", "Sync all to Qdrant embeddings",
      "30 examples pre-seeded across 4 types"]),
    ("📜  Query Logs",
     ["Full audit trail of every query", "Filter: All / Success / Error / Blocked",
      "Expand row to see generated SQL", "Pagination — 20 per page"]),
    ("🛡  Guardrails Config",
     ["Toggle SELECT/INSERT/UPDATE/DELETE", "Set max_rows limit",
      "Changes take effect immediately", "Blocked queries logged automatically"]),
    ("⚙️  Model Config",
     ["Switch GPT-4o / GPT-4o-mini", "Change SQL dialect",
      "Adjust temperature & max_tokens", "No server restart required"]),
]

for i, (title, bullets) in enumerate(screens):
    col = i % 3
    row = i // 3
    left = 0.35 + col * 4.35
    top  = 2.0 + row * 2.5
    box(s, left, top, 4.1, 2.3, fill_color=RGBColor(0x0D, 0x1F, 0x38))
    txt(s, title, left + 0.15, top + 0.1, 3.8, 0.45, size=14, bold=True, color=SKY)
    bullet_block(s, bullets, left + 0.15, top + 0.55, 3.8, 1.65,
                 size=11, color=GRAY, bullet="• ")


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 8 — Evaluation Results
# ═══════════════════════════════════════════════════════════════════════════
s = add_slide(); bg(s)
heading(s, "Evaluation Results", "25 ground-truth queries • 4 query types • automated harness")

# Big metric boxes
metrics = [
    ("100%", "Execution Accuracy", "25 / 25 queries ran\nsuccessfully", GREEN),
    ("8%",   "Exact Match Rate",   "LLM adds LIMIT 500\nguardrail — expected", YELLOW),
    ("~3s",  "Avg Latency",        "End-to-end: classify\n→ generate → execute", SKY),
]
for i, (val, label, note, color) in enumerate(metrics):
    left = 0.5 + i * 4.2
    box(s, left, 2.0, 3.8, 2.2, fill_color=RGBColor(0x0D, 0x1F, 0x38))
    txt(s, val,   left, 2.1, 3.8, 1.0, size=54, bold=True, color=color, align=PP_ALIGN.CENTER)
    txt(s, label, left, 3.05, 3.8, 0.45, size=14, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    txt(s, note,  left, 3.5,  3.8, 0.6,  size=11, color=GRAY, align=PP_ALIGN.CENTER)

# Per-type table
headers = ["Query Type", "Count", "Exec Accuracy", "Exact Match"]
rows = [
    ["SELECT_SIMPLE",    "6", "100%", "16.7%"],
    ["SELECT_AGGREGATE", "7", "100%", "0.0%"],
    ["SELECT_JOIN",      "7", "100%", "14.3%"],
    ["SELECT_TEMPORAL",  "5", "100%", "0.0%"],
]
col_w  = [3.0, 1.2, 2.2, 2.2]
col_x  = [0.5, 3.6, 4.9, 7.2]
top_tbl = 4.55

# Header row
for ci, (hdr, cx, cw) in enumerate(zip(headers, col_x, col_w)):
    box(s, cx, top_tbl, cw - 0.05, 0.42, fill_color=SKY)
    txt(s, hdr, cx + 0.05, top_tbl + 0.05, cw - 0.1, 0.35,
        size=12, bold=True, color=DARK, align=PP_ALIGN.CENTER)

for ri, row in enumerate(rows):
    for ci, (cell, cx, cw) in enumerate(zip(row, col_x, col_w)):
        bg_c = RGBColor(0x0D, 0x1F, 0x38) if ri % 2 == 0 else RGBColor(0x0A, 0x18, 0x2E)
        box(s, cx, top_tbl + 0.42 + ri * 0.42, cw - 0.05, 0.42, fill_color=bg_c)
        color = GREEN if cell == "100%" else WHITE
        txt(s, cell,
            cx + 0.05, top_tbl + 0.47 + ri * 0.42, cw - 0.1, 0.35,
            size=12, color=color, align=PP_ALIGN.CENTER)

txt(s, "Note: Exact match is low because the pipeline appends LIMIT 500 (max_rows guardrail) to all queries. "
    "Results are correct — execution accuracy is the primary metric.",
    0.5, 7.0, 12.3, 0.4, size=11, color=GRAY, italic=True, align=PP_ALIGN.CENTER)


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 9 — Live Demo Queries
# ═══════════════════════════════════════════════════════════════════════════
s = add_slide(); bg(s)
heading(s, "Live Demo — Sample Queries", "Type these in the Query interface at localhost:3000/query")

demo_qs = [
    ("SELECT_SIMPLE",    "List all pending orders"),
    ("SELECT_SIMPLE",    "Show products that are out of stock"),
    ("SELECT_AGGREGATE", "How many customers do we have?"),
    ("SELECT_AGGREGATE", "What is the total revenue from delivered orders?"),
    ("SELECT_AGGREGATE", "How many orders are there per status?"),
    ("SELECT_JOIN",      "Show all orders with customer names"),
    ("SELECT_JOIN",      "List the top 5 customers by total amount spent"),
    ("SELECT_JOIN",      "Which products have been ordered more than 10 times?"),
    ("SELECT_TEMPORAL",  "Show orders placed in the last 30 days"),
    ("SELECT_TEMPORAL",  "Show monthly order counts for this year"),
]

type_colors = {
    "SELECT_SIMPLE":    RGBColor(0x06, 0x7C, 0xA7),
    "SELECT_AGGREGATE": RGBColor(0x06, 0x78, 0x5E),
    "SELECT_JOIN":      RGBColor(0x6D, 0x28, 0xD9),
    "SELECT_TEMPORAL":  RGBColor(0x92, 0x40, 0x0E),
}

for i, (qtype, question) in enumerate(demo_qs):
    col = i % 2
    row = i // 2
    left = 0.4 + col * 6.5
    top  = 1.9 + row * 1.05
    c = type_colors[qtype]
    box(s, left, top, 6.1, 0.9, fill_color=RGBColor(0x0D, 0x1F, 0x38))
    box(s, left, top, 0.08, 0.9, fill_color=c)
    txt(s, qtype.replace("SELECT_", ""), left + 0.2, top + 0.04, 2.0, 0.32,
        size=10, color=c, bold=True)
    txt(s, f'"{question}"', left + 0.2, top + 0.44, 5.7, 0.4,
        size=13, color=WHITE, bold=True)


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 10 — Guardrail Demo
# ═══════════════════════════════════════════════════════════════════════════
s = add_slide(); bg(s)
heading(s, "Guardrails Demo", "Runtime access control — no code changes")

steps = [
    ("Step 1", "Go to Admin → Guardrails (localhost:3000/admin/guardrails)",
     "Show toggles: allow_select=ON, allow_insert=OFF, allow_update=OFF, allow_delete=OFF"),
    ("Step 2", 'Go to Query and type:  "Delete all customers"',
     'Result: BLOCKED ❌  —  "Operation DELETE is not permitted by guardrails"'),
    ("Step 3", "Go back to Guardrails — turn OFF allow_select",
     "Try any SELECT query — it is now blocked too"),
    ("Step 4", "Turn allow_select back ON",
     "Queries work again immediately — no server restart"),
]

for i, (step, action, result) in enumerate(steps):
    top = 2.0 + i * 1.28
    box(s, 0.4, top, 1.1, 1.1, fill_color=SKY)
    txt(s, step, 0.4, top + 0.28, 1.1, 0.55,
        size=12, bold=True, color=DARK, align=PP_ALIGN.CENTER)
    box(s, 1.6, top, 11.1, 1.1, fill_color=RGBColor(0x0D, 0x1F, 0x38))
    txt(s, action, 1.8, top + 0.05, 10.7, 0.45, size=14, bold=True, color=WHITE)
    txt(s, result, 1.8, top + 0.52, 10.7, 0.45, size=12, color=GRAY, italic=True)


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 11 — Project Structure
# ═══════════════════════════════════════════════════════════════════════════
s = add_slide(); bg(s)
heading(s, "Project Structure & Modularity", "Each pipeline stage is an independent, swappable module")

structure = """\
querymind/
├── backend/app/
│   ├── pipeline/
│   │   ├── classifier.py      ← Stage 1: intent classification
│   │   ├── schema_linker.py   ← Stage 2: entity → schema mapping
│   │   ├── retriever.py       ← Stage 3: Qdrant few-shot retrieval
│   │   ├── ingester.py        ← Docling doc parser + Qdrant indexer
│   │   ├── generator.py       ← Stage 4: OpenAI SQL generation
│   │   ├── validator.py       ← Stage 5: guardrails + syntax check
│   │   ├── executor.py        ← Stage 6: safe execution + self-heal
│   │   └── formatter.py       ← Stage 7: JSON + NL summary
│   └── admin/routes.py        ← All CRUD admin API endpoints
├── frontend/src/app/admin/    ← React admin UI (5 screens)
├── scripts/
│   ├── seed_db.py             ← Synthetic e-commerce data
│   └── seed_examples.py       ← 30 few-shot examples
└── eval/
    ├── ground_truth.py        ← 25 Q+SQL ground-truth pairs
    └── run_eval.py            ← Automated evaluation harness"""

box(s, 0.4, 1.85, 12.5, 5.4, fill_color=RGBColor(0x0A, 0x14, 0x24))
txb = s.shapes.add_textbox(Inches(0.65), Inches(2.0), Inches(12.0), Inches(5.1))
txb.word_wrap = False
tf = txb.text_frame
tf.word_wrap = False
p = tf.paragraphs[0]
run = p.add_run()
run.text = structure
run.font.size = Pt(12.5)
run.font.color.rgb = RGBColor(0xA5, 0xF3, 0xFC)   # cyan-200
run.font.name = "Courier New"


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 12 — Summary & Links
# ═══════════════════════════════════════════════════════════════════════════
s = add_slide(); bg(s)
box(s, 0, 0, 13.33, 7.5, fill_color=DARK)
box(s, 0, 0, 13.33, 0.5, fill_color=SKY)
box(s, 0, 7.0, 13.33, 0.5, fill_color=SKY)

txt(s, "⚡ QueryMind AI", 1, 0.7, 11, 0.8,
    size=36, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

achievements = [
    "✅  7-stage modular NL→SQL pipeline with self-healing",
    "✅  Qdrant vector search — 30 few-shot examples across 4 query types",
    "✅  Runtime guardrails — configurable without code changes",
    "✅  Full audit logging — every query tracked",
    "✅  React admin panel — 5 management screens",
    "✅  Evaluation harness — 100% execution accuracy on 25 queries",
    "✅  Docling document ingestion — schema docs → Qdrant context",
]
bullet_block(s, achievements, 2.0, 1.65, 9.3, 4.0, size=16, color=WHITE, bullet="")

divider(s, 5.8)

links = [
    ("📁  GitHub", "github.com/vijaymamilla/querymind"),
    ("🖥  Backend API", "localhost:8000/docs"),
    ("🌐  Admin UI", "localhost:3000"),
]
for i, (label, url) in enumerate(links):
    left = 1.5 + i * 3.7
    txt(s, label, left, 6.05, 3.4, 0.35, size=13, bold=True, color=GRAY, align=PP_ALIGN.CENTER)
    txt(s, url,   left, 6.42, 3.4, 0.35, size=13, color=SKY, align=PP_ALIGN.CENTER)


# ── Save ─────────────────────────────────────────────────────────────────────
out = "QueryMind_Presentation.pptx"
prs.save(out)
print(f"\n✅  Saved: {out}")
print(f"   Slides: {len(prs.slides)}")
print("\nTo export to PDF:")
print("  • macOS: Open in PowerPoint or LibreOffice → File → Export as PDF")
print("  • Or:    libreoffice --headless --convert-to pdf QueryMind_Presentation.pptx")
