import httpx
import asyncio
from typing import Any
import logfire
from app.core.config import settings

JINA_EMBED_URL = "https://api.jina.ai/v1/embeddings"
JINA_RERANK_URL = "https://api.jina.ai/v1/rerank"
EMBEDDING_DIM = 1024

_embed_cache: dict[str, list[float]] = {}


class EmbeddingService:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {settings.jina_api_key}",
            "Content-Type": "application/json",
        }
        self.model = settings.jina_embedding_model

    async def embed(self, text: str) -> list[float]:
        if text in _embed_cache:
            return _embed_cache[text]
        result = await self.embed_batch([text])
        return result[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        uncached = [t for t in texts if t not in _embed_cache]
        if uncached:
            async with httpx.AsyncClient(timeout=30) as client:
                for attempt in range(3):
                    try:
                        resp = await client.post(
                            JINA_EMBED_URL,
                            headers=self.headers,
                            json={"model": self.model, "input": uncached},
                        )
                        resp.raise_for_status()
                        data = resp.json()
                        for i, item in enumerate(data["data"]):
                            _embed_cache[uncached[i]] = item["embedding"]
                        break
                    except Exception as e:
                        if attempt == 2:
                            logfire.error("Embedding failed", error=str(e))
                            for t in uncached:
                                _embed_cache[t] = [0.0] * EMBEDDING_DIM
                        await asyncio.sleep(2 ** attempt)
        return [_embed_cache[t] for t in texts]


class RerankService:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {settings.jina_api_key}",
            "Content-Type": "application/json",
        }
        self.model = settings.jina_reranker_model

    async def rerank(self, query: str, documents: list[str], top_n: int = 5) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=30) as client:
            for attempt in range(3):
                try:
                    resp = await client.post(
                        JINA_RERANK_URL,
                        headers=self.headers,
                        json={"model": self.model, "query": query, "documents": documents, "top_n": top_n},
                    )
                    resp.raise_for_status()
                    results = resp.json()["results"]
                    return [{"index": r["index"], "score": r["relevance_score"], "text": documents[r["index"]]} for r in results]
                except Exception as e:
                    if attempt == 2:
                        logfire.error("Rerank failed", error=str(e))
                        return [{"index": i, "score": 1.0, "text": d} for i, d in enumerate(documents[:top_n])]
                    await asyncio.sleep(2 ** attempt)
        return []


embedding_service = EmbeddingService()
rerank_service = RerankService()
