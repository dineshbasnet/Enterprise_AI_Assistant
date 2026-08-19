from pydantic import BaseModel
from typing import Any
from enum import Enum


class Intent(str, Enum):
    KNOWLEDGE = "knowledge"
    DOCUMENT = "document"
    SUPPORT = "support"
    FEEDBACK = "feedback"
    CONVERSATIONAL = "conversational"
    UNKNOWN = "unknown"


class AgentState(BaseModel):
    user_id: str | None = None
    session_id: str | None = None
    query: str = ""
    intent: Intent = Intent.UNKNOWN
    confidence: float = 0.0
    reasoning: str = ""
    chat_history: list = []
    uploaded_files: list[str] = []
    ocr_result: dict[str, Any] = {}
    extracted_data: dict[str, Any] = {}
    rag_context: list = []
    form_schema: dict[str, Any] = {}
    ticket: dict[str, Any] | None = None
    sentiment: dict[str, Any] | None = None
    response: Any = None
