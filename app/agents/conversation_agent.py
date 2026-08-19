from .base_agent import BaseAgent
from .states import AgentState
from app.core.llm import get_llm


class ConversationAgent(BaseAgent):
    async def execute(self, state: AgentState) -> AgentState:
        llm = get_llm(temperature=0.7)
        result = await llm.ainvoke([
            ("system", "You are a friendly AI assistant. Engage in natural conversation."),
            ("human", state.query),
        ])
        state.response = result.content
        return state
