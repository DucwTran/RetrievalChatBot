import logging
from transformers import SentenceTransformer

from core.load_settings import load_settings

settings = load_settings()
logger = logging.getLogger("embedding")

EMBEDDING_MODEL = settings["embedding"]["model"]
EMBEDDING_DEVICE = settings["embedding"].get("device", "cpu")

_model = None

def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        logger.info(f"Loading embedding model {EMBEDDING_MODEL}.")
        _model = SentenceTransformer(EMBEDDING_MODEL, device=EMBEDDING_DEVICE)
    return _model

def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        logger.warning("No texts provided for embedding.")
        return []
        
    model = get_model()
    embeddings = model.encode(texts, normalize_embeddings=True, convert_to_tensor=False).tolist()
    logger.info(f"Completed embedding texts {len(texts)}.")
    return embeddings