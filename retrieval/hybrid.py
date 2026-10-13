from core.config import RetrievalSettings
from core.schema import Hit
from retrieval.bm25_index import Bm25Index
from retrieval.dense import DenseRetriever
from retrieval.rrf import reciprocal_rank_fusion


class HybridRetriever:
    """Dense + BM25, each searching the full corpus, merged with RRF."""

    def __init__(self, dense: DenseRetriever, bm25: Bm25Index, cfg: RetrievalSettings):
        self._dense = dense
        self._bm25 = bm25
        self._cfg = cfg

    def retrieve(self, query: str) -> list[Hit]:
        dense_hits = self._dense.search(query, self._cfg.dense_k)
        bm25_hits = self._bm25.search(query, self._cfg.bm25_k)
        return reciprocal_rank_fusion(
            [dense_hits, bm25_hits], k=self._cfg.rrf_k, top_n=self._cfg.candidates_n
        )
