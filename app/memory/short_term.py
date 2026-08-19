from __future__ import annotations
from app.database.repositories import ChatRepository
import logfire


class ShortTermMemory:
    """Sliding window over recent messages + automatic summarization."""

    def __init__(self, chat_repo: ChatRepository, window_size: int = 20):
        self.chat_repo = chat_repo
        self.window_size = window_size

    async def get_context(self, session_id: str) -> list[dict]:
        with logfire.span("memory.short_term.get_context"):
            messages = await self.chat_repo.get_history(session_id, limit=self.window_size)
            return [{"role": m.role, "content": m.content} for m in messages]

    async def add(self, session_id: str, role: str, content: str):
        await self.chat_repo.add_message(session_id, role, content)

    async def summarize(self, session_id: str) -> str:
        from app.core.llm import get_llm
        messages = await self.chat_repo.get_history(session_id, limit=50)
        if len(messages) < 10:
            return ""
        text = "\n".join(f"{m.role}: {m.content}" for m in messages)
        llm = get_llm()
        result = await llm.ainvoke([
            ("system", "Summarize this conversation concisely, preserving key facts and decisions."),
            ("human", text),
        ])
        return result.content
