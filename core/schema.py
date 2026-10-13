from dataclasses import dataclass, field
from typing import Any


@dataclass
class Chunk:
    """A unit of knowledge produced by ingestion and stored in Qdrant."""
    id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Hit:
    """A retrieval result; `score` is whatever the producing stage assigned."""
    chunk_id: str
    text: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Source:
    """What the client sees for each chunk that backed an answer."""
    title: str
    type: str | None
    slug: str | None
    image_url: str | None
    snippet: str
    score: float
