"""
Component 3: Examples Retriever
Embeds the user query and retrieves top-k similar (question → SQL) pairs
from Qdrant for few-shot prompting.
Outputs: ExamplesRetrieverOutput
"""

from openai import AsyncOpenAI
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, PointIdsList
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.config import settings
from app.schemas.pipeline import ExamplesRetrieverOutput, FewShotPair

COLLECTION = "few_shot_examples"
VECTOR_SIZE = 1536  # text-embedding-3-small


class ExamplesRetriever:
    def __init__(self):
        self._client: AsyncQdrantClient | None = None
        self._openai = AsyncOpenAI(api_key=settings.openai_api_key)

    def _get_client(self) -> AsyncQdrantClient:
        if self._client is None:
            kwargs = {"url": settings.qdrant_url}
            if settings.qdrant_api_key:
                kwargs["api_key"] = settings.qdrant_api_key
            self._client = AsyncQdrantClient(**kwargs)
        return self._client

    async def _ensure_collection(self):
        client = self._get_client()
        existing = await client.get_collections()
        names = {c.name for c in existing.collections}
        if COLLECTION not in names:
            await client.create_collection(
                collection_name=COLLECTION,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )

    async def _embed(self, text: str) -> list[float]:
        resp = await self._openai.embeddings.create(
            model="text-embedding-3-small",
            input=text,
        )
        return resp.data[0].embedding

    async def retrieve(self, question: str, top_k: int = 4) -> ExamplesRetrieverOutput:
        """Embed the question and return the top-k most similar examples."""
        client = self._get_client()

        # Return empty if collection doesn't exist or has no points yet
        try:
            count_resp = await client.count(collection_name=COLLECTION, exact=True)
            if count_resp.count == 0:
                return ExamplesRetrieverOutput(examples=[])
            limit = min(top_k, count_resp.count)
        except Exception:
            return ExamplesRetrieverOutput(examples=[])

        vector = await self._embed(question)
        results = await client.query_points(
            collection_name=COLLECTION,
            query=vector,
            limit=limit,
            with_payload=True,
        )

        examples = [
            FewShotPair(
                question=hit.payload["question"],
                sql=hit.payload["sql"],
                score=hit.score,
            )
            for hit in results.points
        ]
        return ExamplesRetrieverOutput(examples=examples)

    async def upsert_example(self, example_id: int, question: str, sql: str, query_type: str):
        """Add or update a single example in Qdrant."""
        await self._ensure_collection()
        client = self._get_client()
        vector = await self._embed(question)
        await client.upsert(
            collection_name=COLLECTION,
            points=[
                PointStruct(
                    id=example_id,
                    vector=vector,
                    payload={"question": question, "sql": sql, "query_type": query_type},
                )
            ],
        )

    async def delete_example(self, example_id: int):
        """Remove an example from Qdrant."""
        client = self._get_client()
        await client.delete(
            collection_name=COLLECTION,
            points_selector=PointIdsList(points=[example_id]),
        )

    async def sync_from_db(self, db: AsyncSession):
        """Full re-sync: load all examples from Postgres into Qdrant."""
        result = await db.execute(
            text("SELECT id, question, sql, query_type FROM few_shot_examples")
        )
        rows = result.fetchall()
        if not rows:
            return

        await self._ensure_collection()
        client = self._get_client()

        points = []
        for row in rows:
            vector = await self._embed(row[1])
            points.append(
                PointStruct(
                    id=row[0],
                    vector=vector,
                    payload={"question": row[1], "sql": row[2], "query_type": row[3]},
                )
            )

        await client.upsert(collection_name=COLLECTION, points=points)


# Singleton
retriever = ExamplesRetriever()
