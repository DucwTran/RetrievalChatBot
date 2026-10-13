import logging
from typing import Protocol

from qdrant_client import QdrantClient

from core.errors import VectorStoreUnavailable
from core.schema import Hit
from vectorstore.qdrant import DENSE_VECTOR

logger = logging.getLogger("retrieval")


class QueryEmbedder(Protocol):
    def embed_query(self, text: str) -> list[float]: ...


class DenseRetriever:
    """Semantic search: embed the query and ask Qdrant for the nearest chunks."""

    def __init__(self, client: QdrantClient, collection: str, embedder: QueryEmbedder):
        self._client = client
        self._collection = collection
        self._embedder = embedder

    def search(self, query: str, k: int) -> list[Hit]:
        vector = self._embedder.embed_query(query)
        try:
            response = self._client.query_points(
                collection_name=self._collection,
                query=vector,
                using=DENSE_VECTOR,
                limit=k,
                with_payload=True,
            )
        except Exception as e:
            raise VectorStoreUnavailable(f"Qdrant query failed: {e}") from e

        hits = []
        for point in response.points:
            payload = dict(point.payload or {})
            text = payload.pop("text", "")
            if text:
                hits.append(Hit(chunk_id=str(point.id), text=text, score=point.score, metadata=payload))
        return hits
