import pytest
from fastapi.testclient import TestClient
from qdrant_client import QdrantClient

from api.app import create_app
from api.deps import Container
from api.rate_limit import RateLimiter
from core.config import ContextSettings, RerankSettings, Settings
from core.errors import LLMError, LLMTimeout, LLMUnavailable, VectorStoreUnavailable
from core.schema import Hit
from memory.session import SessionStore
from rag.pipeline import RAGPipeline
from rag.query_rewrite import QueryRewriter
from tests.conftest import FakeLLM, FakeReranker, FakeRetriever

HITS = [Hit("c1", "Dự án Biệt thự Hòa Bình rộng 300 m2", 0.03,
            {"type": "project", "project_name": "Biệt thự Hòa Bình", "project_image_url": "http://img/1.jpg"})]


class BrokenRetriever:
    def retrieve(self, query):
        raise VectorStoreUnavailable("qdrant down")


def make_client(llm=None, retriever=None, rate_limit=60) -> tuple[TestClient, Container]:
    settings = Settings()
    llm = llm or FakeLLM(["đây là câu trả lời"])
    sessions = SessionStore()
    pipeline = RAGPipeline(
        retriever or FakeRetriever(HITS), FakeReranker(), llm, QueryRewriter(llm), sessions,
        RerankSettings(), ContextSettings(),
    )
    container = Container(
        settings=settings, pipeline=pipeline, sessions=sessions, llm=llm, qdrant=QdrantClient(":memory:"),
        bm25_size=1, rerank_enabled=True, rate_limiter=RateLimiter(rate_limit),
    )
    app = create_app()
    app.state.container = container  # no lifespan: we inject fakes instead of real services
    return TestClient(app, raise_server_exceptions=False), container


def test_chat_returns_answer_session_and_sources():
    client, _ = make_client()
    r = client.post("/chat", json={"message": "Dự án Hòa Bình rộng bao nhiêu?"})
    assert r.status_code == 200
    body = r.json()
    assert body["answer"] == "đây là câu trả lời"
    assert body["session_id"]
    assert body["sources"][0]["title"] == "Biệt thự Hòa Bình"
    assert body["sources"][0]["image_url"] == "http://img/1.jpg"


def test_session_id_is_kept_and_history_grows():
    client, container = make_client()
    client.post("/chat", json={"session_id": "abc123", "message": "câu 1"})
    r = client.post("/chat", json={"session_id": "abc123", "message": "câu 2"})
    assert r.json()["session_id"] == "abc123"
    assert len(container.sessions.get("abc123")) == 4


def test_delete_session_clears_memory():
    client, container = make_client()
    client.post("/chat", json={"session_id": "abc", "message": "hi"})
    assert client.delete("/sessions/abc").status_code == 204
    assert container.sessions.get("abc") == []
    assert client.delete("/sessions/abc").status_code == 204  # idempotent


@pytest.mark.parametrize(
    "payload",
    [
        {"message": ""},
        {"message": "    "},
        {"message": "x" * 501},
        {"session_id": "bad id!", "message": "hi"},
        {},
    ],
)
def test_invalid_requests_return_400_without_stack_trace(payload):
    client, _ = make_client()
    r = client.post("/chat", json=payload)
    assert r.status_code == 400
    assert r.json()["error"] == "invalid_request"
    assert "Traceback" not in r.text


@pytest.mark.parametrize(
    "error, status, code",
    [
        (LLMTimeout("slow"), 504, "llm_timeout"),
        (LLMUnavailable("down"), 503, "llm_unavailable"),
        (LLMError("boom"), 502, "llm_error"),
    ],
)
def test_llm_errors_map_to_http_status(error, status, code):
    client, _ = make_client(llm=FakeLLM(error=error))
    r = client.post("/chat", json={"message": "hi"})
    assert (r.status_code, r.json()["error"]) == (status, code)


def test_vector_store_down_returns_503():
    client, _ = make_client(retriever=BrokenRetriever())
    r = client.post("/chat", json={"message": "hi"})
    assert (r.status_code, r.json()["error"]) == (503, "vector_store_unavailable")


def test_unexpected_error_is_hidden_from_user():
    class Boom:
        def retrieve(self, query):
            raise RuntimeError("secret internal detail")

    client, _ = make_client(retriever=Boom())
    r = client.post("/chat", json={"message": "hi"})
    assert r.status_code == 500
    assert "secret" not in r.text


def test_rate_limit_returns_429():
    client, _ = make_client(rate_limit=2)
    codes = [client.post("/chat", json={"message": "hi"}).status_code for _ in range(3)]
    assert codes == [200, 200, 429]


def test_health_ok_and_degraded():
    client, _ = make_client()
    ok = client.get("/health")
    assert ok.status_code == 200 and ok.json()["status"] == "ok"

    client, _ = make_client(llm=FakeLLM(error=LLMUnavailable("down")))
    degraded = client.get("/health")
    assert degraded.status_code == 503 and degraded.json()["llm"]["status"] == "down"
