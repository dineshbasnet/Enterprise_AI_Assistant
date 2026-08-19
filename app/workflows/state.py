from __future__ import annotations
from typing import Any
from pydantic import BaseModel, Field
from enum import Enum


class Intent(str, Enum):
    KNOWLEDGE = "knowledge"
    DOCUMENT = "document"
    SUPPORT = "support"
    FEEDBACK = "feedback"
    CONVERSATIONAL = "conversational"
    UNKNOWN = "unknown"


class GraphState(BaseModel):
    user_id: str = ""
    session_id: str = ""
    query: str = ""

    guardrail_passed: bool = True
    guardrail_reason: str = ""
    cleaned_query: str = ""

    intent: Intent = Intent.UNKNOWN
    confidence: float = 0.0
    reasoning: str = ""

    chat_history: list[dict] = []
    long_term_memories: list[dict] = []

    rewritten_query: str = ""

    retrieved_chunks: list[dict] = []
    reranked_chunks: list[dict] = []
    context: str = ""

    response: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
