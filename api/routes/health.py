import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from api.deps import Container, get_container

logger = logging.getLogger("api")
router = APIRouter()


def _qdrant_ok(container: Container) -> bool:
    try:
        container.qdrant.get_collections()
        return True
    except Exception as e:
        logger.warning(f"Qdrant health check failed: {e}")
        return False


@router.get("/health")
def health(container: Container = Depends(get_container)) -> JSONResponse:
    qdrant = _qdrant_ok(container)
    llm = container.llm.ping()
    body = {
        "status": "ok" if qdrant and llm else "degraded",
        "qdrant": "up" if qdrant else "down",
        "llm": {
            "status": "up" if llm else "down",
            "provider": container.settings.llm.provider,
            "model": container.settings.llm.model,
        },
        "reranker": "enabled" if container.rerank_enabled else "disabled",
        "bm25_chunks": container.bm25_size,
    }
    return JSONResponse(status_code=200 if body["status"] == "ok" else 503, content=body)
