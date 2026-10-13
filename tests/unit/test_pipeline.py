import pytest

from core.config import ContextSettings, RerankSettings
from core.errors import LLMTimeout
from core.schema import Hit
from memory.session import SessionStore
from rag.pipeline import RAGPipeline
from rag.prompts import NO_ANSWER
from rag.query_rewrite import QueryRewriter
from tests.conftest import FakeLLM, FakeReranker, FakeRetriever

HITS = [Hit("c1", "Dự án Biệt thự Hòa Bình rộng 300 m2", 0.03, {"type": "project", "project_name": "Biệt thự Hòa Bình"})]


def make_pipeline(llm=None, retriever=None, reranker=None, min_score=0.0):
    llm = llm or FakeLLM(["câu trả lời"])
    retriever = retriever or FakeRetriever(HITS)
    sessions = SessionStore()
    pipeline = RAGPipeline(
        retriever, reranker or FakeReranker(), llm, QueryRewriter(llm), sessions,
        RerankSettings(min_score=min_score), ContextSettings(),
    )
    return pipeline, llm, retriever, sessions


def test_first_turn_skips_rewrite_and_answers_with_sources():
    pipeline, llm, retriever, _ = make_pipeline()
    result = pipeline.answer("s1", "Dự án Hòa Bình rộng bao nhiêu?")
    assert result.answer == "câu trả lời"
    assert len(llm.calls) == 1  # only the answer call; no rewrite without history
    assert retriever.queries == ["Dự án Hòa Bình rộng bao nhiêu?"]
    assert result.sources[0].title == "Biệt thự Hòa Bình"
    assert set(result.timings) >= {"retrieval", "rerank", "llm", "total"}


def test_follow_up_retrieves_with_rewritten_query_but_answers_original_question():
    pipeline, llm, retriever, _ = make_pipeline(llm=FakeLLM(["a1", "Diện tích dự án Hòa Bình?", "a2"]))
    pipeline.answer("s", "Dự án Hòa Bình ở đâu?")
    pipeline.answer("s", "Thế còn diện tích?")
    assert retriever.queries[-1] == "Diện tích dự án Hòa Bình?"  # rewritten for retrieval
    final_messages = llm.calls[-1]
    assert "Thế còn diện tích?" in final_messages[-1].content  # original question goes to the LLM
    assert [m.role for m in final_messages][:3] == ["system", "user", "assistant"]  # history included


def test_no_relevant_context_skips_llm():
    pipeline, llm, _, sessions = make_pipeline(reranker=FakeReranker(score=0.001), min_score=0.5)
    result = pipeline.answer("s", "câu hỏi lạc đề")
    assert result.answer == NO_ANSWER
    assert result.sources == []
    assert llm.calls == []
    assert len(sessions.get("s")) == 2  # the exchange is still remembered


def test_llm_failure_does_not_write_memory():
    pipeline, _, _, sessions = make_pipeline(llm=FakeLLM(error=LLMTimeout("slow")))
    with pytest.raises(LLMTimeout):
        pipeline.answer("s", "câu hỏi")
    assert sessions.get("s") == []


def test_memory_is_capped_at_five_messages_across_turns():
    pipeline, _, _, sessions = make_pipeline(llm=FakeLLM(["ok"]))
    for i in range(4):
        pipeline.answer("s", f"câu {i}")
    assert len(sessions.get("s")) == 5
