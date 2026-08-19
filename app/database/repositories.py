from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.database.models import ChatMessage, Session, User, SupportTicket, LongTermMemory, Document, DocumentChunk
import uuid


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create(self, user_id: str) -> User:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            user = User(id=user_id, email=f"{user_id}@placeholder.local")
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
        return user


class SessionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create(self, session_id: str, user_id: str) -> Session:
        result = await self.db.execute(select(Session).where(Session.id == session_id))
        session = result.scalar_one_or_none()
        if not session:
            session = Session(id=session_id, user_id=user_id)
            self.db.add(session)
            await self.db.commit()
            await self.db.refresh(session)
        return session


class ChatRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_message(self, session_id: str, role: str, content: str) -> ChatMessage:
        msg = ChatMessage(id=str(uuid.uuid4()), session_id=session_id, role=role, content=content)
        self.db.add(msg)
        await self.db.commit()
        return msg

    async def get_history(self, session_id: str, limit: int = 20) -> list[ChatMessage]:
        result = await self.db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(desc(ChatMessage.created_at))
            .limit(limit)
        )
        return list(reversed(result.scalars().all()))


class TicketRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_id: str, session_id: str, description: str,
                     department: str = "General", priority: str = "MEDIUM") -> SupportTicket:
        ticket = SupportTicket(
            id=str(uuid.uuid4()),
            user_id=user_id,
            session_id=session_id,
            description=description,
            department=department,
            priority=priority,
        )
        self.db.add(ticket)
        await self.db.commit()
        await self.db.refresh(ticket)
        return ticket

    async def get_by_user(self, user_id: str) -> list[SupportTicket]:
        result = await self.db.execute(
            select(SupportTicket).where(SupportTicket.user_id == user_id)
        )
        return result.scalars().all()


class DocumentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_id: str, filename: str, file_path: str, mime_type: str) -> Document:
        doc = Document(
            id=str(uuid.uuid4()),
            user_id=user_id,
            filename=filename,
            file_path=file_path,
            mime_type=mime_type,
        )
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)
        return doc

    async def update_status(self, doc_id: str, status: str):
        result = await self.db.execute(select(Document).where(Document.id == doc_id))
        doc = result.scalar_one_or_none()
        if doc:
            doc.status = status
            await self.db.commit()

    async def get_by_user(self, user_id: str) -> list[Document]:
        result = await self.db.execute(select(Document).where(Document.user_id == user_id))
        return result.scalars().all()


class MemoryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def store(self, user_id: str, memory_type: str, content: str,
                    embedding: list[float] | None = None, importance: float = 0.5,
                    metadata: dict | None = None) -> LongTermMemory:
        mem = LongTermMemory(
            id=str(uuid.uuid4()),
            user_id=user_id,
            memory_type=memory_type,
            content=content,
            embedding=embedding,
            importance=importance,
            metadata=metadata or {},
        )
        self.db.add(mem)
        await self.db.commit()
        await self.db.refresh(mem)
        return mem

    async def search_by_vector(self, user_id: str, embedding: list[float], limit: int = 5) -> list[LongTermMemory]:
        result = await self.db.execute(
            select(LongTermMemory)
            .where(LongTermMemory.user_id == user_id)
            .order_by(LongTermMemory.embedding.l2_distance(embedding))
            .limit(limit)
        )
        return result.scalars().all()
