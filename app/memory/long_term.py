from __future__ import annotations
from app.database.repositories import MemoryRepository
from app.services.embeddings import embedding_service
import logfire


class LongTermMemory:
    """Persistent semantic memory stored in pgvector."""

    TYPES = ("preference", "fact", "conversation_summary", "document_ref", "semantic")

    def __init__(self, memory_repo: MemoryRepository):
        self.repo = memory_repo

    async def store(self, user_id: str, content: str, memory_type: str = "fact",
                    importance: float = 0.5, metadata: dict | None = None):
        with logfire.span("memory.long_term.store", memory_type=memory_type):
            embedding = await embedding_service.embed(content)
            return await self.repo.store(
                user_id=user_id,
                memory_type=memory_type,
                content=content,
                embedding=embedding,
                importance=importance,
                metadata=metadata,
            )

    async def recall(self, user_id: str, query: str, limit: int = 5) -> list[dict]:
        with logfire.span("memory.long_term.recall"):
            embedding = await embedding_service.embed(query)
            memories = await self.repo.search_by_vector(user_id, embedding, limit=limit)
            return [
                {"content": m.content, "type": m.memory_type, "importance": m.importance}
                for m in memories
            ]
