import logging
from collections.abc import Sequence

from core.errors import LLMError
from llm.base import BaseLLM, ChatMessage
from memory.session import Message
from rag.prompts import REWRITE_PROMPT, format_history

logger = logging.getLogger("rag")


class QueryRewriter:
    """Turns a follow-up ("Thế còn diện tích?") into a standalone search query."""

    def __init__(self, llm: BaseLLM):
        self._llm = llm

    def rewrite(self, history: Sequence[Message], question: str) -> str:
        if not history:
            return question
        prompt = REWRITE_PROMPT.format(history=format_history(history), question=question)
        try:
            result = self._llm.generate([ChatMessage("user", prompt)], temperature=0.0, max_tokens=96)
        except LLMError as e:
            logger.warning(f"Query rewrite failed, using original question: {e}")
            return question
        rewritten = result.text.strip().strip('"')
        return rewritten or question
