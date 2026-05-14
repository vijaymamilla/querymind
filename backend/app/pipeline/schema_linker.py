"""
Component 2: Schema Linker
Maps NL entities to actual table/column names using:
  - Live schema introspection from the database
  - Human-readable descriptions and synonyms from SchemaColumn admin records
Outputs: SchemaLinkerOutput
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.pipeline import Ambiguity, SchemaLinkerOutput


class SchemaLinker:
    async def link(
        self,
        question: str,
        tables_mentioned: list[str],
        columns_mentioned: list[str],
        db: AsyncSession,
    ) -> SchemaLinkerOutput:
        """
        Resolve NL mentions to schema entities.
        Also loads all column descriptions for prompt context.
        """
        # 1. Introspect live schema from pg_catalog
        schema_map = await self._introspect_schema(db)

        # 2. Load synonym/description mappings from admin table
        synonym_map = await self._load_synonyms(db)

        # 3. Resolve tables
        resolved_tables = []
        for mention in tables_mentioned:
            resolved = self._resolve(mention, list(schema_map.keys()), synonym_map)
            if resolved:
                resolved_tables.extend(resolved)

        # 4. Resolve columns and detect ambiguities
        resolved_columns = []
        ambiguities = []
        for mention in columns_mentioned:
            all_columns = [
                f"{table}.{col}"
                for table, cols in schema_map.items()
                for col in cols
            ]
            matches = self._resolve(mention, all_columns, synonym_map)
            if len(matches) > 1:
                ambiguities.append(Ambiguity(mention=mention, candidates=matches))
            elif matches:
                resolved_columns.extend(matches)

        return SchemaLinkerOutput(
            resolved_tables=list(set(resolved_tables)),
            resolved_columns=list(set(resolved_columns)),
            ambiguities=ambiguities,
        )

    async def get_schema_context(self, db: AsyncSession) -> str:
        """
        Returns a formatted schema string for the LLM prompt.
        Excludes columns marked as sensitive.
        """
        schema_map = await self._introspect_schema(db)
        descriptions = await self._load_descriptions(db)
        sensitive = await self._load_sensitive_columns(db)

        lines = ["-- Database Schema --"]
        for table, columns in schema_map.items():
            lines.append(f"\nTable: {table}")
            for col_name, col_type in columns.items():
                key = f"{table}.{col_name}"
                if key in sensitive:
                    continue
                desc = descriptions.get(key, "")
                desc_str = f"  -- {desc}" if desc else ""
                lines.append(f"  {col_name} {col_type}{desc_str}")

        return "\n".join(lines)

    async def _introspect_schema(self, db: AsyncSession) -> dict[str, dict[str, str]]:
        """Query pg_catalog to get all user tables and their columns."""
        result = await db.execute(
            text("""
                SELECT
                    t.table_name,
                    c.column_name,
                    c.data_type
                FROM information_schema.tables t
                JOIN information_schema.columns c
                    ON t.table_name = c.table_name
                    AND t.table_schema = c.table_schema
                WHERE t.table_schema = 'public'
                    AND t.table_type = 'BASE TABLE'
                    AND t.table_name NOT IN (
                        'schema_columns', 'few_shot_examples', 'query_logs',
                        'guardrail_config', 'model_config', 'alembic_version'
                    )
                ORDER BY t.table_name, c.ordinal_position
            """)
        )
        schema: dict[str, dict[str, str]] = {}
        for row in result.fetchall():
            table, col, dtype = row
            schema.setdefault(table, {})[col] = dtype
        return schema

    async def _load_synonyms(self, db: AsyncSession) -> dict[str, list[str]]:
        """Returns {synonym: ["table.column", ...]} mapping."""
        result = await db.execute(
            text("SELECT table_name, column_name, synonyms FROM schema_columns")
        )
        syn_map: dict[str, list[str]] = {}
        for table, col, synonyms in result.fetchall():
            for syn in (synonyms or []):
                syn_map.setdefault(syn.lower(), []).append(f"{table}.{col}")
        return syn_map

    async def _load_descriptions(self, db: AsyncSession) -> dict[str, str]:
        result = await db.execute(
            text("SELECT table_name, column_name, description FROM schema_columns WHERE description IS NOT NULL")
        )
        return {f"{t}.{c}": d for t, c, d in result.fetchall()}

    async def _load_sensitive_columns(self, db: AsyncSession) -> set[str]:
        result = await db.execute(
            text("SELECT table_name, column_name FROM schema_columns WHERE is_sensitive = true")
        )
        return {f"{t}.{c}" for t, c in result.fetchall()}

    def _resolve(self, mention: str, candidates: list[str], synonym_map: dict) -> list[str]:
        """Simple fuzzy match: exact → synonym → substring."""
        mention_lower = mention.lower()

        # Exact match
        exact = [c for c in candidates if c.lower() == mention_lower or c.lower().endswith(f".{mention_lower}")]
        if exact:
            return exact

        # Synonym lookup
        if mention_lower in synonym_map:
            return synonym_map[mention_lower]

        # Substring match (last resort)
        substr = [c for c in candidates if mention_lower in c.lower()]
        return substr


# Singleton
schema_linker = SchemaLinker()
