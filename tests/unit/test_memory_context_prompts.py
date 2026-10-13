from core.schema import Hit
from memory.session import SessionStore
from rag.context import build_context
from rag.prompts import SYSTEM_PROMPT, build_messages


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


# ---- session memory ----------------------------------------------------------

def test_unknown_session_is_empty():
    assert SessionStore().get("nope") == []


def test_keeps_only_last_five_messages():
    store = SessionStore(max_messages=5)
    store.append("s", "q1", "a1")
    store.append("s", "q2", "a2")
    store.append("s", "q3", "a3")  # 6 messages -> the oldest ("q1") is dropped
    contents = [m.content for m in store.get("s")]
    assert contents == ["a1", "q2", "a2", "q3", "a3"]


def test_sessions_are_isolated():
    store = SessionStore()
    store.append("a", "hi", "hello")
    assert store.get("b") == []


def test_delete_session():
    store = SessionStore()
    store.append("a", "hi", "hello")
    assert store.delete("a") is True
    assert store.get("a") == []
    assert store.delete("a") is False


def test_ttl_expires_idle_sessions():
    clock = Clock()
    store = SessionStore(ttl_seconds=60, clock=clock)
    store.append("a", "hi", "hello")
    clock.now += 61
    assert store.get("a") == []


def test_max_sessions_evicts_least_recently_used():
    clock = Clock()
    store = SessionStore(max_sessions=2, clock=clock)
    store.append("a", "1", "1")
    store.append("b", "2", "2")
    store.append("c", "3", "3")
    assert store.get("a") == []
    assert store.get("b") and store.get("c")


def test_get_returns_copy():
    store = SessionStore()
    store.append("a", "hi", "hello")
    store.get("a").clear()
    assert len(store.get("a")) == 2


# ---- context -----------------------------------------------------------------

def h(cid, text, score=None, **meta):
    metadata = dict(meta)
    if score is not None:
        metadata["rerank_score"] = score
    return Hit(chunk_id=cid, text=text, score=0.5, metadata=metadata)


def test_context_dedups_by_id_and_text():
    hits = [h("1", "Nội dung A"), h("1", "Nội dung A"), h("2", "Nội   dung  A")]
    ctx = build_context(hits, max_chars=1000)
    assert len(ctx.sources) == 1


def test_context_filters_low_rerank_scores():
    hits = [h("1", "tốt", 0.9), h("2", "kém", 0.01)]
    ctx = build_context(hits, max_chars=1000, min_score=0.1)
    assert [s.snippet for s in ctx.sources] == ["tốt"]


def test_context_ignores_threshold_when_not_reranked():
    ctx = build_context([h("1", "chưa rerank")], max_chars=1000, min_score=0.9)
    assert len(ctx.sources) == 1


def test_context_respects_budget_without_cutting_chunks():
    hits = [h("1", "a" * 60), h("2", "b" * 60), h("3", "c" * 20)]
    ctx = build_context(hits, max_chars=100)
    assert [s.snippet for s in ctx.sources] == ["a" * 60, "c" * 20]
    assert "b" * 60 not in ctx.text


def test_context_labels_match_sources_and_carry_metadata():
    hits = [h("1", "Diện tích 300 m2", project_name="Biệt thự Hòa Bình", type="project",
              project_slug="biet-thu", project_image_url="http://img/1.jpg")]
    ctx = build_context(hits, max_chars=1000)
    assert ctx.text.startswith("[1] Biệt thự Hòa Bình\nDiện tích 300 m2")
    source = ctx.sources[0]
    assert (source.title, source.type, source.slug, source.image_url) == (
        "Biệt thự Hòa Bình", "project", "biet-thu", "http://img/1.jpg")


def test_context_empty_when_nothing_passes():
    assert build_context([], max_chars=100).sources == []


# ---- prompts -----------------------------------------------------------------

def test_messages_layout_without_history():
    msgs = build_messages([], "NGỮ CẢNH", "Câu hỏi?")
    assert [m.role for m in msgs] == ["system", "user"]
    assert msgs[0].content == SYSTEM_PROMPT
    assert "NGỮ CẢNH" in msgs[1].content and "Câu hỏi?" in msgs[1].content


def test_messages_put_history_between_system_and_question():
    store = SessionStore()
    store.append("s", "Resort Hải Vân 2 ở đâu?", "Ở Đà Nẵng.")
    msgs = build_messages(store.get("s"), "CTX", "Thế còn diện tích?")
    assert [m.role for m in msgs] == ["system", "user", "assistant", "user"]
    assert msgs[1].content == "Resort Hải Vân 2 ở đâu?"
    assert "Thế còn diện tích?" in msgs[-1].content


def test_system_prompt_forbids_using_history_as_facts():
    assert "KHÔNG phải nguồn thông tin" in SYSTEM_PROMPT
