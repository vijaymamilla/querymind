"""
Component 6: SQL Executor
Executes validated SQL against the configured database.
Uses the same async connection (read-only by role convention).
Captures latency and row count.
Outputs: SQLExecutorOutput
"""

import time
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.pipeline import SQLExecutorOutput


class SQLExecutor:
    async def execute(self, sql: str, db: AsyncSession) -> SQLExecutorOutput:
        start = time.perf_counter()
        try:
            result = await db.execute(text(sql))
            rows_raw = result.fetchall()
            columns = list(result.keys())
            latency_ms = (time.perf_counter() - start) * 1000

            rows = [dict(zip(columns, row)) for row in rows_raw]

            return SQLExecutorOutput(
                rows=rows,
                columns=columns,
                row_count=len(rows),
                latency_ms=round(latency_ms, 2),
            )
        except Exception as e:
            latency_ms = (time.perf_counter() - start) * 1000
            return SQLExecutorOutput(
                rows=[],
                columns=[],
                row_count=0,
                latency_ms=round(latency_ms, 2),
                error=str(e),
            )


# Singleton
executor = SQLExecutor()
