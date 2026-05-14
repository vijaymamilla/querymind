"""
Component 7: Result Formatter
Converts raw SQL results into:
  - Typed table data for UI rendering
  - A 1–2 sentence NL summary via LLM
Outputs: ResultFormatterOutput
"""

from openai import AsyncOpenAI

from app.config import settings
from app.schemas.pipeline import ResultFormatterOutput, SQLExecutorOutput

client = AsyncOpenAI(api_key=settings.openai_api_key)


class ResultFormatter:
    async def format(
        self,
        question: str,
        executor_output: SQLExecutorOutput,
    ) -> ResultFormatterOutput:
        # Generate NL summary only if results exist
        if executor_output.rows:
            nl_summary = await self._summarize(question, executor_output)
        else:
            nl_summary = "The query returned no results."

        return ResultFormatterOutput(
            table=executor_output.rows,
            columns=executor_output.columns,
            nl_summary=nl_summary,
            row_count=executor_output.row_count,
        )

    async def _summarize(self, question: str, data: SQLExecutorOutput) -> str:
        """Ask the LLM for a 1–2 sentence plain English summary of the result."""
        # Only send the first 10 rows to keep token usage low
        preview_rows = data.rows[:10]
        preview = "\n".join(
            str(dict(row)) for row in preview_rows
        )
        if data.row_count > 10:
            preview += f"\n... and {data.row_count - 10} more rows"

        prompt = (
            f"The user asked: \"{question}\"\n\n"
            f"The query returned {data.row_count} row(s):\n{preview}\n\n"
            f"Write 1–2 sentences summarizing the key insight from these results. "
            f"Be specific — mention actual values where relevant. "
            f"Do NOT say 'the query returned' — just state the insight directly."
        )

        response = await client.chat.completions.create(
            model=settings.openai_model,
            temperature=0.3,
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content.strip()


# Singleton
formatter = ResultFormatter()
