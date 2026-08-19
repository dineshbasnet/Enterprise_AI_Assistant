from .base_agent import BaseAgent
from .states import AgentState


class DocumentAgent(BaseAgent):
    async def execute(self, state: AgentState) -> AgentState:
        state.response = "Please upload a document using the /upload endpoint for processing."
        return state
