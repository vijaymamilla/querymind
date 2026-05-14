"""
Admin API routes for all 5 admin panels.
Each section is a self-contained router that can be mounted separately.
"""

import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete

from app.db.session import get_db
from app.models.admin import (
    FewShotExample,
    GuardrailConfig,
    ModelConfig,
    QueryLog,
    SchemaColumn,
)
from app.pipeline.retriever import retriever
from app.pipeline.ingester import ingester
from app.pipeline.schema_linker import schema_linker
from app.schemas.pipeline import (
    FewShotExampleCreate,
    FewShotExampleRead,
    FewShotExampleUpdate,
    GuardrailConfigRead,
    GuardrailConfigUpdate,
    ModelConfigRead,
    ModelConfigUpdate,
    QueryLogListResponse,
    QueryLogRead,
    SchemaColumnCreate,
    SchemaColumnRead,
    SchemaColumnUpdate,
)

# ─────────────────────────────────────────────
# Schema Manager
# ─────────────────────────────────────────────
schema_router = APIRouter(prefix="/admin/schema", tags=["Schema Manager"])


@schema_router.get("/introspect")
async def introspect_schema(db: AsyncSession = Depends(get_db)):
    """Return the live schema structure from the database."""
    schema_map = await schema_linker._introspect_schema(db)
    return {"schema": schema_map}


@schema_router.get("/columns", response_model=list[SchemaColumnRead])
async def list_columns(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SchemaColumn).order_by(SchemaColumn.table_name))
    return result.scalars().all()


@schema_router.post("/columns", response_model=SchemaColumnRead, status_code=201)
async def create_column(body: SchemaColumnCreate, db: AsyncSession = Depends(get_db)):
    col = SchemaColumn(**body.model_dump())
    db.add(col)
    await db.flush()
    await db.refresh(col)
    return col


@schema_router.patch("/columns/{column_id}", response_model=SchemaColumnRead)
async def update_column(
    column_id: int, body: SchemaColumnUpdate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(SchemaColumn).where(SchemaColumn.id == column_id))
    col = result.scalar_one_or_none()
    if not col:
        raise HTTPException(status_code=404, detail="Column not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(col, field, value)
    await db.flush()
    await db.refresh(col)
    return col


@schema_router.delete("/columns/{column_id}", status_code=204)
async def delete_column(column_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SchemaColumn).where(SchemaColumn.id == column_id))
    col = result.scalar_one_or_none()
    if not col:
        raise HTTPException(status_code=404, detail="Column not found")
    await db.delete(col)


# ─────────────────────────────────────────────
# Examples Manager
# ─────────────────────────────────────────────
examples_router = APIRouter(prefix="/admin/examples", tags=["Examples Manager"])


