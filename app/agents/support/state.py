from typing import Optional
from pydantic import BaseModel


class Ticket(BaseModel):
    ticket_id: Optional[str] = None
    department: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None


class SupportState(BaseModel):

    # User information
    user_id: str
    session_id: str

    # User query
    query: str

    # Conversation history
    chat_history: list = []

    # Decision returned by LLM
    action: Optional[str] = None
    reasoning: Optional[str] = None

    # Ticket
    ticket: Ticket = Ticket()

    # Final response
    response: Optional[str] = None