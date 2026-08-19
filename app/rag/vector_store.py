from __future__ import annotations
from typing import Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.embeddings import embedding_service
from app.database.repositories import DocumentRepository
from app.database.models import DocumentChunk
import uuid
import logfire


class TextSplitter:
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64):
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def split(self, text: str) -> list[str]:
        return self._splitter.split_text(text)


class VectorStore:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_chunks(self, document_id: str, chunks: list[str], metadata: dict | None = None) -> None:
        with logfire.span("vector_store.add_chunks", document_id=document_id, count=len(chunks)):
            embeddings = await embedding_service.embed_batch(chunks)
            for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
                obj = DocumentChunk(
                    id=str(uuid.uuid4()),
                    document_id=document_id,
                    content=chunk,
                    chunk_index=i,
                    embedding=emb,
                    metadata=metadata or {},
                )
                self.db.add(obj)
            await self.db.commit()

    async def similarity_search(self, query: str, limit: int = 5, metadata_filter: dict | None = None) -> list[dict[str, Any]]:
        from sqlalchemy import select
        from app.database.models import DocumentChunk
        with logfire.span("vector_store.similarity_search"):
            query_emb = await embedding_service.embed(query)
            stmt = (
                select(DocumentChunk)
                .order_by(DocumentChunk.embedding.l2_distance(query_emb))
                .limit(limit)
            )
            result = await self.db.execute(stmt)
            rows = result.scalars().all()
            return [{"id": r.id, "content": r.content, "metadata": r.metadata, "document_id": r.document_id} for r in rows]
