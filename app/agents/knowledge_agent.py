

from __future__ import annotations

import logging
from typing import List

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.base_agent import BaseAgent
from app.agents.state import AgentState
from app.core.llm import get_llm
from app.services.rag_service import RAGService, RetrievedChunk

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants — tune these empirically; do NOT hard-code in the orchestrator
# ---------------------------------------------------------------------------

# Minimum rerank score for a chunk to survive into the context window.
# Chunks below this are too semantically distant to be useful and would
# hallucination-pad the prompt.
RERANK_THRESHOLD: float = 0.30

# Number of chunks to pull from pgvector before reranking.
# More candidates = better recall; reranking then narrows to quality.
TOP_K_RETRIEVAL: int = 8

# Number of chunks kept after reranking.
TOP_K_RERANK: int = 3

# If the best rerank score after filtering is below this, the agent treats
# the query as out-of-scope and returns a fallback instead of hallucinating.
CONFIDENCE_FLOOR: float = 0.45

# Maximum characters allowed in a single query string.
MAX_QUERY_LENGTH: int = 1_000


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are the Knowledge Agent for an organizational AI assistant.

Your job is to answer the user's question using ONLY the context passages
provided below.  Do not use any prior knowledge or make up information.

Rules:
- If the context does not contain enough information to answer, say:
  "I don't have enough information in the knowledge base to answer that."
- Always cite which passage(s) your answer is based on using [Source N] tags.
- Keep answers concise and factual.
- Do not speculate beyond what the passages state.

Context passages:
{context}
"""


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class KnowledgeAgent(BaseAgent):
    """
    Retrieval-Augmented Generation agent.

    Depends on RAGService for embedding + vector search + reranking.
    Sets state.confidence so the orchestrator can decide whether to
    escalate to the Support Agent.
    """

    def __init__(self) -> None:
        self._rag = RAGService()

    # ------------------------------------------------------------------
    # Public interface required by BaseAgent
    # ------------------------------------------------------------------

    async def execute(self, state: AgentState) -> AgentState:
        """
        Run the full RAG pipeline and update AgentState in place.
        Always returns a valid state — never raises to the orchestrator.
        """
        state.agent_name = "knowledge_agent"

        # ── 1. Validate input ──────────────────────────────────────────
        query = (state.query or "").strip()
        if not query:
            return self._fail(state, "Query is empty.")
        if len(query) > MAX_QUERY_LENGTH:
            return self._fail(
                state,
                f"Query exceeds maximum length of {MAX_QUERY_LENGTH} characters.",
            )

        try:
            # ── 2. Retrieve candidate chunks from pgvector ─────────────
            chunks: List[RetrievedChunk] = await self._rag.retrieve(
                query=query,
                top_k=TOP_K_RETRIEVAL,
            )

            if not chunks:
                logger.info("KnowledgeAgent: no chunks retrieved for query='%s'", query[:80])
                return self._out_of_scope(state)

            # ── 3. Rerank and filter ───────────────────────────────────
            ranked: List[RetrievedChunk] = await self._rag.rerank(
                query=query,
                chunks=chunks,
                top_k=TOP_K_RERANK,
            )

            # Drop anything below the rerank threshold
            surviving = [c for c in ranked if c.rerank_score >= RERANK_THRESHOLD]

            if not surviving:
                logger.info(
                    "KnowledgeAgent: all chunks below rerank threshold (%.2f) for query='%s'",
                    RERANK_THRESHOLD,
                    query[:80],
                )
                return self._out_of_scope(state)

            # ── 4. Confidence score (used by orchestrator for routing) ─
            # We use the top chunk's rerank score as the confidence signal.
            # The orchestrator compares this against settings.CONFIDENCE_THRESHOLD.
            confidence: float = surviving[0].rerank_score
            state.confidence = confidence

            if confidence < CONFIDENCE_FLOOR:
                # Knowledge base has something but it's too weak to trust.
                # Return low confidence so the orchestrator can escalate.
                logger.info(
                    "KnowledgeAgent: low confidence (%.2f) — returning partial context",
                    confidence,
                )

            # ── 5. Assemble context string ─────────────────────────────
            context_blocks: List[str] = []
            for i, chunk in enumerate(surviving, start=1):
                source_label = chunk.metadata.get("source", f"Document {i}")
                context_blocks.append(
                    f"[Source {i}] ({source_label})\n{chunk.text}"
                )
            context_str = "\n\n---\n\n".join(context_blocks)

            # ── 6. LLM generation ──────────────────────────────────────
            llm = get_llm(temperature=0.1)  # low temp = more factual
            messages = [
                SystemMessage(content=SYSTEM_PROMPT.format(context=context_str)),
                HumanMessage(content=query),
            ]

            result = await llm.ainvoke(messages)
            answer: str = result.content.strip()

            # ── 7. Build source list for the frontend to display ───────
            sources = [
                {
                    "index": i,
                    "source": c.metadata.get("source", "Unknown"),
                    "page": c.metadata.get("page"),
                    "rerank_score": round(c.rerank_score, 4),
                    "chunk_id": c.chunk_id,
                }
                for i, c in enumerate(surviving, start=1)
            ]

            # ── 8. Update state ────────────────────────────────────────
            state.response = answer
            state.sources = sources
            state.error = None

            logger.info(
                "KnowledgeAgent: answered query='%s...' confidence=%.2f sources=%d",
                query[:60],
                confidence,
                len(sources),
            )

        except Exception as exc:  # noqa: BLE001
            # Log the full traceback but return a clean error state so the
            # orchestrator can decide what to do next (e.g. route to Support Agent).
            logger.exception("KnowledgeAgent: unexpected error for query='%s'", query[:80])
            return self._fail(state, f"Internal error in Knowledge Agent: {exc}")

        return state

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _out_of_scope(state: AgentState) -> AgentState:
        """
        No relevant chunks found.  Set confidence to 0 so the orchestrator
        knows this query should escalate to the Support Agent.
        """
        state.response = (
            "I don't have enough information in the knowledge base to answer that. "
            "I'll connect you with a support agent who can help further."
        )
        state.confidence = 0.0
        state.sources = []
        state.error = None
        return state

    @staticmethod
    def _fail(state: AgentState, message: str) -> AgentState:
        """
        Hard failure (bad input or unrecoverable error).
        Confidence 0 so the orchestrator escalates.
        """
        state.response = "Sorry, I was unable to process your request."
        state.confidence = 0.0
        state.sources = []
        state.error = message
        logger.warning("KnowledgeAgent._fail: %s", message)
        return state