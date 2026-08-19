from sqlalchemy import Column, String, Float, Text, DateTime, ForeignKey, Boolean, Integer
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector
from datetime import datetime
import uuid


class Base(DeclarativeBase):
    pass


def _uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    email = Column(String, unique=True, nullable=False)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    sessions = relationship("Session", back_populates="user")
    memories = relationship("LongTermMemory", back_populates="user")


class Session(Base):
    __tablename__ = "sessions"
    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = relationship("User", back_populates="sessions")
    messages = relationship("ChatMessage", back_populates="session")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    session_id = Column(UUID(as_uuid=False), ForeignKey("sessions.id"), nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    session = relationship("Session", back_populates="messages")


class Document(Base):
    __tablename__ = "documents"
    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"))
    filename = Column(String, nullable=False)
    file_path = Column(String)
    mime_type = Column(String)
    status = Column(String, default="pending")
    extra_metadata = Column("metadata", JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    chunks = relationship("DocumentChunk", back_populates="document")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    document_id = Column(UUID(as_uuid=False), ForeignKey("documents.id"), nullable=False)
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer)
    embedding = Column(Vector(1024))
    extra_metadata = Column("metadata", JSONB, default={})
    document = relationship("Document", back_populates="chunks")


class SupportTicket(Base):
    __tablename__ = "support_tickets"
    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"))
    session_id = Column(UUID(as_uuid=False), ForeignKey("sessions.id"))
    department = Column(String)
    priority = Column(String, default="MEDIUM")
    status = Column(String, default="OPEN")
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class LongTermMemory(Base):
    __tablename__ = "long_term_memories"
    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    memory_type = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1024))
    importance = Column(Float, default=0.5)
    extra_metadata = Column("metadata", JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="memories")
