import logging

from sentence_transformers import SentenceTransformer

logger = logging.getLogger("embedding")


class Embedder:
    """Dense embedder. E5-family models need "query: " / "passage: " prefixes."""

    def __init__(self, model_name: str, device: str = "cpu", batch_size: int = 64):
        logger.info(f"Loading embedding model {model_name}")
        self._model = SentenceTransformer(model_name, device=device)
        self._batch_size = batch_size
        self._use_e5_prefix = "e5" in model_name.lower()

    @property
    def dimension(self) -> int:
        return self._model.get_sentence_embedding_dimension()

    def embed_passages(self, texts: list[str]) -> list[list[float]]:
        return self._encode(texts, "passage: ")

    def embed_query(self, text: str) -> list[float]:
        return self._encode([text], "query: ")[0]

    def _encode(self, texts: list[str], prefix: str) -> list[list[float]]:
        if not texts:
            return []
        if self._use_e5_prefix:
            texts = [prefix + t for t in texts]
        vectors = self._model.encode(
            texts, batch_size=self._batch_size, normalize_embeddings=True, convert_to_numpy=True
        )
        return vectors.tolist()
