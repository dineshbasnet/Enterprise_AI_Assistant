from .base_agent import BaseAgent
from .states import AgentState
from app.core.llm import get_llm


class KnowledgeAgent(BaseAgent):
    async def execute(self, state: AgentState) -> AgentState:
        llm = get_llm(temperature=0.3)
        result = await llm.ainvoke([
            ("system", "You are a knowledgeable organizational assistant. Answer factual questions accurately."),
            ("human", state.query),
        ])
        state.response = result.content
        return state
