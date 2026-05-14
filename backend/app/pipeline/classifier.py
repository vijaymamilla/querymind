"""
Component 1: Query Classifier
Determines intent before any SQL is generated.
Outputs: ClassifierOutput
"""

import re
from app.schemas.pipeline import ClassifierOutput


# Keywords that signal each category
_TEMPORAL_PATTERNS = re.compile(
    r"\b(yesterday|today|last (week|month|quarter|year)|this (week|month|year)|"
    r"between|since|before|after|date|time|period|recent|latest)\b",
    re.IGNORECASE,
)
_AGGREGATE_PATTERNS = re.compile(
    r"\b(total|sum|average|avg|count|how many|maximum|minimum|max|min|"
    r"top \d+|bottom \d+|per|by|group)\b",
    re.IGNORECASE,
)
_JOIN_PATTERNS = re.compile(
    r"\b(with|and their|along with|including|joined|related|associated|"
    r"for each|per customer|per product|per order)\b",
    re.IGNORECASE,
)
_DESTRUCTIVE_PATTERNS = re.compile(
    r"\b(delete|remove|drop|update|change|modify|insert|add|create|alter|"
    r"truncate|reset)\b",
    re.IGNORECASE,
)


class QueryClassifier:
    """
    Rule-based + LLM-assisted classifier.
    For the MVP the rules cover most cases. Swap in an LLM call for higher accuracy.
    """

    async def classify(self, question: str) -> ClassifierOutput:
        question_lower = question.lower()

        # Block destructive intents immediately
        if _DESTRUCTIVE_PATTERNS.search(question_lower):
            return ClassifierOutput(
                query_type="UNSUPPORTED",
                confidence=0.95,
            )

        # Detect query type by priority
        if _TEMPORAL_PATTERNS.search(question_lower) and _AGGREGATE_PATTERNS.search(question_lower):
            query_type = "SELECT_TEMPORAL"
        elif _AGGREGATE_PATTERNS.search(question_lower):
            query_type = "SELECT_AGGREGATE"
        elif _JOIN_PATTERNS.search(question_lower):
            query_type = "SELECT_JOIN"
        else:
            query_type = "SELECT_SIMPLE"

        # Naive entity extraction — replace with NER or LLM for production
        tables_mentioned = self._extract_tables(question_lower)
        columns_mentioned = self._extract_columns(question_lower)

        return ClassifierOutput(
            query_type=query_type,
            tables_mentioned=tables_mentioned,
            columns_mentioned=columns_mentioned,
            confidence=0.8,
        )

    def _extract_tables(self, question: str) -> list[str]:
        """
        Placeholder: extract likely table names from the question.
        In production, match against the actual schema vocabulary.
        """
        # TODO: replace with schema-aware entity extraction
        return []

    def _extract_columns(self, question: str) -> list[str]:
        """
        Placeholder: extract likely column names from the question.
        """
        # TODO: replace with schema-aware entity extraction
        return []


# Singleton
classifier = QueryClassifier()