@examples_router.get("", response_model=list[FewShotExampleRead])
async def list_examples(
    query_type: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(FewShotExample).order_by(FewShotExample.created_at.desc())
    if query_type:
        stmt = stmt.where(FewShotExample.query_type == query_type)
    result = await db.execute(stmt)
    return result.scalars().all()


@examples_router.post("", response_model=FewShotExampleRead, status_code=201)
async def create_example(body: FewShotExampleCreate, db: AsyncSession = Depends(get_db)):
    ex = FewShotExample(**body.model_dump())
    db.add(ex)
    await db.flush()
    await db.refresh(ex)
    await retriever.upsert_example(ex.id, ex.question, ex.sql, ex.query_type)
    return ex


@examples_router.patch("/{example_id}", response_model=FewShotExampleRead)
async def update_example(
    example_id: int, body: FewShotExampleUpdate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(FewShotExample).where(FewShotExample.id == example_id))
    ex = result.scalar_one_or_none()
    if not ex:
        raise HTTPException(status_code=404, detail="Example not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(ex, field, value)
    await db.flush()
    await db.refresh(ex)
    await retriever.upsert_example(ex.id, ex.question, ex.sql, ex.query_type)
    return ex


@examples_router.delete("/{example_id}", status_code=204)
async def delete_example(example_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FewShotExample).where(FewShotExample.id == example_id))
    ex = result.scalar_one_or_none()
    if not ex:
        raise HTTPException(status_code=404, detail="Example not found")
    await retriever.delete_example(example_id)
    await db.delete(ex)


@examples_router.post("/sync-embeddings", status_code=202)
async def sync_embeddings(db: AsyncSession = Depends(get_db)):
    """Re-index all examples into Qdrant."""
    await retriever.sync_from_db(db)
    return {"message": "Sync complete"}


# ─────────────────────────────────────────────
# Documents (Docling ingestion)
# ─────────────────────────────────────────────
documents_router = APIRouter(prefix="/admin/documents", tags=["Documents"])


@documents_router.post("/upload", status_code=202)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a PDF, DOCX, or HTML file. Docling parses it and the text chunks
    are indexed into Qdrant's 'schema_docs' collection.
    """
    suffix = Path(file.filename).suffix.lower()
    allowed = {".pdf", ".docx", ".html", ".htm", ".md", ".txt"}
    if suffix not in allowed:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file type '{suffix}'. Allowed: {', '.join(allowed)}",
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = Path(tmp.name)

    try:
        chunk_count = await ingester.ingest(tmp_path, doc_name=file.filename)
    finally:
        tmp_path.unlink(missing_ok=True)

    return {"doc_name": file.filename, "chunks_indexed": chunk_count}


@documents_router.delete("/{doc_name:path}", status_code=204)
async def delete_document(doc_name: str):
    """Remove all indexed chunks for a document by its original filename."""
    await ingester.delete_document(doc_name)


@documents_router.get("/search")
async def search_documents(q: str, top_k: int = Query(3, ge=1, le=20)):
    """Semantic search over ingested document chunks."""
    results = await ingester.search(q, top_k=top_k)
    return {"results": results}


# ─────────────────────────────────────────────
# Query Logs
# ─────────────────────────────────────────────
logs_router = APIRouter(prefix="/admin/logs", tags=["Query Logs"])


@logs_router.get("", response_model=QueryLogListResponse)
async def list_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(QueryLog).order_by(QueryLog.created_at.desc())
    count_stmt = select(func.count()).select_from(QueryLog)

    if status:
        stmt = stmt.where(QueryLog.status == status)
        count_stmt = count_stmt.where(QueryLog.status == status)

    total = (await db.execute(count_stmt)).scalar_one()
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    items = (await db.execute(stmt)).scalars().all()

    return QueryLogListResponse(items=items, total=total, page=page, page_size=page_size)


# ─────────────────────────────────────────────
# Guardrails Config
# ─────────────────────────────────────────────
guardrails_router = APIRouter(prefix="/admin/guardrails", tags=["Guardrails"])


@guardrails_router.get("", response_model=list[GuardrailConfigRead])
async def list_guardrails(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(GuardrailConfig))
    return result.scalars().all()


@guardrails_router.patch("/{key}", response_model=GuardrailConfigRead)
async def update_guardrail(
    key: str, body: GuardrailConfigUpdate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(GuardrailConfig).where(GuardrailConfig.key == key))
    cfg = result.scalar_one_or_none()
    if not cfg:
        raise HTTPException(status_code=404, detail="Guardrail key not found")
    cfg.value = body.value
    await db.flush()
    await db.refresh(cfg)
    return cfg


# ─────────────────────────────────────────────
# Model Config
# ─────────────────────────────────────────────
model_config_router = APIRouter(prefix="/admin/config", tags=["Model Config"])


@model_config_router.get("", response_model=list[ModelConfigRead])
async def list_model_config(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ModelConfig))
    return result.scalars().all()


@model_config_router.patch("/{key}", response_model=ModelConfigRead)
async def update_model_config(
    key: str, body: ModelConfigUpdate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(ModelConfig).where(ModelConfig.key == key))
    cfg = result.scalar_one_or_none()
    if not cfg:
        raise HTTPException(status_code=404, detail="Config key not found")
    cfg.value = body.value
    await db.flush()
    await db.refresh(cfg)
    return cfg
