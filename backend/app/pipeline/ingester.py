"""
Document Ingester
Uses Docling to parse PDFs/DOCX/HTML documents and indexes text chunks
into a Qdrant 'schema_docs' collection for schema-context retrieval.
"""

import uuid
from pathlib import Path

from docling.document_converter import DocumentConverter
from openai import AsyncOpenAI
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, PointIdsList, PointStruct, VectorParams

from app.config import settings

COLLECTION = "schema_docs"
VECTOR_SIZE = 1536  # text-embedding-3-small
CHUNK_SIZE = 400    # words per chunk
CHUNK_OVERLAP = 50  # word overlap between chunks


def _stable_uuid(doc_name: str, chunk_index: int) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{doc_name}:{chunk_index}"))


def _chunk_text(text: str) -> list[str]:
    words = text.split()
    chunks, i = [], 0
    while i < len(words):
        chunks.append(" ".join(words[i : i + CHUNK_SIZE]))
        i += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


class DocumentIngester:
    def __init__(self):
        self._client: AsyncQdrantClient | None = None
        self._openai = AsyncOpenAI(api_key=settings.openai_api_key)
        self._converter = DocumentConverter()

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

    async def ingest(self, file_path: str | Path, doc_name: str) -> int:
        """
        Parse a document with Docling and index its chunks into Qdrant.
        Returns the number of chunks indexed.
        """
        result = self._converter.convert(str(file_path))
        markdown = result.document.export_to_markdown()

        chunks = _chunk_text(markdown)
        if not chunks:
            return 0

        await self._ensure_collection()
        client = self._get_client()

        points = []
        for i, chunk in enumerate(chunks):
            vector = await self._embed(chunk)
            points.append(
                PointStruct(
                    id=_stable_uuid(doc_name, i),
                    vector=vector,
                    payload={"text": chunk, "doc_name": doc_name, "chunk_index": i},
                )
            )

        await client.upsert(collection_name=COLLECTION, points=points)
        return len(chunks)

    async def delete_document(self, doc_name: str):
        """Remove all chunks belonging to a document."""
        client = self._get_client()
        await client.delete(
            collection_name=COLLECTION,
            points_selector=PointIdsList(
                points=[
                    _stable_uuid(doc_name, i)
                    for i in range(10_000)  # generous upper bound
                ]
            ),
        )

    async def search(self, query: str, top_k: int = 3) -> list[dict]:
        """Retrieve relevant document chunks for a query."""
        client = self._get_client()
        try:
            count_resp = await client.count(collection_name=COLLECTION, exact=True)
            if count_resp.count == 0:
                return []
        except Exception:
            return []

        vector = await self._embed(query)
        results = await client.query_points(
            collection_name=COLLECTION,
            query=vector,
            limit=top_k,
            with_payload=True,
        )
        return [
            {
                "text": hit.payload["text"],
                "doc_name": hit.payload["doc_name"],
                "score": hit.score,
            }
            for hit in results.points
        ]


# Singleton
ingester = DocumentIngester()
