import logging
from dataclasses import replace
from typing import Protocol

from core.config import RerankSettings
from core.schema import Hit
from reranking.base import BaseReranker

logger = logging.getLogger("reranking")


class PairScorer(Protocol):
    def score_batch(self, pairs: list[tuple[str, str]]) -> list[float]: ...


class CrossEncoderReranker(BaseReranker):
    """Scores every (query, chunk) pair jointly; slower but far more precise than retrieval."""

    def __init__(self, scorer: PairScorer):
        self._scorer = scorer

    def rerank(self, query: str, hits: list[Hit], top_k: int) -> list[Hit]:
        if not hits:
            return []
        scores = self._scorer.score_batch([(query, h.text) for h in hits])
        scored = [
            replace(h, metadata={**h.metadata, "rerank_score": float(s)})
            for h, s in zip(hits, scores, strict=True)
        ]
        scored.sort(key=lambda h: h.metadata["rerank_score"], reverse=True)
        return scored[:top_k]


class PassthroughReranker(BaseReranker):
    """Keeps retrieval order; used when reranking is disabled (e.g. for ablation)."""

    def rerank(self, query: str, hits: list[Hit], top_k: int) -> list[Hit]:
        return hits[:top_k]


def build_reranker(cfg: RerankSettings) -> BaseReranker:
    if not cfg.enabled:
        return PassthroughReranker()
    from reranking.models.cross_encoder import CrossEncoderModel

    return CrossEncoderReranker(CrossEncoderModel(cfg.model, cfg.device, cfg.max_length))
