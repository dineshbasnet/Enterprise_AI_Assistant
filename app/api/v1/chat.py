from fastapi import APIRouter
from pydantic import BaseModel
from app.agents.orchestrator import AgentOrchestrator

router = APIRouter(prefix="/chat", tags=["Chat"])
orchestrator = AgentOrchestrator()


class ChatRequest(BaseModel):
    user_id: str = "anonymous"
    session_id: str = "default"
    query: str


class ChatResponse(BaseModel):
    response: str
    intent: str = ""
    confidence: float = 0.0


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    result = await orchestrator.route(
        query=request.query,
        user_id=request.user_id,
        session_id=request.session_id,
    )
    return ChatResponse(**result)
