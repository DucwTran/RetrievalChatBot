from core.config import RetrievalSettings
from core.schema import Hit
from retrieval.bm25_index import Bm25Index, tokenize
from retrieval.hybrid import HybridRetriever
from retrieval.rrf import reciprocal_rank_fusion
from tests.conftest import cid


def hit(chunk_id: str) -> Hit:
    return Hit(chunk_id=chunk_id, text=chunk_id, score=0.0)


# ---- tokenizer / BM25 -------------------------------------------------------

def test_tokenize_lowercases_and_strips_punctuation():
    assert tokenize("Biệt thự, Đà Nẵng!") == ["biệt", "thự", "đà", "nẵng"]


def test_bm25_ranks_matching_chunk_first(chunks):
    index = Bm25Index(chunks)
    hits = index.search("phong cách Japandi", k=3)
    assert hits[0].chunk_id == cid(3)


def test_bm25_returns_nothing_for_unknown_terms(chunks):
    assert Bm25Index(chunks).search("zzzxxx", k=3) == []


def test_bm25_respects_k(chunks):
    assert len(Bm25Index(chunks).search("dự án phong cách công ty", k=2)) == 2


def test_bm25_rare_term_outweighs_common_term(chunks):
    # "japandi" appears in one chunk, "phong" in two: rare term should dominate.
    hits = Bm25Index(chunks).search("phong japandi", k=2)
    assert hits[0].chunk_id == cid(3)


# ---- RRF ---------------------------------------------------------------------

def test_rrf_matches_hand_computed_scores():
    fused = reciprocal_rank_fusion([[hit("a"), hit("b"), hit("c")], [hit("b"), hit("c"), hit("d")]], k=60)
    assert [h.chunk_id for h in fused] == ["b", "c", "a", "d"]
    scores = {h.chunk_id: h.score for h in fused}
    assert scores["b"] == 1 / 62 + 1 / 61
    assert scores["a"] == 1 / 61


def test_rrf_records_ranks_per_list():
    fused = reciprocal_rank_fusion([[hit("a")], [hit("b"), hit("a")]], k=60)
    assert {h.chunk_id: h.metadata["rrf_ranks"] for h in fused} == {"a": [1, 2], "b": [None, 1]}


def test_rrf_top_n():
    fused = reciprocal_rank_fusion([[hit("a"), hit("b"), hit("c")]], top_n=2)
    assert len(fused) == 2


def test_rrf_handles_empty_input():
    assert reciprocal_rank_fusion([[], []]) == []


# ---- hybrid ------------------------------------------------------------------

class StubDense:
    def __init__(self, hits):
        self.hits = hits

    def search(self, query, k):
        return self.hits[:k]


def test_hybrid_surfaces_chunk_that_dense_missed(chunks):
    """BM25 is an independent branch, so an exact keyword match survives even if dense misses it."""
    bm25 = Bm25Index(chunks)
    dense = StubDense([hit(cid(1)), hit(cid(2))])  # dense never returns c3
    retriever = HybridRetriever(dense, bm25, RetrievalSettings(dense_k=2, bm25_k=3, candidates_n=10))
    ids = [h.chunk_id for h in retriever.retrieve("Japandi")]
    assert cid(3) in ids
