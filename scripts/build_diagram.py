"""
Generate QueryMind AI — Pipeline Architecture Diagram (PNG)
Similar style to MediShield diagram.
Run: python3 scripts/build_diagram.py
Output: QueryMind_Architecture.png
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.patheffects as pe

fig, ax = plt.subplots(1, 1, figsize=(22, 14))
ax.set_xlim(0, 22)
ax.set_ylim(0, 14)
ax.axis("off")
fig.patch.set_facecolor("#0F172A")
ax.set_facecolor("#0F172A")

# ── Colour palette ────────────────────────────────────────────────────────────
C_BG       = "#0F172A"
C_TITLE_BG = "#0EA5E9"
C_STAGE_BG = "#1E3A5F"
C_CARD_BG  = "#0D1F38"
C_ARROW    = "#0EA5E9"
C_WHITE    = "#FFFFFF"
C_GRAY     = "#94A3B8"
C_GREEN    = "#22C55E"
C_YELLOW   = "#F59E0B"
C_PURPLE   = "#8B5CF6"
C_ORANGE   = "#F97316"
C_CYAN     = "#06B6D4"
C_RED      = "#EF4444"
C_PINK     = "#EC4899"

def rbox(ax, x, y, w, h, fc, ec="#0EA5E9", lw=1.2, radius=0.25, alpha=1.0):
    box = FancyBboxPatch((x, y), w, h,
                         boxstyle=f"round,pad=0,rounding_size={radius}",
                         facecolor=fc, edgecolor=ec, linewidth=lw, alpha=alpha,
                         zorder=3)
    ax.add_patch(box)
    return box

def label(ax, x, y, text, size=8, color=C_WHITE, bold=False, ha="center", va="center", zorder=5):
    weight = "bold" if bold else "normal"
    ax.text(x, y, text, fontsize=size, color=color, ha=ha, va=va,
            fontweight=weight, zorder=zorder, wrap=True,
            multialignment="center")

def arrow(ax, x1, y1, x2, y2, color=C_ARROW, lw=1.8):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw),
                zorder=4)

def icon_circle(ax, x, y, r, color, text, tsize=10):
    circ = plt.Circle((x, y), r, color=color, zorder=4)
    ax.add_patch(circ)
    ax.text(x, y, text, fontsize=tsize, color=C_WHITE, ha="center",
            va="center", fontweight="bold", zorder=5)


# ══════════════════════════════════════════════════════════════════════════════
# TITLE
# ══════════════════════════════════════════════════════════════════════════════
rbox(ax, 0.2, 12.8, 21.6, 1.0, fc=C_TITLE_BG, ec=C_TITLE_BG, radius=0.3)
label(ax, 11.0, 13.38, "QueryMind AI  —  Text-to-SQL Analytics Engine",
      size=18, bold=True, color=C_WHITE)
label(ax, 11.0, 13.05,
      "Natural language querying over PostgreSQL  •  7-Stage Modular Pipeline  •  Qdrant RAG  •  GPT-4o  •  Runtime Guardrails",
      size=9, color="#E0F2FE")

# Tech logos row
techs = [
    ("🤖", "OpenAI GPT-4o", 2.2),
    ("📦", "Qdrant", 4.8),
    ("📄", "Docling", 7.2),
    ("🐘", "PostgreSQL 16", 9.8),
    ("⚡", "FastAPI", 12.5),
    ("🌐", "Next.js 14", 15.0),
    ("🔍", "sqlglot", 17.5),
    ("🐳", "Docker", 20.0),
]
for icon, name, tx in techs:
    label(ax, tx, 12.88, f"{icon} {name}", size=7.5, color="#BAE6FD")


# ══════════════════════════════════════════════════════════════════════════════
# LEFT PANEL — Input
# ══════════════════════════════════════════════════════════════════════════════
rbox(ax, 0.2, 7.5, 2.6, 5.0, fc=C_CARD_BG, ec=C_PURPLE, lw=1.5, radius=0.3)
label(ax, 1.5, 12.1, "💬 User Input", size=9, bold=True, color=C_PURPLE)

inputs = [
    ("📊", "Aggregates", '"Total revenue?"'),
    ("🔗", "Joins",      '"Orders + names"'),
    ("📅", "Temporal",   '"Last 30 days"'),
    ("🔍", "Simple",     '"List customers"'),
]
for i, (ic, typ, ex) in enumerate(inputs):
    iy = 11.4 - i * 0.95
    rbox(ax, 0.35, iy - 0.35, 2.3, 0.75, fc="#1E1B4B", ec=C_PURPLE, lw=0.8, radius=0.15)
    label(ax, 0.72, iy + 0.02, ic, size=11)
    label(ax, 1.55, iy + 0.15, typ, size=8, bold=True, color=C_WHITE)
    label(ax, 1.55, iy - 0.08, ex, size=7, color=C_GRAY)

label(ax, 1.5, 7.9, "FastAPI\nAsync Upload", size=7.5, color=C_GRAY)
rbox(ax, 0.5, 7.6, 2.0, 0.55, fc="#0D1F38", ec=C_GRAY, lw=0.8, radius=0.15)
label(ax, 1.5, 7.88, "POST  /query", size=8, color=C_CYAN, bold=True)

# arrow from input to pipeline
arrow(ax, 2.8, 10.0, 3.5, 10.0)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN PIPELINE — 7 stages (horizontal)
# ══════════════════════════════════════════════════════════════════════════════
stages = [
    {
        "num": "1", "label": "Classifier",
        "color": C_CYAN, "icon": "🎯",
        "x": 3.5, "bullets": ["Intent detection", "SELECT_SIMPLE", "SELECT_AGG", "SELECT_JOIN", "SELECT_TEMPORAL", "BLOCKED"],
        "model": "GPT-4o"
    },
    {
        "num": "2", "label": "Schema\nLinker",
        "color": C_GREEN, "icon": "🔗",
        "x": 5.85, "bullets": ["Entity mapping", "Table resolution", "Column matching", "Alias handling"],
        "model": "DB Introspect"
    },
    {
        "num": "3", "label": "Retriever",
        "color": C_YELLOW, "icon": "🔍",
        "x": 8.2, "bullets": ["Embed question", "Qdrant search", "Top-4 examples", "Cosine similarity"],
        "model": "Qdrant RAG"
    },
    {
        "num": "4", "label": "Generator",
        "color": C_ORANGE, "icon": "⚡",
        "x": 10.55, "bullets": ["Build prompt", "Schema context", "Few-shot examples", "GPT-4o → SQL"],
        "model": "GPT-4o"
    },
    {
        "num": "5", "label": "Validator",
        "color": C_RED, "icon": "🛡",
        "x": 12.9, "bullets": ["sqlglot AST", "Schema check", "Guardrail rules", "Block/Allow"],
        "model": "sqlglot"
    },
    {
        "num": "6", "label": "Executor",
        "color": C_PINK, "icon": "▶",
        "x": 15.25, "bullets": ["Run SQL safely", "Catch errors", "Self-heal retry", "Row limit apply"],
        "model": "PostgreSQL"
    },
    {
        "num": "7", "label": "Formatter",
        "color": C_PURPLE, "icon": "📋",
        "x": 17.6, "bullets": ["JSON table", "Column names", "Row count", "NL summary"],
        "model": "GPT-4o"
    },
]

BOX_W = 2.1
BOX_H = 4.8
BOX_Y = 7.3

for i, st in enumerate(stages):
    x = st["x"]
    col = st["color"]

    # Main card
    rbox(ax, x, BOX_Y, BOX_W, BOX_H, fc=C_CARD_BG, ec=col, lw=1.8, radius=0.25)

    # Header band
    rbox(ax, x, BOX_Y + BOX_H - 1.05, BOX_W, 1.05, fc=col, ec=col, lw=0, radius=0.25)
    # fix bottom of header band
    rbox(ax, x, BOX_Y + BOX_H - 1.05, BOX_W, 0.35, fc=col, ec=col, lw=0, radius=0.0)

    label(ax, x + BOX_W/2, BOX_Y + BOX_H - 0.38,
          f"[{st['num']}]  {st['icon']}  {st['label']}",
          size=8.5, bold=True, color=C_BG)

    # Bullets
    for j, b in enumerate(st["bullets"]):
        by = BOX_Y + BOX_H - 1.45 - j * 0.52
        label(ax, x + 0.18, by, "▸", size=7, color=col, ha="left")
        label(ax, x + 0.42, by, b, size=7.5, color=C_WHITE, ha="left")

    # Model badge
    rbox(ax, x + 0.2, BOX_Y + 0.12, BOX_W - 0.4, 0.42,
         fc="#0A1628", ec=col, lw=0.8, radius=0.12)
    label(ax, x + BOX_W/2, BOX_Y + 0.33, st["model"], size=7.5, color=col, bold=True)

    # Stage number circle
    icon_circle(ax, x - 0.01, BOX_Y + BOX_H - 0.01, 0.22, col, st["num"], tsize=8)

    # Arrow to next stage
    if i < len(stages) - 1:
        arrow(ax, x + BOX_W + 0.02, BOX_Y + BOX_H/2 + 0.3,
              x + BOX_W + 0.22, BOX_Y + BOX_H/2 + 0.3, lw=2.0)

# Self-heal arc (Executor → Generator)
ax.annotate("", xy=(12.55, BOX_Y + 0.6), xytext=(17.25, BOX_Y + 0.6),
            arrowprops=dict(arrowstyle="-|>", color=C_RED, lw=1.5,
                            connectionstyle="arc3,rad=0.35"), zorder=4)
label(ax, 14.9, BOX_Y - 0.28, "🔄  Self-Heal: error injected back to GPT-4o for retry",
      size=7.5, color=C_RED)


# ══════════════════════════════════════════════════════════════════════════════
# DATA & KNOWLEDGE LAYER
# ══════════════════════════════════════════════════════════════════════════════
rbox(ax, 0.2, 2.5, 13.8, 4.55, fc="#080F1C", ec=C_CYAN, lw=1.5, radius=0.3)
label(ax, 7.1, 6.72, "Data & Knowledge Layer", size=10, bold=True, color=C_CYAN)

# PostgreSQL
rbox(ax, 0.4, 2.65, 3.2, 3.8, fc=C_CARD_BG, ec=C_GREEN, lw=1.3, radius=0.2)
label(ax, 2.0, 6.12, "🐘  PostgreSQL 16", size=8.5, bold=True, color=C_GREEN)
pg_tables = [
    ("customers",   "1 000+ rows"),
    ("orders",      "1 000+ rows"),
    ("order_items", "3 000+ rows"),
    ("products",    "1 000+ rows"),
    ("categories",  "7 rows"),
    ("suppliers",   "20 rows"),
    ("reviews",     "1 000+ rows"),
]
for j, (tbl, cnt) in enumerate(pg_tables):
    ty = 5.72 - j * 0.44
    label(ax, 0.75, ty, "◼", size=6, color=C_GREEN, ha="left")
    label(ax, 1.0,  ty, tbl, size=7.5, color=C_WHITE, ha="left")
    label(ax, 3.35, ty, cnt, size=6.5, color=C_GRAY, ha="right")

# Qdrant
rbox(ax, 3.8, 2.65, 3.2, 3.8, fc=C_CARD_BG, ec=C_YELLOW, lw=1.3, radius=0.2)
label(ax, 5.4, 6.12, "📦  Qdrant Vector DB", size=8.5, bold=True, color=C_YELLOW)
qdrant_cols = [
    ("few_shot_examples", "30 Q→SQL pairs", "1536 dims"),
    ("schema_docs",       "Document chunks", "1536 dims"),
]
for j, (col_name, desc, dims) in enumerate(qdrant_cols):
    cy = 5.55 - j * 1.45
    rbox(ax, 3.95, cy - 0.55, 2.9, 1.3, fc="#1A1500", ec=C_YELLOW, lw=0.7, radius=0.15)
    label(ax, 5.4, cy + 0.42, col_name, size=8, bold=True, color=C_YELLOW)
    label(ax, 5.4, cy + 0.08, desc, size=7.5, color=C_WHITE)
    label(ax, 5.4, cy - 0.25, f"text-embedding-3-small  •  {dims}", size=6.5, color=C_GRAY)

# Docling
rbox(ax, 7.2, 2.65, 3.1, 3.8, fc=C_CARD_BG, ec=C_ORANGE, lw=1.3, radius=0.2)
label(ax, 8.75, 6.12, "📄  Docling Parser", size=8.5, bold=True, color=C_ORANGE)
doc_items = ["PDF → markdown", "DOCX → chunks", "HTML → text", "Word-count chunking",
             "400 words / chunk", "50-word overlap", "UUID dedup", "→ schema_docs"]
for j, item in enumerate(doc_items):
    dy = 5.72 - j * 0.44
    label(ax, 7.45, dy, "▸", size=7, color=C_ORANGE, ha="left")
    label(ax, 7.7,  dy, item, size=7.5, color=C_WHITE, ha="left")

# Admin DB tables
rbox(ax, 10.55, 2.65, 3.2, 3.8, fc=C_CARD_BG, ec=C_PINK, lw=1.3, radius=0.2)
label(ax, 12.15, 6.12, "🗂  Admin Tables (PG)", size=8.5, bold=True, color=C_PINK)
admin_tables = [
    ("few_shot_examples", "Q→SQL pairs store"),
    ("schema_columns",    "Column metadata"),
    ("guardrail_config",  "Runtime toggles"),
    ("model_config",      "LLM settings"),
    ("query_logs",        "Full audit trail"),
]
for j, (tbl, desc) in enumerate(admin_tables):
    ay = 5.7 - j * 0.66
    rbox(ax, 10.7, ay - 0.2, 2.9, 0.58, fc="#1A001A", ec=C_PINK, lw=0.6, radius=0.12)
    label(ax, 10.95, ay + 0.1, tbl, size=7.5, bold=True, color=C_PINK, ha="left")
    label(ax, 10.95, ay - 0.1, desc, size=6.8, color=C_GRAY, ha="left")

# Arrows from data layer up to pipeline stages
data_arrows = [
    (2.0,  6.45, 4.0,  BOX_Y,  C_GREEN,  "customers\norders…"),
    (5.4,  6.45, 9.3,  BOX_Y,  C_YELLOW, "top-4\nexamples"),
    (8.75, 6.45, 8.75, BOX_Y,  C_ORANGE, "doc\nchunks"),
    (12.1, 6.45, 14.0, BOX_Y,  C_PINK,   "guardrails\nconfig"),
]
for x1, y1, x2, y2, col, lbl in data_arrows:
    arrow(ax, x1, y1, x2, y2, color=col, lw=1.5)


# ══════════════════════════════════════════════════════════════════════════════
# RIGHT PANEL — Output & Admin UI
# ══════════════════════════════════════════════════════════════════════════════
rbox(ax, 19.9, 7.3, 1.9, 4.8, fc=C_CARD_BG, ec=C_GREEN, lw=1.5, radius=0.25)
label(ax, 20.85, 11.78, "✅ Output", size=8.5, bold=True, color=C_GREEN)

outputs = ["JSON table", "Column names", "Row count", "NL Summary", "Latency ms", "Query type"]
for j, o in enumerate(outputs):
    oy = 11.38 - j * 0.52
    label(ax, 20.1, oy, "▸", size=7, color=C_GREEN, ha="left")
    label(ax, 20.35, oy, o, size=7.5, color=C_WHITE, ha="left")

rbox(ax, 19.95, 7.45, 1.8, 0.55, fc="#0A2010", ec=C_GREEN, lw=0.8, radius=0.12)
label(ax, 20.85, 7.73, "GET results", size=7.5, color=C_GREEN, bold=True)

# Arrow from formatter to output
arrow(ax, 19.7, BOX_Y + BOX_H/2 + 0.3, 19.9, BOX_Y + BOX_H/2 + 0.3, lw=2.0)


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN UI PANEL
# ══════════════════════════════════════════════════════════════════════════════
rbox(ax, 14.2, 2.65, 7.6, 3.8, fc="#080F1C", ec=C_PURPLE, lw=1.5, radius=0.3)
label(ax, 18.0, 6.12, "⚙️  Admin Panel  —  Next.js 14 + React + Tailwind CSS",
      size=9, bold=True, color=C_PURPLE)

admin_screens = [
    ("🗃", "Schema Manager",   "Browse tables, add descriptions\n& synonyms, mark sensitive cols",  C_CYAN,   14.35),
    ("📚", "Examples Manager", "Add / edit / delete Q→SQL pairs\nSync all to Qdrant embeddings",     C_YELLOW, 16.25),
    ("📜", "Query Logs",       "Full audit: SQL, status,\nlatency, row count, filter",               C_GREEN,  18.15),
    ("🛡", "Guardrails",       "Toggle SELECT/INSERT/UPDATE\nDELETE + max_rows limit",               C_RED,    20.05),
]
for ic, name, desc, col, sx in admin_screens:
    rbox(ax, sx, 2.82, 1.75, 3.1, fc=C_CARD_BG, ec=col, lw=1.0, radius=0.18)
    label(ax, sx + 0.875, 5.62, ic, size=14)
    label(ax, sx + 0.875, 5.22, name, size=7.5, bold=True, color=col)
    label(ax, sx + 0.875, 4.82, desc, size=6.5, color=C_GRAY)
    # URL badge
    rbox(ax, sx + 0.1, 2.92, 1.55, 0.38, fc="#0A1628", ec=col, lw=0.6, radius=0.1)
    label(ax, sx + 0.875, 3.11, f"/admin/{name.lower().split()[0]}", size=6.5, color=col)


# ══════════════════════════════════════════════════════════════════════════════
# EVALUATION SUMMARY (bottom right)
# ══════════════════════════════════════════════════════════════════════════════
rbox(ax, 14.2, 0.15, 7.6, 2.2, fc="#080F1C", ec=C_GREEN, lw=1.5, radius=0.3)
label(ax, 18.0, 2.02, "📊  Evaluation Summary  —  25 Ground-Truth Queries", size=9, bold=True, color=C_GREEN)

eval_metrics = [
    ("100%", "Execution\nAccuracy", C_GREEN,  15.0),
    ("8%",   "Exact\nMatch Rate",   C_YELLOW, 17.1),
    ("~3s",  "Avg\nLatency",        C_CYAN,   19.2),
    ("30",   "Few-Shot\nExamples",  C_ORANGE, 21.3),
]
for val, lbl, col, ex in eval_metrics:
    rbox(ax, ex - 0.85, 0.28, 1.7, 1.55, fc=C_CARD_BG, ec=col, lw=1.0, radius=0.18)
    label(ax, ex, 1.45, val,  size=18, bold=True, color=col)
    label(ax, ex, 0.72, lbl,  size=7,  color=C_GRAY)

# Query type badges
query_types = [
    ("SELECT_SIMPLE",    C_CYAN,   14.35),
    ("SELECT_AGGREGATE", C_GREEN,  16.1),
    ("SELECT_JOIN",      C_PURPLE, 17.9),
    ("SELECT_TEMPORAL",  C_YELLOW, 19.75),
]
for qt, col, qx in query_types:
    rbox(ax, qx, 0.18, 1.65, 0.38, fc="#0A1628", ec=col, lw=0.8, radius=0.1)
    label(ax, qx + 0.825, 0.37, qt, size=6, color=col, bold=True)


# ══════════════════════════════════════════════════════════════════════════════
# HOW IT WORKS (right column)
# ══════════════════════════════════════════════════════════════════════════════
rbox(ax, 0.2, 0.15, 13.8, 2.2, fc="#080F1C", ec=C_CYAN, lw=1.5, radius=0.3)
label(ax, 7.1, 2.02, "⚡  How It Works", size=9, bold=True, color=C_CYAN)

steps = [
    ("1", "User types a natural language question into the Query UI at localhost:3000/query"),
    ("2", "Classifier detects intent type — simple, aggregate, join, temporal, or blocked"),
    ("3", "Schema Linker maps entities to real PostgreSQL table/column names"),
    ("4", "Retriever embeds the question and fetches top-4 similar Q→SQL pairs from Qdrant"),
    ("5", "Generator calls GPT-4o with schema + examples → returns SQL"),
    ("6", "Validator checks syntax (sqlglot AST), schema, and guardrail rules"),
    ("7", "Executor runs SQL on PostgreSQL. On error → self-heal retry with error fed back to LLM"),
    ("8", "Formatter returns JSON table + column names + natural language summary"),
]
col_break = 4
for i, (num, step) in enumerate(steps):
    col_i = i // col_break
    row_i = i % col_break
    sx = 0.4  + col_i * 6.9
    sy = 1.62 - row_i * 0.42
    icon_circle(ax, sx + 0.22, sy, 0.16, C_CYAN, num, tsize=6.5)
    label(ax, sx + 0.55, sy, step, size=7, color=C_WHITE, ha="left", va="center")


# ══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════════════════
label(ax, 11.0, 0.07,
      "github.com/vijaymamilla/querymind   •   Backend: FastAPI localhost:8000   •   Admin UI: Next.js localhost:3000   •   Codebasics AI Engineering Bootcamp Capstone",
      size=7, color=C_GRAY)


# ── Save ──────────────────────────────────────────────────────────────────────
plt.tight_layout(pad=0)
out = "QueryMind_Architecture.png"
plt.savefig(out, dpi=180, bbox_inches="tight",
            facecolor=C_BG, edgecolor="none")
plt.close()
print(f"✅  Saved: {out}  (open to view)")
