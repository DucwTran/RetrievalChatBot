from dataclasses import dataclass

from fastapi import Depends, Request
from qdrant_client import QdrantClient

from api.rate_limit import RateLimiter
from core.config import Settings
from core.errors import RateLimited
from llm.base import BaseLLM
from memory.session import SessionStore
from rag.pipeline import RAGPipeline


@dataclass
class Container:
    """Everything built once at startup and shared by requests."""
    settings: Settings
    pipeline: RAGPipeline
    sessions: SessionStore
    llm: BaseLLM
    qdrant: QdrantClient
    bm25_size: int
    rerank_enabled: bool
    rate_limiter: RateLimiter


def get_container(request: Request) -> Container:
    return request.app.state.container


def get_pipeline(container: Container = Depends(get_container)) -> RAGPipeline:
    return container.pipeline


def enforce_rate_limit(request: Request, container: Container = Depends(get_container)) -> None:
    client = request.client.host if request.client else "unknown"
    if not container.rate_limiter.allow(client):
        raise RateLimited()
