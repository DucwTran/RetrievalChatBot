from abc import ABC, abstractmethod

from core.schema import Hit


class BaseReranker(ABC):
    @abstractmethod
    def rerank(self, query: str, hits: list[Hit], top_k: int) -> list[Hit]:
        """Return the `top_k` best hits, best first, with `rerank_score` in metadata."""
