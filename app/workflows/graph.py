from langgraph.graph import StateGraph, END
from app.workflows.state import GraphState, Intent
from app.workflows.nodes import (
    guardrail_node, planner_node, memory_retrieval_node,
    query_rewriter_node, knowledge_retrieval_node, context_builder_node,
    llm_node, memory_update_node, support_node, document_node, feedback_node,
    route_after_guardrails, route_after_planner,
)

builder = StateGraph(GraphState)

builder.add_node("guardrails", guardrail_node)
builder.add_node("planner", planner_node)
builder.add_node("memory_retrieval", memory_retrieval_node)
builder.add_node("query_rewriter", query_rewriter_node)
builder.add_node("knowledge_retrieval", knowledge_retrieval_node)
builder.add_node("context_builder", context_builder_node)
builder.add_node("llm", llm_node)
builder.add_node("memory_update", memory_update_node)
builder.add_node("support", support_node)
builder.add_node("document", document_node)
builder.add_node("feedback", feedback_node)

builder.set_entry_point("guardrails")

builder.add_conditional_edges("guardrails", route_after_guardrails, {
    "planner": "planner",
    "__end__": END,
})

builder.add_conditional_edges("planner", route_after_planner, {
    "support": "support",
    "document": "document",
    "feedback": "feedback",
    "memory_retrieval": "memory_retrieval",
})

builder.add_edge("memory_retrieval", "query_rewriter")
builder.add_edge("query_rewriter", "knowledge_retrieval")
builder.add_edge("knowledge_retrieval", "context_builder")
builder.add_edge("context_builder", "llm")
builder.add_edge("llm", "memory_update")
builder.add_edge("memory_update", END)
builder.add_edge("support", END)
builder.add_edge("document", END)
builder.add_edge("feedback", END)

graph = builder.compile()
