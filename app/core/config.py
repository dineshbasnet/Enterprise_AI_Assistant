from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM
    ollama_base_url: str = "http://localhost:11434/v1"
    model_name: str = "qwen3:4b"
    ollama_api_key: str = "ollama"

    # Embeddings / Reranking
    jina_api_key: str = "dummy_jina_key"
    jina_embedding_model: str = "jina-embeddings-v3"
    jina_reranker_model: str = "jina-reranker-v2-base-multilingual"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/ai_platform"

    @property
    def async_database_url(self) -> str:
        url = self.database_url
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url
    supabase_url: str = "dummy"
    supabase_key: str = "dummy"

    # Observability
    logfire_token: str = "dummy_logfire_token"

    # App
    app_env: str = "development"
    app_secret_key: str = "dummy_secret_key"


settings = Settings()
