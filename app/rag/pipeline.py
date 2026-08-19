from __future__ import annotations
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.rag.vector_store import VectorStore, TextSplitter
from app.services.embeddings import rerank_service
import logfire


class RAGPipeline:
    def __init__(self, db: AsyncSession):
        self.vector_store = VectorStore(db)
        self.splitter = TextSplitter()

    async def ingest(self, document_id: str, text: str, metadata: dict | None = None) -> int:
        with logfire.span("rag.ingest", document_id=document_id):
            chunks = self.splitter.split(text)
            await self.vector_store.add_chunks(document_id, chunks, metadata)
            return len(chunks)

    async def retrieve(self, query: str, top_k: int = 10, rerank_top_n: int = 5) -> list[dict[str, Any]]:
        with logfire.span("rag.retrieve", query=query):
            candidates = await self.vector_store.similarity_search(query, limit=top_k)
            if not candidates:
                return []
            texts = [c["content"] for c in candidates]
            reranked = await rerank_service.rerank(query, texts, top_n=rerank_top_n)
            return [
                {**candidates[r["index"]], "rerank_score": r["score"]}
                for r in reranked
            ]

    def build_context(self, chunks: list[dict[str, Any]]) -> str:
        return "\n\n---\n\n".join(c["content"] for c in chunks)
