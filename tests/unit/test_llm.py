from types import SimpleNamespace

import httpx
import ollama
import pytest

from core.config import LLMSettings
from core.errors import LLMError, LLMTimeout, LLMUnavailable
from llm.base import ChatMessage
from llm.factory import PROVIDERS, get_llm
from llm.ollama import OllamaLLM
from llm.openai import OpenAILLM
from rag.query_rewrite import QueryRewriter
from memory.session import SessionStore
from tests.conftest import FakeLLM

MSGS = [ChatMessage("user", "hi")]


def test_factory_selects_provider_from_settings():
    assert isinstance(get_llm(LLMSettings(provider="ollama")), OllamaLLM)
    assert isinstance(get_llm(LLMSettings(provider="openai", api_key="sk-test")), OpenAILLM)


def test_factory_rejects_unknown_provider():
    cfg = LLMSettings(provider="nope")
    with pytest.raises(ValueError, match="Unknown LLM provider"):
        get_llm(cfg)


def test_openai_requires_api_key():
    with pytest.raises(ValueError):
        get_llm(LLMSettings(provider="openai"))


def test_registering_new_provider_needs_no_pipeline_change(monkeypatch):
    monkeypatch.setitem(PROVIDERS, "fake", lambda cfg: FakeLLM())
    cfg = LLMSettings(provider="fake")
    assert isinstance(get_llm(cfg), FakeLLM)


class StubOllamaClient:
    def __init__(self, error=None):
        self.error = error

    def chat(self, **kwargs):
        if self.error:
            raise self.error
        return SimpleNamespace(
            message=SimpleNamespace(content="  xin chào  "), prompt_eval_count=11, eval_count=7
        )


def make_ollama(error=None) -> OllamaLLM:
    llm = OllamaLLM(LLMSettings())
    llm._client = StubOllamaClient(error)
    return llm


def test_ollama_success_returns_text_and_tokens():
    result = make_ollama().generate(MSGS)
    assert (result.text, result.input_tokens, result.output_tokens) == ("xin chào", 11, 7)


@pytest.mark.parametrize(
    "raised, expected",
    [
        (httpx.ReadTimeout("slow"), LLMTimeout),
        (httpx.ConnectError("down"), LLMUnavailable),
        (ConnectionError("down"), LLMUnavailable),
        (ollama.ResponseError("model not found", 404), LLMError),
    ],
)
def test_ollama_errors_are_mapped_to_typed_errors(raised, expected):
    with pytest.raises(expected):
        make_ollama(raised).generate(MSGS)


def test_timeout_is_not_reported_as_unavailable():
    with pytest.raises(LLMTimeout):
        make_ollama(httpx.ReadTimeout("slow")).generate(MSGS)


# ---- query rewriting ---------------------------------------------------------

def test_rewrite_skips_llm_without_history():
    llm = FakeLLM()
    assert QueryRewriter(llm).rewrite([], "Xin chào") == "Xin chào"
    assert llm.calls == []


def test_rewrite_uses_history_to_build_standalone_query():
    store = SessionStore()
    store.append("s", "Resort Hải Vân 2 ở đâu?", "Ở Đà Nẵng.")
    llm = FakeLLM(['"Diện tích của Resort Hải Vân 2 là bao nhiêu?"'])
    result = QueryRewriter(llm).rewrite(store.get("s"), "Thế còn diện tích?")
    assert result == "Diện tích của Resort Hải Vân 2 là bao nhiêu?"
    assert "Resort Hải Vân 2 ở đâu?" in llm.calls[0][0].content


def test_rewrite_falls_back_to_original_on_llm_error():
    store = SessionStore()
    store.append("s", "a", "b")
    rewriter = QueryRewriter(FakeLLM(error=LLMTimeout("slow")))
    assert rewriter.rewrite(store.get("s"), "câu hỏi") == "câu hỏi"
