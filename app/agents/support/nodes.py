import uuid
from app.core.llm import get_llm
from .prompts import SUPPORT_DECISION_PROMPT
from .decision import SupportDecision
import logfire


async def retrieve_history(state):
    return state


async def decision_node(state):
    with logfire.span("support.decision"):
        llm = get_llm(temperature=0.0).with_structured_output(SupportDecision)
        result = llm.invoke([
            ("system", SUPPORT_DECISION_PROMPT),
            ("human", state.query),
        ])
        state.action = result.action
        state.reasoning = result.reasoning
        return state


async def answer_node(state):
    with logfire.span("support.answer"):
        llm = get_llm(temperature=0.3)
        result = await llm.ainvoke([
            ("system", "You are a helpful support agent. Answer the user's question concisely."),
            ("human", state.query),
        ])
        state.response = result.content
        return state


async def ticket_node(state):
    with logfire.span("support.ticket"):
        state.ticket.ticket_id = str(uuid.uuid4())
        state.ticket.department = "IT"
        state.ticket.priority = "HIGH"
        state.ticket.status = "OPEN"
        state.response = f"Support ticket {state.ticket.ticket_id} created successfully."
        return state
