from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db
from app.memory.manager import MemoryManager


router = APIRouter(prefix="/memory", tags=["Memory"])


class MemoryStore(BaseModel):
    user_id: str
    content: str
    memory_type: str = "fact"
    importance: float = 0.5


class MemoryQuery(BaseModel):
    user_id: str
    query: str
    limit: int = 5


@router.post("/store")
async def store_memory(req: MemoryStore, db: AsyncSession = Depends(get_db)):
    manager = MemoryManager(db)
    mem = await manager.store_memory(
        user_id=req.user_id,
        content=req.content,
        memory_type=req.memory_type,
        importance=req.importance,
    )
    return {"id": mem.id, "stored": True}


@router.post("/recall")
async def recall_memory(req: MemoryQuery, db: AsyncSession = Depends(get_db)):
    manager = MemoryManager(db)
    memories = await manager.long_term.recall(req.user_id, req.query, limit=req.limit)
    return {"memories": memories}
