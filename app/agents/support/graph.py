from langgraph.graph import StateGraph, END

from .state import SupportState

from .nodes import retrieve_history, decision_node, answer_node, ticket_node

builder = StateGraph(SupportState)
builder.add_node("history", retrieve_history)
builder.add_node("decision", decision_node)
builder.add_node("answer", answer_node)
builder.add_node("ticket", ticket_node)

def router(state: SupportState) -> str:
    return state.action


builder.set_entry_point("history")
builder.add_edge("history", "decision")


builder.add_conditional_edges(
    "decision", router, {"answer": "answer", "ticket": "ticket"}
)

builder.add_edge("answer", END)
builder.add_edge("ticket", END)
graph = builder.compile()
