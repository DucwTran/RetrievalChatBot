import logging
import time
from dataclasses import dataclass, field
from typing import Protocol

from core.config import ContextSettings, RerankSettings
from core.schema import Hit, Source
from llm.base import BaseLLM
from memory.session import SessionStore
from rag.context import build_context
from rag.prompts import NO_ANSWER, build_messages
from rag.query_rewrite import QueryRewriter
from rag.timing import Timings
from reranking.base import BaseReranker

logger = logging.getLogger("rag")


class Retriever(Protocol):
    def retrieve(self, query: str) -> list[Hit]: ...


@dataclass
class ChatResult:
    answer: str
    sources: list[Source] = field(default_factory=list)
    standalone_query: str = ""
    context: str = ""  # exactly what the LLM saw (used by evaluation to judge faithfulness)
    timings: Timings = field(default_factory=Timings)
    input_tokens: int | None = None
    output_tokens: int | None = None


class RAGPipeline:
    """Orchestrates one chat turn. All collaborators are injected, so each can be faked in tests."""

    def __init__(
        self,
        retriever: Retriever,
        reranker: BaseReranker,
        llm: BaseLLM,
        rewriter: QueryRewriter,
        sessions: SessionStore,
        rerank_cfg: RerankSettings,
        context_cfg: ContextSettings,
    ):
        self._retriever = retriever
        self._reranker = reranker
        self._llm = llm
        self._rewriter = rewriter
        self._sessions = sessions
        self._rerank_cfg = rerank_cfg
        self._context_cfg = context_cfg

    def answer(self, session_id: str, message: str) -> ChatResult:
        result = ChatResult(answer="")
        t = result.timings
        error: str | None = None
        candidates: list[Hit] = []
        start = time.perf_counter()
        try:
            history = self._sessions.get(session_id)  # 1. memory

            with t.measure("rewrite"):  # 2. history -> standalone query (only when there is history)
                result.standalone_query = self._rewriter.rewrite(history, message)

            with t.measure("retrieval"):  # 3. dense + BM25 + RRF, using the standalone query
                candidates = self._retriever.retrieve(result.standalone_query)
            with t.measure("rerank"):  # 4. cross-encoder on the candidates
                ranked = self._reranker.rerank(
                    result.standalone_query, candidates, self._rerank_cfg.top_k
                )

            context = build_context(  # 5. dedup / filter / format
                ranked,
                max_chars=self._context_cfg.max_chars,
                min_score=self._rerank_cfg.min_score,
            )

            if not context.sources:  # nothing relevant: don't ask the LLM to guess
                result.answer = NO_ANSWER
            else:
                with t.measure("llm"):  # 6. history + context + original question
                    llm_result = self._llm.generate(build_messages(history, context.text, message))
                result.answer = llm_result.text
                result.sources = context.sources
                result.context = context.text
                result.input_tokens = llm_result.input_tokens
                result.output_tokens = llm_result.output_tokens

            self._sessions.append(session_id, message, result.answer)  # 7. only after success
            return result
        except Exception as e:
            error = type(e).__name__
            raise
        finally:
            t["total"] = (time.perf_counter() - start) * 1000
            logger.info(
                "chat session=%s query=%r standalone=%r candidates=%s context=%s %s tokens_in=%s tokens_out=%s error=%s",
                session_id, message, result.standalone_query,
                len(candidates),
                len(result.sources),
                " ".join(f"t_{k}={v:.0f}ms" for k, v in t.items()),
                result.input_tokens, result.output_tokens, error,
            )
