"""Tests for the SQL Validator guardrails."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.pipeline.validator import SQLValidator


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.execute = AsyncMock()
    result = MagicMock()
    result.fetchall.return_value = [("orders",), ("customers",), ("products",)]
    db.execute.return_value = result
    return db


@pytest.mark.asyncio
async def test_blocks_delete(mock_db):
    v = SQLValidator()
    out = await v.validate("DELETE FROM orders WHERE id = 1", mock_db)
    assert not out.valid
    assert any("delete" in e.lower() for e in out.errors)


@pytest.mark.asyncio
async def test_blocks_drop(mock_db):
    v = SQLValidator()
    out = await v.validate("DROP TABLE orders", mock_db)
    assert not out.valid


@pytest.mark.asyncio
async def test_allows_select(mock_db):
    v = SQLValidator()
    out = await v.validate("SELECT * FROM orders", mock_db)
    assert out.valid
    assert "LIMIT" in out.sanitized_sql


@pytest.mark.asyncio
async def test_appends_limit(mock_db):
    v = SQLValidator()
    out = await v.validate("SELECT id, total FROM orders ORDER BY total DESC", mock_db)
    assert out.valid
    assert "LIMIT" in out.sanitized_sql


@pytest.mark.asyncio
async def test_respects_existing_limit(mock_db):
    v = SQLValidator()
    out = await v.validate("SELECT * FROM orders LIMIT 5", mock_db)
    assert out.valid
    assert out.sanitized_sql.upper().count("LIMIT") == 1
