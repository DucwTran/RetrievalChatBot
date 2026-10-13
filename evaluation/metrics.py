"""Retrieval metrics. A question lists `relevant` as metadata filters; a hit is
relevant if its metadata satisfies ALL key/values of ANY one filter. Matching on
metadata (not chunk ids) keeps the dataset valid when chunking changes."""
import statistics
from collections.abc import Sequence

from core.schema import Hit

K = 5  # cutoff used for Recall@K / Precision@K throughout the evaluation


def is_relevant(hit: Hit, relevant: Sequence[dict]) -> bool:
    return any(all(hit.metadata.get(k) == v for k, v in f.items()) for f in relevant)


def recall_at_k(hits: Sequence[Hit], relevant: Sequence[dict], k: int) -> float:
    """1.0 if at least one relevant chunk is in the top k (hit rate), else 0.0."""
    return float(any(is_relevant(h, relevant) for h in hits[:k]))


def reciprocal_rank(hits: Sequence[Hit], relevant: Sequence[dict]) -> float:
    for rank, hit in enumerate(hits, start=1):
        if is_relevant(hit, relevant):
            return 1.0 / rank
    return 0.0


def precision_at_k(hits: Sequence[Hit], relevant: Sequence[dict], k: int) -> float:
    top = hits[:k]
    return sum(is_relevant(h, relevant) for h in top) / k if top else 0.0


def percentile(values: Sequence[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, round(pct / 100 * (len(ordered) - 1)))
    return ordered[index]


def summarize_latency(values: Sequence[float]) -> dict[str, float]:
    return {
        "mean": statistics.fmean(values) if values else 0.0,
        "p50": percentile(values, 50),
        "p95": percentile(values, 95),
    }
