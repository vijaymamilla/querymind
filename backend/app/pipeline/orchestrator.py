"""
Pipeline Orchestrator
Wires all 7 components into the full NL → SQL → Result pipeline.
Handles the single retry loop for self-healing SQL.
"""

import time
from sqlalchemy.ext.asyncio import AsyncSession

from app.pipeline.classifier import classifier
from app.pipeline.schema_linker import schema_linker
from app.pipeline.retriever import retriever
from app.pipeline.generator import generator
from app.pipeline.validator import validator
from app.pipeline.executor import executor
from app.pipeline.formatter import formatter
from app.schemas.pipeline import QueryResponse, ErrorResponse


class QueryPipeline:
    async def run(self, question: str, db: AsyncSession) -> QueryResponse | ErrorResponse:
        start = time.perf_counter()

        # ── Step 1: Classify ──────────────────────────────────────
        classifier_out = await classifier.classify(question)

        if classifier_out.query_type == "UNSUPPORTED":
            return ErrorResponse(
                error="Unsupported query",
                detail=(
                    "This question appears to request a data modification or an operation "
                    "not supported by this system. Only read-only SELECT queries are allowed."
                ),
            )

        # ── Step 2: Schema Link ───────────────────────────────────
        linker_out = await schema_linker.link(
            question=question,
            tables_mentioned=classifier_out.tables_mentioned,
            columns_mentioned=classifier_out.columns_mentioned,
            db=db,
        )

        # Get formatted schema string for the prompt
        schema_context = await schema_linker.get_schema_context(db)

        # ── Step 3: Retrieve Few-Shot Examples ────────────────────
        examples_out = await retriever.retrieve(question=question, top_k=4)

        # ── Step 4: Generate SQL ──────────────────────────────────
        gen_out = await generator.generate(
            question=question,
            schema_context=schema_context,
            linker_output=linker_out,
            examples_output=examples_out,
        )

        # ── Step 5: Validate SQL (with one retry) ─────────────────
        val_out = await validator.validate(sql=gen_out.sql, db=db)

        if not val_out.valid:
            # Retry once with error injected
            gen_out = await generator.generate(
                question=question,
                schema_context=schema_context,
                linker_output=linker_out,
                examples_output=examples_out,
                error_context="; ".join(val_out.errors),
            )
            val_out = await validator.validate(sql=gen_out.sql, db=db)

            if not val_out.valid:
                return ErrorResponse(
                    error="SQL generation failed",
                    detail=f"Could not generate valid SQL after retry: {'; '.join(val_out.errors)}",
                )

        # ── Step 6: Execute SQL ───────────────────────────────────
        exec_out = await executor.execute(sql=val_out.sanitized_sql, db=db)

        if exec_out.error:
            # Self-healing: retry with execution error
            gen_out = await generator.generate(
                question=question,
                schema_context=schema_context,
                linker_output=linker_out,
                examples_output=examples_out,
                error_context=exec_out.error,
            )
            val_out = await validator.validate(sql=gen_out.sql, db=db)
            if val_out.valid:
                exec_out = await executor.execute(sql=val_out.sanitized_sql, db=db)

        if exec_out.error:
            return ErrorResponse(
                error="Query execution failed",
                detail=exec_out.error,
            )

        # ── Step 7: Format Result ─────────────────────────────────
        result = await formatter.format(question=question, executor_output=exec_out)

        total_latency = (time.perf_counter() - start) * 1000

        return QueryResponse(
            question=question,
            query_type=classifier_out.query_type,
            generated_sql=val_out.sanitized_sql,
            explanation=gen_out.explanation,
            result=result,
            latency_ms=round(total_latency, 2),
            ambiguities=linker_out.ambiguities,
        )


# Singleton
pipeline = QueryPipeline()
