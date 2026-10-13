import logging
from collections.abc import Iterator

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PayloadSchemaType, PointStruct, VectorParams

from core.config import QdrantSettings
from core.errors import VectorStoreUnavailable
from core.schema import Chunk

logger = logging.getLogger("vector_database")

DENSE_VECTOR = "dense"


def make_client(cfg: QdrantSettings) -> QdrantClient:
    if cfg.path:
        return QdrantClient(path=cfg.path)
    client = QdrantClient(url=cfg.url, api_key=cfg.api_key or None, timeout=cfg.timeout)
    try:
        client.get_collections()
    except Exception as e:
        raise VectorStoreUnavailable(f"Cannot connect to Qdrant at {cfg.url}: {e}") from e
    return client


def ensure_collection(client: QdrantClient, name: str, dimension: int, recreate: bool = False) -> None:
    exists = client.collection_exists(name)
    if exists and recreate:
        client.delete_collection(name)
        exists = False
    if exists:
        return
    client.create_collection(
        collection_name=name,
        vectors_config={DENSE_VECTOR: VectorParams(size=dimension, distance=Distance.COSINE)},
    )
    client.create_payload_index(name, field_name="type", field_schema=PayloadSchemaType.KEYWORD)
    logger.info(f"Created collection '{name}' (dim={dimension}, cosine)")


def upsert_chunks(client: QdrantClient, name: str, chunks: list[Chunk], vectors: list[list[float]]) -> None:
    points = [
        PointStruct(id=c.id, vector={DENSE_VECTOR: v}, payload={"text": c.text, **c.metadata})
        for c, v in zip(chunks, vectors, strict=True)
    ]
    client.upsert(collection_name=name, points=points)


def load_corpus(client: QdrantClient, name: str, batch: int = 256) -> list[Chunk]:
    """Read every chunk back from Qdrant (used to build the in-memory BM25 index)."""
    return list(_scroll(client, name, batch))


def _scroll(client: QdrantClient, name: str, batch: int) -> Iterator[Chunk]:
    offset = None
    while True:
        points, offset = client.scroll(
            collection_name=name, limit=batch, offset=offset, with_payload=True, with_vectors=False
        )
        for p in points:
            payload = dict(p.payload or {})
            text = payload.pop("text", "")
            if text:
                yield Chunk(id=str(p.id), text=text, metadata=payload)
        if offset is None:
            return
