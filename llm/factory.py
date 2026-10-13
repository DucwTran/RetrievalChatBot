from core.config import LLMSettings
from llm.base import BaseLLM
from llm.ollama import OllamaLLM
from llm.openai import OpenAILLM

PROVIDERS: dict[str, type[BaseLLM]] = {
    "ollama": OllamaLLM,
    "openai": OpenAILLM,
}


def get_llm(cfg: LLMSettings) -> BaseLLM:
    """Add a provider = one new class + one entry in PROVIDERS; the pipeline never changes."""
    try:
        provider = PROVIDERS[cfg.provider]
    except KeyError:
        raise ValueError(f"Unknown LLM provider '{cfg.provider}'. Available: {sorted(PROVIDERS)}") from None
    return provider(cfg)
