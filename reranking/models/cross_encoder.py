import logging

from sentence_transformers import CrossEncoder

from core.errors import RerankerUnavailable

logger = logging.getLogger("reranking")


class CrossEncoderModel:
    """Thin wrapper so the reranker can be tested with a fake scorer."""

    def __init__(self, model_name: str, device: str = "cpu", max_length: int = 512):
        logger.info(f"Loading reranker model: {model_name}")
        # fp16 halves the model's VRAM use on GPU.
        kwargs = {"torch_dtype": "float16"} if device.startswith("cuda") else {}
        try:
            self._model = CrossEncoder(model_name, device=device, max_length=max_length, model_kwargs=kwargs)
        except Exception as e:
            raise RerankerUnavailable(f"Cannot load reranker '{model_name}': {e}") from e

    def score_batch(self, pairs: list[tuple[str, str]]) -> list[float]:
        return self._model.predict(pairs).tolist()
