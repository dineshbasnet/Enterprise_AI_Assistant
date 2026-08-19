"""initial tables

Revision ID: 001
Revises:
Create Date: 2026-07-27
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("email", sa.String, unique=True, nullable=False),
        sa.Column("name", sa.String),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "sessions",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "chat_messages",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("session_id", UUID(as_uuid=False), sa.ForeignKey("sessions.id"), nullable=False),
        sa.Column("role", sa.String, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "documents",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=False), sa.ForeignKey("users.id")),
        sa.Column("filename", sa.String, nullable=False),
        sa.Column("file_path", sa.String),
        sa.Column("mime_type", sa.String),
        sa.Column("status", sa.String, server_default="pending"),
        sa.Column("metadata", JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "document_chunks",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("document_id", UUID(as_uuid=False), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("chunk_index", sa.Integer),
        sa.Column("embedding", Vector(1024)),
        sa.Column("metadata", JSONB, server_default="{}"),
    )

    op.create_table(
        "support_tickets",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=False), sa.ForeignKey("users.id")),
        sa.Column("session_id", UUID(as_uuid=False), sa.ForeignKey("sessions.id")),
        sa.Column("department", sa.String),
        sa.Column("priority", sa.String, server_default="MEDIUM"),
        sa.Column("status", sa.String, server_default="OPEN"),
        sa.Column("description", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "long_term_memories",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("memory_type", sa.String, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("embedding", Vector(1024)),
        sa.Column("importance", sa.Float, server_default="0.5"),
        sa.Column("metadata", JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("long_term_memories")
    op.drop_table("support_tickets")
    op.drop_table("document_chunks")
    op.drop_table("documents")
    op.drop_table("chat_messages")
    op.drop_table("sessions")
    op.drop_table("users")
