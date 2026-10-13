from dataclasses import dataclass, field

from core.schema import Hit, Source

TITLE_KEYS = (
    "project_name", "news_item_title", "interior_name", "architecture_type_name",
    "project_category_name", "news_category_name", "company_name",
)
SLUG_KEYS = ("project_slug", "news_item_slug", "interior_slug")
SNIPPET_CHARS = 200


@dataclass
class ContextResult:
    text: str
    sources: list[Source] = field(default_factory=list)  # same order as the [n] labels in `text`


def _first(metadata: dict, keys) -> str | None:
    return next((metadata[k] for k in keys if metadata.get(k)), None)


def _image(metadata: dict) -> str | None:
    return next(
        (v for k, v in metadata.items() if v and k.endswith(("image_url", "thumbnail_url"))), None
    )


def to_source(hit: Hit) -> Source:
    meta = hit.metadata
    snippet = hit.text if len(hit.text) <= SNIPPET_CHARS else hit.text[:SNIPPET_CHARS].rstrip() + "..."
    return Source(
        title=_first(meta, TITLE_KEYS) or meta.get("type") or "Nguồn",
        type=meta.get("type"),
        slug=_first(meta, SLUG_KEYS),
        image_url=_image(meta),
        snippet=snippet,
        score=meta.get("rerank_score", hit.score),
    )


def build_context(hits: list[Hit], *, max_chars: int, min_score: float | None = None) -> ContextResult:
    """Dedup -> drop irrelevant -> keep best-first order -> fit the character budget.

    Hits are expected best-first. The score filter only applies when a reranker
    scored them. A chunk that doesn't fit the remaining budget is skipped whole
    rather than cut mid-sentence.
    """
    seen_ids: set[str] = set()
    seen_texts: set[str] = set()
    parts: list[str] = []
    sources: list[Source] = []
    used = 0

    for hit in hits:
        normalized = " ".join(hit.text.split())
        if not normalized or hit.chunk_id in seen_ids or normalized in seen_texts:
            continue
        seen_ids.add(hit.chunk_id)
        seen_texts.add(normalized)

        score = hit.metadata.get("rerank_score")
        if min_score is not None and score is not None and score < min_score:
            continue
        if used + len(normalized) > max_chars:
            continue

        source = to_source(hit)
        parts.append(f"[{len(sources) + 1}] {source.title}\n{hit.text.strip()}")
        sources.append(source)
        used += len(normalized)

    return ContextResult(text="\n\n".join(parts), sources=sources)
