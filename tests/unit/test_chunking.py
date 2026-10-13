from ingestion.helpers.ids import chunk_id
from ingestion.helpers.make_metadata import make_metadata
from ingestion.helpers.split_paragraphs import split_paragraphs


def test_chunk_id_is_deterministic():
    assert chunk_id("a.json", "overview", "text") == chunk_id("a.json", "overview", "text")


def test_chunk_id_changes_with_any_part():
    base = chunk_id("a.json", "overview", "text")
    assert base != chunk_id("b.json", "overview", "text")
    assert base != chunk_id("a.json", "description", "text")
    assert base != chunk_id("a.json", "overview", "other")


def test_make_metadata_merges_without_mutating_base():
    base = {"type": "project", "source": "projects.json"}
    meta = make_metadata(base, chunk_type="overview", priority=1)
    assert meta == {"type": "project", "source": "projects.json", "chunk_type": "overview", "priority": 1}
    assert "chunk_type" not in base


def test_split_empty_text():
    assert split_paragraphs("", max_len=50, overlap=1) == []
    assert split_paragraphs("   ", max_len=50, overlap=1) == []


def test_split_respects_max_len():
    text = ". ".join(f"Câu số {i} có nội dung khá dài" for i in range(20)) + "."
    chunks = split_paragraphs(text, max_len=80, overlap=1)
    assert len(chunks) > 1
    assert all(len(c) <= 80 for c in chunks)


def test_split_overlaps_consecutive_chunks():
    text = "Một. Hai. Ba. Bốn. Năm. Sáu."
    chunks = split_paragraphs(text, max_len=15, overlap=1)
    for prev, nxt in zip(chunks, chunks[1:]):
        assert prev.split(" ")[-1] in nxt  # last sentence of prev re-appears in next


def test_split_without_overlap_has_no_repeated_sentence():
    chunks = split_paragraphs("Một. Hai. Ba. Bốn.", max_len=10, overlap=0)
    assert " ".join(chunks).count("Hai.") == 1


def test_split_cuts_oversized_sentence():
    chunks = split_paragraphs("từ " * 100, max_len=40, overlap=0)
    assert all(len(c) <= 40 for c in chunks)
    assert len(chunks) > 1
