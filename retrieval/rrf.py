from core.schema import Hit


def reciprocal_rank_fusion(rankings: list[list[Hit]], k: int = 60, top_n: int | None = None) -> list[Hit]:
    """Fuse ranked lists: score(d) = sum over lists of 1 / (k + rank), rank starting at 1.

    RRF only uses ranks, so it needs no score normalisation between retrievers
    whose scores live on different scales (cosine vs BM25).
    `metadata["rrf_ranks"]` records the rank in each input list (None if absent).
    """
    scores: dict[str, float] = {}
    first_seen: dict[str, Hit] = {}
    ranks: dict[str, list[int | None]] = {}

    for list_idx, ranking in enumerate(rankings):
        for rank, hit in enumerate(ranking, start=1):
            scores[hit.chunk_id] = scores.get(hit.chunk_id, 0.0) + 1.0 / (k + rank)
            first_seen.setdefault(hit.chunk_id, hit)
            ranks.setdefault(hit.chunk_id, [None] * len(rankings))[list_idx] = rank

    fused = [
        Hit(
            chunk_id=cid,
            text=first_seen[cid].text,
            score=score,
            metadata={**first_seen[cid].metadata, "rrf_ranks": ranks[cid]},
        )
        for cid, score in scores.items()
    ]
    fused.sort(key=lambda h: h.score, reverse=True)
    return fused[:top_n] if top_n else fused
