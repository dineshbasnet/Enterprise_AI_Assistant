from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.repositories import ChatRepository, MemoryRepository
from app.memory.short_term import ShortTermMemory
from app.memory.long_term import LongTermMemory


class MemoryManager:
    def __init__(self, db: AsyncSession):
        chat_repo = ChatRepository(db)
        memory_repo = MemoryRepository(db)
        self.short_term = ShortTermMemory(chat_repo)
        self.long_term = LongTermMemory(memory_repo)

    async def get_full_context(self, user_id: str, session_id: str, query: str) -> dict:
        recent = await self.short_term.get_context(session_id)
        long_term = await self.long_term.recall(user_id, query, limit=5)
        return {"recent_messages": recent, "long_term_memories": long_term}

    async def save_interaction(self, session_id: str, user_query: str, assistant_response: str):
        await self.short_term.add(session_id, "user", user_query)
        await self.short_term.add(session_id, "assistant", assistant_response)

    async def store_memory(self, user_id: str, content: str, memory_type: str = "fact",
                           importance: float = 0.5, metadata: dict | None = None):
        return await self.long_term.store(user_id, content, memory_type, importance, metadata)
