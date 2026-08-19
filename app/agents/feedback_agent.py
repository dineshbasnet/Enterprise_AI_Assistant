from .base_agent import BaseAgent
from .states import AgentState


class FeedbackAgent(BaseAgent):
    async def execute(self, state: AgentState) -> AgentState:
        state.response = "Thank you for your feedback. It has been recorded."
        return state
