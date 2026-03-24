import logging
import os
from fastapi import APIRouter
from vectorstore.qdrant import get_qdrant_client
from core.load_settings import load_settings

logger = logging.getLogger("health")
router = APIRouter()

@router.get("/health")
async def health_check():
    health_status = {
        "status": "healthy",
        "services": {}
    }

    try:
        client = get_qdrant_client()
        collections = client.get_collections()
        health_status["services"]["qdrant"] = {
            "status": "up",
            "collections": len(collections.collections)
        }
    except Exception as e:
        logger.error(f"Embedding model health check failed: {e}")
        health_status["status"] = "degraded"
        health_status["services"]["embedding"] = {
            "status": "down",
            "error": str(e)
        }

    settings = load_settings()
    llm_config = settings.get("llm", {})
    health_status["services"]["llm"] = {
        "provider": llm_config.get("provider", "unknown"),
        "model": llm_config.get("model_name", "unknown"),
        "status": "configured"
    }

    return health_status