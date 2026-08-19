from langchain_openai import ChatOpenAI
from app.core.config import settings


def get_llm(
    temperature: float = 0.1,
    streaming: bool = False,
    model: str | None = None,
) -> ChatOpenAI:
    return ChatOpenAI(
        model=model or settings.model_name,
        base_url=settings.ollama_base_url,
        api_key=settings.ollama_api_key,
        temperature=temperature,
        streaming=streaming,
    )
