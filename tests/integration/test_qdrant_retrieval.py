import pytest
from qdrant_client import QdrantClient

from core.config import RetrievalSettings
from retrieval.bm25_index import Bm25Index
from retrieval.dense import DenseRetriever
from retrieval.hybrid import HybridRetriever
from tests.conftest import HashEmbedder, cid
from vectorstore.qdrant import ensure_collection, load_corpus, upsert_chunks

COLLECTION = "test_collection"


@pytest.fixture
def client(chunks):
    embedder = HashEmbedder()
    client = QdrantClient(":memory:")
    ensure_collection(client, COLLECTION, embedder.dimension)
    upsert_chunks(client, COLLECTION, chunks, embedder.embed_passages([c.text for c in chunks]))
    return client


def test_upsert_is_idempotent(client, chunks):
    embedder = HashEmbedder()
    upsert_chunks(client, COLLECTION, chunks, embedder.embed_passages([c.text for c in chunks]))
    assert client.count(COLLECTION).count == len(chunks)


def test_ensure_collection_recreate_clears_data(client):
    ensure_collection(client, COLLECTION, HashEmbedder.dimension, recreate=True)
    assert client.count(COLLECTION).count == 0


def test_load_corpus_round_trips_text_and_metadata(client, chunks):
    corpus = {c.id: c for c in load_corpus(client, COLLECTION, batch=2)}
    assert set(corpus) == {c.id for c in chunks}
    assert corpus[cid(3)].text == chunks[2].text
    assert corpus[cid(3)].metadata["interior_name"] == "Japandi"
    assert "text" not in corpus[cid(3)].metadata


def test_dense_search_returns_semantically_closest_chunk(client):
    dense = DenseRetriever(client, COLLECTION, HashEmbedder())
    hits = dense.search("phong cách Indochine Đông Dương", k=3)
    assert hits[0].chunk_id == cid(2)
    assert hits[0].metadata["type"] == "interior_style"


def test_hybrid_over_real_qdrant_finds_relevant_chunk(client):
    bm25 = Bm25Index(load_corpus(client, COLLECTION))
    retriever = HybridRetriever(
        DenseRetriever(client, COLLECTION, HashEmbedder()), bm25, RetrievalSettings(candidates_n=5)
    )
    hits = retriever.retrieve("giờ làm việc của công ty")
    assert hits[0].chunk_id == cid(4)
    assert hits[0].metadata["rrf_ranks"] is not None
