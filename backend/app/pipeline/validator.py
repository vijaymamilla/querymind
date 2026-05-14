"""
Component 5: SQL Validator
- Syntax check via sqlglot
- Guardrails: block destructive statements
- Schema check: verify tables/columns exist
- Auto-append LIMIT if missing
Outputs: SQLValidatorOutput
"""

import re
import sqlglot
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.config import settings
from app.schemas.pipeline import SQLValidatorOutput

DESTRUCTIVE_KEYWORDS = {"drop", "delete", "update", "insert", "truncate", "alter", "create", "replace"}


class SQLValidator:
    async def validate(
        self,
        sql: str,
        db: AsyncSession,
        max_rows: int | None = None,
    ) -> SQLValidatorOutput:
        errors: list[str] = []
        sanitized = sql.strip().rstrip(";")

        # 1. Guardrails: block destructive keywords
        destructive = self._check_destructive(sanitized)
        if destructive:
            return SQLValidatorOutput(
                valid=False,
                sanitized_sql=sanitized,
                errors=[f"Blocked: query contains forbidden keyword '{destructive}'"],
            )

        # 2. Syntax check via sqlglot
        syntax_errors = self._check_syntax(sanitized)
        errors.extend(syntax_errors)

        # 3. Schema check: verify referenced tables exist
        schema_errors = await self._check_schema(sanitized, db)
        errors.extend(schema_errors)

        if errors:
            return SQLValidatorOutput(valid=False, sanitized_sql=sanitized, errors=errors)

        # 4. Append LIMIT if not present
        limit = max_rows or settings.sql_max_rows
        sanitized = self._ensure_limit(sanitized, limit)

        return SQLValidatorOutput(valid=True, sanitized_sql=sanitized, errors=[])

    def _check_destructive(self, sql: str) -> str | None:
        """Return the offending keyword if found, else None."""
        tokens = re.findall(r"\b\w+\b", sql.lower())
        for token in tokens:
            if token in DESTRUCTIVE_KEYWORDS:
                return token
        return None

    def _check_syntax(self, sql: str) -> list[str]:
        """Parse with sqlglot (postgres dialect) and return any parse errors."""
        try:
            statements = sqlglot.parse(
                sql,
                read="postgres",
                error_level=sqlglot.ErrorLevel.RAISE,
            )
            if not statements or statements[0] is None:
                return ["Empty or unrecognized SQL statement"]
            return []
        except Exception as e:
            return [f"Syntax error: {e}"]

    async def _check_schema(self, sql: str, db: AsyncSession) -> list[str]:
        """
        Verify that tables referenced in the SQL actually exist.
        Uses sqlglot AST to extract only real FROM/JOIN table names — avoids
        false positives from functions like EXTRACT(YEAR FROM col).
        """
        try:
            # Use sqlglot AST to find actual table references (not function keywords)
            try:
                statements = sqlglot.parse(sql, read="postgres")
                mentioned = set()
                for stmt in statements:
                    if stmt is None:
                        continue
                    for table in stmt.find_all(sqlglot.exp.Table):
                        name = table.name
                        if name:
                            mentioned.add(name.lower())
            except Exception:
                # Fall back to a conservative regex that skips function FROM clauses
                table_refs = re.findall(
                    r"(?<!\()\bfrom\s+([a-zA-Z_]\w*)|\bjoin\s+([a-zA-Z_]\w*)",
                    sql, re.IGNORECASE,
                )
                mentioned = {t for pair in table_refs for t in pair if t}

            if not mentioned:
                return []

            result = await db.execute(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'public'"
                )
            )
            existing = {row[0].lower() for row in result.fetchall()}

            missing = [t for t in mentioned if t.lower() not in existing]
            if missing:
                return [f"Table(s) not found in schema: {', '.join(missing)}"]
            return []
        except Exception as e:
            return [f"Schema check failed: {e}"]

    def _ensure_limit(self, sql: str, limit: int) -> str:
        """Append LIMIT N if the query has none."""
        if re.search(r"\blimit\b", sql, re.IGNORECASE):
            return sql
        return f"{sql}\nLIMIT {limit}"


# Singleton
validator = SQLValidator()
