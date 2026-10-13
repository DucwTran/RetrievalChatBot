import logging

import openai

from core.config import LLMSettings
from core.errors import LLMError, LLMTimeout, LLMUnavailable
from llm.base import BaseLLM, LLMResult

logger = logging.getLogger("llm")


class OpenAILLM(BaseLLM):
    def __init__(self, cfg: LLMSettings):
        if not cfg.api_key:
            raise ValueError("LLM__API_KEY is required when LLM__PROVIDER=openai")
        self._cfg = cfg
        self._client = openai.OpenAI(api_key=cfg.api_key, base_url=cfg.base_url, timeout=cfg.timeout)

    def generate(self, messages, *, temperature=None, max_tokens=None) -> LLMResult:
        try:
            response = self._client.chat.completions.create(
                model=self._cfg.model,
                messages=[{"role": m.role, "content": m.content} for m in messages],
                temperature=self._cfg.temperature if temperature is None else temperature,
                max_tokens=max_tokens or self._cfg.max_tokens,
            )
        except openai.APITimeoutError as e:
            raise LLMTimeout(f"OpenAI timed out after {self._cfg.timeout}s") from e
        except openai.APIConnectionError as e:
            raise LLMUnavailable(f"Cannot reach OpenAI: {e}") from e
        except openai.APIError as e:
            raise LLMError(f"OpenAI error: {e}") from e

        usage = response.usage
        return LLMResult(
            text=(response.choices[0].message.content or "").strip(),
            model=self._cfg.model,
            input_tokens=usage.prompt_tokens if usage else None,
            output_tokens=usage.completion_tokens if usage else None,
        )

    def ping(self) -> bool:
        try:
            self._client.models.list()
            return True
        except Exception:
            return False
