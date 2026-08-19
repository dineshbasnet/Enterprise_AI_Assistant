from pydantic import BaseModel, Field
from app.workflows.graph import graph
from app.workflows.state import GraphState
import logfire


class AgentOrchestrator:
    """Routes all requests through the main LangGraph workflow."""

    async def route(self, query: str, user_id: str = "", session_id: str = "") -> dict:
        with logfire.span("orchestrator.route", query=query[:100]):
            state = GraphState(
                user_id=user_id or "anonymous",
                session_id=session_id or "default",
                query=query,
            )
            result = await graph.ainvoke(state)
            return {
                "response": result.get("response", ""),
                "intent": result.get("intent", "unknown"),
                "confidence": result.get("confidence", 0.0),
            }
