import math
import re
import unicodedata
from collections import Counter, defaultdict
from collections.abc import Iterable

from core.schema import Chunk, Hit

_TOKEN = re.compile(r"\w+", re.UNICODE)


def tokenize(text: str) -> list[str]:
    """Lowercase word tokens. Vietnamese syllables are whitespace separated, so
    a plain \\w+ split is a reasonable baseline."""
    return _TOKEN.findall(unicodedata.normalize("NFC", text).lower())


class Bm25Index:
    """In-memory BM25 (Okapi) over the whole corpus, backed by an inverted index."""

    def __init__(self, chunks: Iterable[Chunk], k1: float = 1.5, b: float = 0.75):
        self._k1 = k1
        self._b = b
        self._chunks: list[Chunk] = []
        self._doc_len: list[int] = []
        self._postings: dict[str, list[tuple[int, int]]] = defaultdict(list)

        for chunk in chunks:
            tokens = tokenize(chunk.text)
            if not tokens:
                continue
            doc_idx = len(self._chunks)
            self._chunks.append(chunk)
            self._doc_len.append(len(tokens))
            for term, tf in Counter(tokens).items():
                self._postings[term].append((doc_idx, tf))

        self._n = len(self._chunks)
        self._avg_len = sum(self._doc_len) / self._n if self._n else 0.0

    def __len__(self) -> int:
        return self._n

    def _idf(self, term: str) -> float:
        df = len(self._postings[term])
        return math.log((self._n - df + 0.5) / (df + 0.5) + 1)

    def search(self, query: str, k: int) -> list[Hit]:
        scores: dict[int, float] = defaultdict(float)
        for term in set(tokenize(query)):
            if term not in self._postings:
                continue
            idf = self._idf(term)
            for doc_idx, tf in self._postings[term]:
                norm = 1 - self._b + self._b * self._doc_len[doc_idx] / self._avg_len
                scores[doc_idx] += idf * tf * (self._k1 + 1) / (tf + self._k1 * norm)

        top = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:k]
        return [
            Hit(
                chunk_id=self._chunks[i].id,
                text=self._chunks[i].text,
                score=score,
                metadata=dict(self._chunks[i].metadata),
            )
            for i, score in top
        ]
