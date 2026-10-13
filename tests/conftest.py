import hashlib
import math
import uuid

import pytest

from core.schema import Chunk, Hit
from llm.base import BaseLLM, ChatMessage, LLMResult
from reranking.base import BaseReranker
from retrieval.bm25_index import tokenize


def cid(n: int) -> str:
    """Qdrant point ids must be UUIDs; tests refer to chunks by small numbers."""
    return str(uuid.UUID(int=n))


class FakeLLM(BaseLLM):
    """Returns canned replies and records every call."""

    def __init__(self, replies=None, error: Exception | None = None):
        self.replies = list(replies or ["fake answer"])
        self.error = error
        self.calls: list[list[ChatMessage]] = []

    def generate(self, messages, *, temperature=None, max_tokens=None) -> LLMResult:
        self.calls.append(messages)
        if self.error:
            raise self.error
        text = self.replies.pop(0) if len(self.replies) > 1 else self.replies[0]
        return LLMResult(text=text, model="fake", input_tokens=10, output_tokens=5)

    def ping(self) -> bool:
        return self.error is None


class FakeRetriever:
    def __init__(self, hits: list[Hit]):
        self.hits = hits
        self.queries: list[str] = []

    def retrieve(self, query: str) -> list[Hit]:
        self.queries.append(query)
        return list(self.hits)


class FakeReranker(BaseReranker):
    """Gives each hit a fixed rerank_score (default 1.0) and keeps order."""

    def __init__(self, score: float = 1.0):
        self.score = score

    def rerank(self, query, hits, top_k):
        return [Hit(h.chunk_id, h.text, h.score, {**h.metadata, "rerank_score": self.score}) for h in hits[:top_k]]


class HashEmbedder:
    """Deterministic bag-of-words embedder: shared words => higher cosine similarity."""

    dimension = 64

    def _vec(self, text: str) -> list[float]:
        v = [0.0] * self.dimension
        for tok in tokenize(text):
            v[int(hashlib.md5(tok.encode()).hexdigest(), 16) % self.dimension] += 1.0
        norm = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / norm for x in v]

    def embed_passages(self, texts):
        return [self._vec(t) for t in texts]

    def embed_query(self, text):
        return self._vec(text)


@pytest.fixture
def chunks() -> list[Chunk]:
    rows = [
        (cid(1), "Dự án Biệt thự Hòa Bình có diện tích 300 m2 tại Đà Nẵng", {"type": "project", "project_name": "Biệt thự Hòa Bình"}),
        (cid(2), "Phong cách Indochine kết hợp nét Đông Dương và Pháp", {"type": "interior_style", "interior_name": "Indochine"}),
        (cid(3), "Phong cách Japandi kết hợp Nhật Bản và Bắc Âu tối giản", {"type": "interior_style", "interior_name": "Japandi"}),
        (cid(4), "Công ty hoạt động từ 8 giờ đến 17 giờ các ngày trong tuần", {"type": "company_info", "company_name": "NMK"}),
        (cid(5), "Tin tức: khánh thành dự án nhà phố hiện đại tại quận 3", {"type": "news", "news_item_title": "Khánh thành nhà phố"}),
    ]
    return [Chunk(id=i, text=t, metadata=m) for i, t, m in rows]
