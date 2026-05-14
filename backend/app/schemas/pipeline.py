"""
Typed Pydantic schemas for every pipeline component.
Each component consumes and produces these models — they are the contract
between stages and between frontend ↔ backend.
"""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────
# 1. Query Classifier
# ─────────────────────────────────────────────

class ClassifierOutput(BaseModel):
    query_type: str  # SELECT_SIMPLE | SELECT_AGGREGATE | SELECT_JOIN | SELECT_TEMPORAL | UNSUPPORTED
    tables_mentioned: list[str] = []
    columns_mentioned: list[str] = []
    confidence: float = 1.0


# ─────────────────────────────────────────────
# 2. Schema Linker
# ─────────────────────────────────────────────

class Ambiguity(BaseModel):
    mention: str
    candidates: list[str]  # e.g. ["billing.amount", "claims.amount"]


class SchemaLinkerOutput(BaseModel):
    resolved_tables: list[str]
    resolved_columns: list[str]
    ambiguities: list[Ambiguity] = []


# ─────────────────────────────────────────────
# 3. Examples Retriever
# ─────────────────────────────────────────────

class FewShotPair(BaseModel):
    question: str
    sql: str
    score: float = 1.0


class ExamplesRetrieverOutput(BaseModel):
    examples: list[FewShotPair]


# ─────────────────────────────────────────────
# 4. SQL Generator
# ─────────────────────────────────────────────

class SQLGeneratorOutput(BaseModel):
    sql: str
    explanation: str


# ─────────────────────────────────────────────
# 5. SQL Validator
# ─────────────────────────────────────────────

class SQLValidatorOutput(BaseModel):
    valid: bool
    sanitized_sql: str
    errors: list[str] = []


# ─────────────────────────────────────────────
# 6. SQL Executor
# ─────────────────────────────────────────────

class SQLExecutorOutput(BaseModel):
    rows: list[dict[str, Any]]
    columns: list[str]
    row_count: int
    latency_ms: float
    error: str | None = None


# ─────────────────────────────────────────────
# 7. Result Formatter
# ─────────────────────────────────────────────

class ResultFormatterOutput(BaseModel):
    table: list[dict[str, Any]]
    columns: list[str]
    nl_summary: str
    row_count: int


# ─────────────────────────────────────────────
# API Request / Response
# ─────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)


class QueryResponse(BaseModel):
    question: str
    query_type: str
    generated_sql: str
    explanation: str
    result: ResultFormatterOutput
    latency_ms: float
    ambiguities: list[Ambiguity] = []


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None


# ─────────────────────────────────────────────
# Admin — Schema Manager
# ─────────────────────────────────────────────

class SchemaColumnRead(BaseModel):
    id: int
    table_name: str
    column_name: str
    description: str | None
    synonyms: list[str]
    is_sensitive: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SchemaColumnCreate(BaseModel):
    table_name: str
    column_name: str
    description: str | None = None
    synonyms: list[str] = []
    is_sensitive: bool = False


class SchemaColumnUpdate(BaseModel):
    description: str | None = None
    synonyms: list[str] | None = None
    is_sensitive: bool | None = None


# ─────────────────────────────────────────────
# Admin — Examples Manager
# ─────────────────────────────────────────────

class FewShotExampleRead(BaseModel):
    id: int
    question: str
    sql: str
    query_type: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FewShotExampleCreate(BaseModel):
    question: str
    sql: str
    query_type: str = "SELECT_SIMPLE"


class FewShotExampleUpdate(BaseModel):
    question: str | None = None
    sql: str | None = None
    query_type: str | None = None


# ─────────────────────────────────────────────
# Admin — Query Logs
# ─────────────────────────────────────────────

class QueryLogRead(BaseModel):
    id: int
    nl_query: str
    query_type: str | None
    generated_sql: str | None
    status: str
    error_message: str | None
    latency_ms: float | None
    row_count: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class QueryLogListResponse(BaseModel):
    items: list[QueryLogRead]
    total: int
    page: int
    page_size: int


# ─────────────────────────────────────────────
# Admin — Guardrails
# ─────────────────────────────────────────────

class GuardrailConfigRead(BaseModel):
    key: str
    value: str
    description: str | None

    model_config = {"from_attributes": True}


class GuardrailConfigUpdate(BaseModel):
    value: str


# ─────────────────────────────────────────────
# Admin — Model Config
# ─────────────────────────────────────────────

class ModelConfigRead(BaseModel):
    key: str
    value: str
    description: str | None

    model_config = {"from_attributes": True}


class ModelConfigUpdate(BaseModel):
    value: str
