import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from api.bootstrap import build_container
from api.errors import register_error_handlers
from api.routes import chat, health
from core.config import get_settings
from core.setup_logging import setup_logging

logger = logging.getLogger("api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging()
    app.state.container = build_container(settings)  # any failure aborts startup
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="RAG Chatbot API", version="2.0.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api.cors_origins,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Content-Type"],
    )

    @app.middleware("http")
    async def response_time(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Response-Time"] = f"{(time.perf_counter() - start) * 1000:.0f}ms"
        return response

    register_error_handlers(app)
    app.include_router(chat.router)
    app.include_router(health.router)
    return app


app = create_app()
