import uuid

from fastapi import APIRouter, Depends, Response

from api.deps import Container, enforce_rate_limit, get_container, get_pipeline
from api.schemas import ChatRequest, ChatResponse, SourceOut
from rag.pipeline import RAGPipeline

router = APIRouter()

# Handlers are plain `def` on purpose: the pipeline is blocking (embedding, rerank,
# LLM), so FastAPI runs them in its threadpool instead of stalling the event loop.


@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(enforce_rate_limit)])
def chat(
    body: ChatRequest,
    pipeline: RAGPipeline = Depends(get_pipeline),
) -> ChatResponse:
    session_id = body.session_id or uuid.uuid4().hex
    result = pipeline.answer(session_id, body.message)
    return ChatResponse(
        session_id=session_id,
        answer=result.answer,
        sources=[SourceOut(**vars(s)) for s in result.sources],
    )


@router.delete("/sessions/{session_id}", status_code=204)
def delete_session(session_id: str, container: Container = Depends(get_container)) -> Response:
    container.sessions.delete(session_id)  # idempotent: unknown ids are fine
    return Response(status_code=204)
