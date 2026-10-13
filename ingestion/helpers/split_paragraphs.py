import logging
import re

from core.config import get_settings

logger = logging.getLogger("ingestion")

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+|\n+")


def _split_sentences(text: str, max_len: int) -> list[str]:
    """Split into sentences; a sentence longer than max_len is cut at a space."""
    sentences = []
    for sentence in _SENTENCE_END.split(text):
        sentence = sentence.strip()
        while len(sentence) > max_len:
            cut = sentence.rfind(" ", 0, max_len)
            if cut <= 0:
                cut = max_len
            sentences.append(sentence[:cut].strip())
            sentence = sentence[cut:].strip()
        if sentence:
            sentences.append(sentence)
    return sentences


def split_paragraphs(text: str, max_len: int | None = None, overlap: int | None = None) -> list[str]:
    """Pack sentences into chunks of at most max_len characters.

    Consecutive chunks share `overlap` trailing sentences so context isn't lost
    at the boundary. Defaults come from settings.chunking.
    """
    cfg = get_settings().chunking
    max_len = max_len or cfg.max_chars
    overlap = cfg.overlap_sentences if overlap is None else overlap

    if not text or not text.strip():
        logger.debug("Empty text provided to split_paragraphs")
        return []

    chunks: list[str] = []
    current: list[str] = []
    for sentence in _split_sentences(text, max_len):
        if current and len(" ".join([*current, sentence])) > max_len:
            chunks.append(" ".join(current))
            current = current[-overlap:] if overlap > 0 else []
            if current and len(" ".join([*current, sentence])) > max_len:
                current = []
        current.append(sentence)
    if current:
        chunks.append(" ".join(current))
    return chunks
