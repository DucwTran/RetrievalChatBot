from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ChatMessage:
    role: Literal["system", "user", "assistant"]
    content: str


@dataclass(frozen=True)
class LLMResult:
    text: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None


class BaseLLM(ABC):
    """The only thing the RAG pipeline knows about a language model."""

    @abstractmethod
    def generate(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResult:
        """Raise LLMTimeout / LLMUnavailable / LLMError on failure; never return error text."""

    @abstractmethod
    def ping(self) -> bool:
        """Cheap reachability check used by /health."""
