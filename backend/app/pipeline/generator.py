"""
Component 4: SQL Generator
Constructs a prompt with schema context + few-shot examples and calls OpenAI
to generate a SQL query. SELECT-only by prompt enforcement.
Outputs: SQLGeneratorOutput
"""

from openai import AsyncOpenAI

from app.config import settings
from app.schemas.pipeline import (
    Ambiguity,
    ExamplesRetrieverOutput,
    SchemaLinkerOutput,
    SQLGeneratorOutput,
)

client = AsyncOpenAI(api_key=settings.openai_api_key)

SYSTEM_PROMPT = """You are an expert SQL query generator. Your job is to convert natural language questions into valid {dialect} SQL queries.

STRICT RULES:
1. Only generate SELECT statements. NEVER generate INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, or any DDL/DML.
2. Always use exact table and column names from the schema provided.
3. If the user asks for something destructive or outside the schema, respond with: ERROR: <reason>
4. Add a LIMIT clause if the query could return many rows.
5. Be precise — do not guess at column names not in the schema.

DIALECT: {dialect}

{schema_context}
"""

FEW_SHOT_TEMPLATE = """
--- Few-Shot Examples ---
{examples}
--- End Examples ---
"""


class SQLGenerator:
    async def generate(
        self,
        question: str,
        schema_context: str,
        linker_output: SchemaLinkerOutput,
        examples_output: ExamplesRetrieverOutput,
        dialect: str | None = None,
        temperature: float | None = None,
        error_context: str | None = None,  # for self-healing retry
    ) -> SQLGeneratorOutput:
        dialect = dialect or settings.sql_dialect
        temperature = temperature if temperature is not None else settings.openai_temperature

        system = SYSTEM_PROMPT.format(dialect=dialect.upper(), schema_context=schema_context)

        # Build few-shot block
        few_shot_block = ""
        if examples_output.examples:
            ex_lines = []
            for ex in examples_output.examples:
                ex_lines.append(f"Q: {ex.question}\nSQL: {ex.sql}")
            few_shot_block = FEW_SHOT_TEMPLATE.format(examples="\n\n".join(ex_lines))

        # Build user message
        user_parts = []
        if few_shot_block:
            user_parts.append(few_shot_block)

        if linker_output.resolved_tables:
            user_parts.append(f"Relevant tables: {', '.join(linker_output.resolved_tables)}")
        if linker_output.resolved_columns:
            user_parts.append(f"Relevant columns: {', '.join(linker_output.resolved_columns)}")

        if error_context:
            user_parts.append(
                f"PREVIOUS ATTEMPT FAILED with error: {error_context}\n"
                f"Please fix the query and try again."
            )

        user_parts.append(f"Question: {question}")
        user_parts.append("Generate only the SQL query, then on a new line starting with 'Explanation:' give a one-sentence plain English explanation.")

        user_message = "\n\n".join(user_parts)

        response = await client.chat.completions.create(
            model=settings.openai_model,
            temperature=temperature,
            max_tokens=settings.openai_max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_message},
            ],
        )

        raw = response.choices[0].message.content or ""
        return self._parse_response(raw)

    def _parse_response(self, raw: str) -> SQLGeneratorOutput:
        """Split the model's output into SQL and explanation."""
        explanation = ""
        sql = raw.strip()

        if "Explanation:" in raw:
            parts = raw.split("Explanation:", 1)
            sql = parts[0].strip()
            explanation = parts[1].strip()

        # Strip markdown code fences if present (```sql ... ``` or ``` ... ```)
        if sql.startswith("```"):
            lines = sql.split("\n")
            sql = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:]).strip()

        # Strip common LLM label prefixes: "SQL:", "sql:", "Query:", etc.
        import re
        sql = re.sub(r"(?i)^\s*(sql|query)\s*:\s*", "", sql).strip()

        return SQLGeneratorOutput(sql=sql, explanation=explanation)


# Singleton
generator = SQLGenerator()
