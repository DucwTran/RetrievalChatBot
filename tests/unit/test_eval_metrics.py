from core.schema import Hit
from evaluation.evaluate import is_refusal, parse_scores
from evaluation.metrics import is_relevant, precision_at_k, recall_at_k, reciprocal_rank, summarize_latency
from rag.prompts import NO_ANSWER


def h(**meta) -> Hit:
    return Hit(chunk_id=str(meta), text="t", score=0.0, metadata=meta)


REL = [{"project_id": 7}]
HITS = [h(project_id=1), h(project_id=7, chunk_type="specs"), h(project_id=7), h(type="news"), h(project_id=2)]


def test_is_relevant_requires_all_keys_of_one_filter():
    assert is_relevant(h(project_id=7, type="project"), [{"project_id": 7, "type": "project"}])
    assert not is_relevant(h(project_id=7), [{"project_id": 7, "type": "project"}])
    assert is_relevant(h(type="news"), [{"project_id": 7}, {"type": "news"}])  # any-of filters


def test_recall_is_hit_rate_within_k():
    assert recall_at_k(HITS, REL, k=2) == 1.0
    assert recall_at_k(HITS, REL, k=1) == 0.0


def test_mrr_uses_first_relevant_rank():
    assert reciprocal_rank(HITS, REL) == 0.5
    assert reciprocal_rank([h(project_id=1)], REL) == 0.0


def test_precision_at_k():
    assert precision_at_k(HITS, REL, k=5) == 2 / 5


def test_latency_summary():
    s = summarize_latency([10, 20, 30, 40, 100])
    assert s["p50"] == 30 and s["p95"] == 100 and s["mean"] == 40


def test_judge_output_parsing():
    assert parse_scores('Here: {"correctness": 4, "faithfulness": 5}') == (4, 5)
    assert parse_scores("no json") is None
    assert parse_scores('{"correctness": "x"}') is None


def test_refusal_detection():
    assert is_refusal(NO_ANSWER)
    assert is_refusal("Xin lỗi, mình không tìm thấy thông tin này.")
    assert not is_refusal("Dự án nằm ở Bình Dương.")
