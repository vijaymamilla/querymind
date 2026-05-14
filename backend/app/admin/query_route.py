from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db.session import get_db
from app.models.admin import QueryLog
from app.pipeline.orchestrator import pipeline
from app.schemas.pipeline import QueryRequest, QueryResponse, ErrorResponse

router = APIRouter()


@router.post("/query", response_model=QueryResponse | ErrorResponse)
async def run_query(request: QueryRequest, db: AsyncSession = Depends(get_db)):
    """
    Main endpoint: converts a natural language question to SQL and returns results.
    """
    result = await pipeline.run(question=request.question, db=db)

    # Persist to query log
    if isinstance(result, QueryResponse):
        log = QueryLog(
            nl_query=request.question,
            query_type=result.query_type,
            generated_sql=result.generated_sql,
            status="success",
            latency_ms=result.latency_ms,
            row_count=result.result.row_count,
        )
    else:
        log = QueryLog(
            nl_query=request.question,
            status="error",
            error_message=result.detail,
        )

    db.add(log)
    await db.commit()

    return result
