"""Single source of truth for configuration.

Defaults live here; override any value with an environment variable or `.env`,
using `__` as the nesting delimiter (e.g. `LLM__PROVIDER=openai`).
"""
from functools import lru_cache

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class DataSettings(BaseModel):
    raw_dir: str = "data/raw"
    processed_dir: str = "data/processed"


class ChunkingSettings(BaseModel):
    max_chars: int = 400
    overlap_sentences: int = 1


class QdrantSettings(BaseModel):
    url: str = "http://localhost:6333"
    path: str | None = None  # embedded mode without a server (dev only; one process at a time)
    api_key: str | None = None
    collection: str = "chatbot_collection"
    timeout: int = 30


class EmbeddingSettings(BaseModel):
    model: str = "intfloat/multilingual-e5-small"
    device: str = "cpu"
    batch_size: int = 64


class LLMSettings(BaseModel):
    provider: str = "ollama"  # validated against llm.factory.PROVIDERS
    model: str = "qwen2.5:3b"
    base_url: str | None = None  # ollama defaults to http://localhost:11434
    api_key: str | None = None
    temperature: float = 0.2
    max_tokens: int = 1024
    timeout: int = 60


class RetrievalSettings(BaseModel):
    dense_k: int = 20
    bm25_k: int = 20
    rrf_k: int = 60
    candidates_n: int = 20


class RerankSettings(BaseModel):
    enabled: bool = True
    model: str = "BAAI/bge-reranker-v2-m3"
    device: str = "cpu"
    top_k: int = 5
    min_score: float = 0.01  # tuned on the evaluation set: off-topic <= 0.0011, relevant >= 0.07
    max_length: int = 512


class ContextSettings(BaseModel):
    max_chars: int = 3000


class MemorySettings(BaseModel):
    max_messages: int = 5
    ttl_seconds: int = 1800
    max_sessions: int = 1000


class ApiSettings(BaseModel):
    max_message_length: int = 500
    rate_limit_per_minute: int = 60
    cors_origins: list[str] = ["http://localhost:5173"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_nested_delimiter="__", extra="ignore"
    )

    log_level: str = "INFO"
    data: DataSettings = DataSettings()
    chunking: ChunkingSettings = ChunkingSettings()
    qdrant: QdrantSettings = QdrantSettings()
    embedding: EmbeddingSettings = EmbeddingSettings()
    llm: LLMSettings = LLMSettings()
    retrieval: RetrievalSettings = RetrievalSettings()
    rerank: RerankSettings = RerankSettings()
    context: ContextSettings = ContextSettings()
    memory: MemorySettings = MemorySettings()
    api: ApiSettings = ApiSettings()


@lru_cache
def get_settings() -> Settings:
    return Settings()
