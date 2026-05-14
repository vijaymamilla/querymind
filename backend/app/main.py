from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.admin.query_route import router as query_router
from app.admin.routes import (
    schema_router,
    examples_router,
    logs_router,
    guardrails_router,
    model_config_router,
    documents_router,
)
from app.db.session import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create admin tables on startup (use Alembic for production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="QueryMind AI",
    description="Text-to-SQL Analytics Engine",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ─────────────────────────────────────
app.include_router(query_router, tags=["Query"])
app.include_router(schema_router)
app.include_router(examples_router)
app.include_router(logs_router)
app.include_router(guardrails_router)
app.include_router(model_config_router)
app.include_router(documents_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "QueryMind AI"}
