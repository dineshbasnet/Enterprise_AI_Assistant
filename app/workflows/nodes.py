from __future__ import annotations
from typing import Any
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from app.workflows.state import GraphState, Intent
from app.core.llm import get_llm
from app.services.guardrails import Guardrails
from app.memory.manager import MemoryManager
from app.rag.pipeline import RAGPipeline
import logfire


guardrails = Guardrails()


async def guardrail_node(state: GraphState) -> dict:
    with logfire.span("node.guardrails"):
        result = await guardrails.check_input(state.query)
        if not result.passed:
            return {"guardrail_passed": False, "guardrail_reason": result.reason, "response": result.reason}
        return {"guardrail_passed": True, "cleaned_query": result.modified_input or state.query}


async def planner_node(state: GraphState) -> dict:
    with logfire.span("node.planner"):
        from pydantic import BaseModel, Field
        from app.workflows.state import Intent

        class IntentOutput(BaseModel):
            intent: Intent
            confidence: float = Field(ge=0, le=1)
            reasoning: str

        llm = get_llm(temperature=0.0).with_structured_output(IntentOutput)
        result = llm.invoke([
            ("system", "Classify the user query into one intent: knowledge, document, support, feedback, conversational, unknown."),
            ("human", state.cleaned_query or state.query),
        ])
        return {"intent": result.intent, "confidence": result.confidence, "reasoning": result.reasoning}


async def memory_retrieval_node(state: GraphState) -> dict:
    with logfire.span("node.memory_retrieval"):
        from app.database.connection import async_session
        async with async_session() as db:
            manager = MemoryManager(db)
            ctx = await manager.get_full_context(state.user_id, state.session_id, state.query)
        return {
            "chat_history": ctx["recent_messages"],
            "long_term_memories": ctx["long_term_memories"],
        }


async def query_rewriter_node(state: GraphState) -> dict:
    with logfire.span("node.query_rewriter"):
        if not state.chat_history:
            return {"rewritten_query": state.cleaned_query or state.query}
        history_text = "\n".join(f"{m['role']}: {m['content']}" for m in state.chat_history[-6:])
        llm = get_llm(temperature=0.0)
        result = await llm.ainvoke([
            ("system", "Rewrite the user query to be self-contained given the conversation history. Return only the rewritten query."),
            ("human", f"History:\n{history_text}\n\nQuery: {state.query}"),
        ])
        return {"rewritten_query": result.content.strip()}


async def knowledge_retrieval_node(state: GraphState) -> dict:
    with logfire.span("node.knowledge_retrieval"):
        from app.database.connection import async_session
        async with async_session() as db:
            pipeline = RAGPipeline(db)
            chunks = await pipeline.retrieve(state.rewritten_query or state.query, top_k=10, rerank_top_n=5)
        return {"retrieved_chunks": chunks, "reranked_chunks": chunks}


async def context_builder_node(state: GraphState) -> dict:
    with logfire.span("node.context_builder"):
        memory_text = ""
        if state.long_term_memories:
            memory_text = "Relevant memories:\n" + "\n".join(m["content"] for m in state.long_term_memories) + "\n\n"
        rag_text = ""
        if state.reranked_chunks:
            rag_text = "Retrieved context:\n" + "\n\n---\n\n".join(c["content"] for c in state.reranked_chunks)
        return {"context": memory_text + rag_text}


async def llm_node(state: GraphState) -> dict:
    with logfire.span("node.llm", intent=state.intent):
        llm = get_llm(temperature=0.3)
        messages: list[Any] = [
            SystemMessage(content=(
                "You are a helpful organizational AI assistant.\n"
                + (f"Context:\n{state.context}\n" if state.context else "")
            ))
        ]
        for m in state.chat_history[-10:]:
            if m["role"] == "user":
                messages.append(HumanMessage(content=m["content"]))
            elif m["role"] == "assistant":
                messages.append(AIMessage(content=m["content"]))
        messages.append(HumanMessage(content=state.query))
        result = await llm.ainvoke(messages)
        return {"response": result.content}


async def memory_update_node(state: GraphState) -> dict:
    with logfire.span("node.memory_update"):
        if state.response and state.user_id and state.session_id:
            from app.database.connection import async_session
            async with async_session() as db:
                manager = MemoryManager(db)
                await manager.save_interaction(state.session_id, state.query, state.response)
        return {}


async def support_node(state: GraphState) -> dict:
    with logfire.span("node.support"):
        from app.agents.support.graph import graph
        from app.agents.support.state import SupportState, Ticket
        support_state = SupportState(
            user_id=state.user_id,
            session_id=state.session_id,
            query=state.query,
            chat_history=[f"{m['role']}: {m['content']}" for m in state.chat_history],
        )
        result = await graph.ainvoke(support_state)
        return {"response": result.get("response", "Support request processed.")}


async def document_node(state: GraphState) -> dict:
    with logfire.span("node.document"):
        return {"response": "Please upload a document using the /upload endpoint for processing."}


async def feedback_node(state: GraphState) -> dict:
    with logfire.span("node.feedback"):
        return {"response": "Thank you for your feedback. It has been recorded."}


def route_after_guardrails(state: GraphState) -> str:
    return "planner" if state.guardrail_passed else "__end__"


def route_after_planner(state: GraphState) -> str:
    return {
        Intent.SUPPORT: "support",
        Intent.DOCUMENT: "document",
        Intent.FEEDBACK: "feedback",
    }.get(state.intent, "memory_retrieval")
