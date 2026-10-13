import logging

import httpx
import ollama

from core.config import LLMSettings
from core.errors import LLMError, LLMTimeout, LLMUnavailable
from llm.base import BaseLLM, LLMResult

logger = logging.getLogger("llm")

DEFAULT_BASE_URL = "http://localhost:11434"


class OllamaLLM(BaseLLM):
    def __init__(self, cfg: LLMSettings):
        self._cfg = cfg
        self._client = ollama.Client(host=cfg.base_url or DEFAULT_BASE_URL, timeout=cfg.timeout)

    def generate(self, messages, *, temperature=None, max_tokens=None) -> LLMResult:
        try:
            response = self._client.chat(
                model=self._cfg.model,
                messages=[{"role": m.role, "content": m.content} for m in messages],
                options={
                    "temperature": self._cfg.temperature if temperature is None else temperature,
                    "num_predict": max_tokens or self._cfg.max_tokens,
                },
            )
        except httpx.TimeoutException as e:
            raise LLMTimeout(f"Ollama timed out after {self._cfg.timeout}s") from e
        except (httpx.ConnectError, ConnectionError) as e:
            raise LLMUnavailable(f"Cannot reach Ollama: {e}") from e
        except ollama.ResponseError as e:
            raise LLMError(f"Ollama error: {e}") from e

        return LLMResult(
            text=(response.message.content or "").strip(),
            model=self._cfg.model,
            input_tokens=response.prompt_eval_count,
            output_tokens=response.eval_count,
        )

    def ping(self) -> bool:
        try:
            self._client.list()
            return True
        except Exception:
            return False
