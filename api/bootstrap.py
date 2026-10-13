import logging
from dataclasses import dataclass

from qdrant_client import QdrantClient

from api.deps import Container
from api.rate_limit import RateLimiter
from core.config import Settings
from llm.factory import get_llm
from memory.session import SessionStore
from rag.pipeline import RAGPipeline
from rag.query_rewrite import QueryRewriter
from reranking.base import BaseReranker
from reranking.reranker import build_reranker
from retrieval.bm25_index import Bm25Index
from retrieval.dense import DenseRetriever
from retrieval.hybrid import HybridRetriever
from vectorstore.qdrant import load_corpus, make_client

logger = logging.getLogger("api")


@dataclass
class RetrievalStack:
    """Retrieval components shared by the API and the evaluation script."""
    client: QdrantClient
    bm25: Bm25Index
    dense: DenseRetriever
    hybrid: HybridRetriever
    reranker: BaseReranker


def build_retrieval(settings: Settings) -> RetrievalStack:
    from embedding.embedder import Embedder  # heavy import (torch); keep out of module import time

    client = make_client(settings.qdrant)
    corpus = load_corpus(client, settings.qdrant.collection)
    if not corpus:
        raise RuntimeError(
            f"Collection '{settings.qdrant.collection}' is empty. Run: python -m scripts.ingest"
        )
    bm25 = Bm25Index(corpus)
    embedder = Embedder(settings.embedding.model, settings.embedding.device, settings.embedding.batch_size)
    dense = DenseRetriever(client, settings.qdrant.collection, embedder)
    return RetrievalStack(
        client=client,
        bm25=bm25,
        dense=dense,
        hybrid=HybridRetriever(dense, bm25, settings.retrieval),
        reranker=build_reranker(settings.rerank),
    )


def build_container(settings: Settings) -> Container:
    """Wire the whole application. Raises on any failure so a half-working app never starts."""
    stack = build_retrieval(settings)
    llm = get_llm(settings.llm)
    sessions = SessionStore(
        settings.memory.max_messages, settings.memory.ttl_seconds, settings.memory.max_sessions
    )
    pipeline = RAGPipeline(
        stack.hybrid, stack.reranker, llm, QueryRewriter(llm), sessions, settings.rerank, settings.context
    )
    logger.info(f"Ready: {len(stack.bm25)} chunks, llm={settings.llm.provider}:{settings.llm.model}")
    return Container(
        settings=settings,
        pipeline=pipeline,
        sessions=sessions,
        llm=llm,
        qdrant=stack.client,
        bm25_size=len(stack.bm25),
        rerank_enabled=settings.rerank.enabled,
        rate_limiter=RateLimiter(settings.api.rate_limit_per_minute),
    )
