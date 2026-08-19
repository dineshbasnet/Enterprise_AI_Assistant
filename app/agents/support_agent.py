from .base_agent import BaseAgent
from .support.graph import graph
from .support.state import SupportState

class SupportAgent(BaseAgent):

    async def execute(self, state:SupportState):

        return await graph.ainvoke(state)