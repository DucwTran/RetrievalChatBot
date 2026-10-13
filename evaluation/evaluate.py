"""Evaluate retrieval (and optionally generation) on evaluation/dataset.json.

Retrieval:   python -m evaluation.evaluate
Generation:  python -m evaluation.evaluate --generate [--judge-model qwen2.5:7b]

Retrieval modes compared: dense, bm25, hybrid (RRF), hybrid+rerank.
Metrics: Recall@5 (hit rate), MRR, Precision@5, and per-stage latency.
"""
import argparse
import json
import re
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from api.bootstrap import RetrievalStack, build_retrieval
from core.config import get_settings
from core.errors import LLMError
from core.schema import Hit
from evaluation.metrics import K, precision_at_k, recall_at_k, reciprocal_rank, summarize_latency
from evaluation.report import print_report
from llm.base import ChatMessage
from llm.factory import get_llm
from memory.session import SessionStore
from rag.pipeline import RAGPipeline
from rag.prompts import NO_ANSWER
from rag.query_rewrite import QueryRewriter

DATASET = Path(__file__).parent / "dataset.json"
RESULTS_DIR = Path(__file__).parent / "results"
MODES = ["dense", "bm25", "hybrid", "hybrid+rerank"]

JUDGE_PROMPT = """You are grading a chatbot answer. Use ONLY the information below.

Question: {question}
Reference answer: {expected}
Retrieved context given to the chatbot:
{context}

Chatbot answer: {answer}

Score each from 1 (worst) to 5 (best):
- correctness: does the chatbot answer agree with the reference answer?
- faithfulness: is every claim in the chatbot answer supported by the retrieved context (no invented facts)?

Reply with JSON only: {{"correctness": <1-5>, "faithfulness": <1-5>}}"""


def load_dataset(limit: int | None) -> list[dict]:
    data = json.loads(DATASET.read_text(encoding="utf-8"))
    return data[:limit] if limit else data


def fmt_history(item: dict) -> list[tuple[str, str]]:
    """[(user, assistant), ...] pairs from the dataset's flat history list."""
    h = item.get("history", [])
    return [(h[i]["content"], h[i + 1]["content"]) for i in range(0, len(h) - 1, 2)]


def standalone_queries(items: list[dict], rewriter: QueryRewriter | None) -> dict[int, str]:
    """Follow-ups are rewritten with their history, exactly as the pipeline does."""
    store = SessionStore()
    queries = {}
    for item in items:
        history = []
        if rewriter and item.get("history"):
            store.delete("tmp")
            for user, assistant in fmt_history(item):
                store.append("tmp", user, assistant)
            history = store.get("tmp")
        queries[item["id"]] = rewriter.rewrite(history, item["question"]) if rewriter else item["question"]
    return queries


def retrieve(mode: str, stack: RetrievalStack, query: str, times: dict[str, list[float]]) -> list[Hit]:
    t0 = time.perf_counter()
    if mode == "dense":
        hits = stack.dense.search(query, K)
    elif mode == "bm25":
        hits = stack.bm25.search(query, K)
    else:
        hits = stack.hybrid.retrieve(query)
    times["retrieval"].append((time.perf_counter() - t0) * 1000)
    if mode == "hybrid+rerank":
        t1 = time.perf_counter()
        hits = stack.reranker.rerank(query, hits, K)
        times["rerank"].append((time.perf_counter() - t1) * 1000)
    return hits[:K]


def evaluate_retrieval(items, queries, stack) -> dict:
    scored = [i for i in items if i["relevant"]]
    report = {}
    for mode in MODES:
        times: dict[str, list[float]] = defaultdict(list)
        per_cat: dict[str, list[tuple[float, float, float]]] = defaultdict(list)
        for item in scored:
            hits = retrieve(mode, stack, queries[item["id"]], times)
            row = (
                recall_at_k(hits, item["relevant"], K),
                reciprocal_rank(hits, item["relevant"]),
                precision_at_k(hits, item["relevant"], K),
            )
            per_cat[item["category"]].append(row)
            per_cat["ALL"].append(row)
        report[mode] = {
            "metrics": {
                cat: {
                    "n": len(rows),
                    f"recall@{K}": sum(r[0] for r in rows) / len(rows),
                    "mrr": sum(r[1] for r in rows) / len(rows),
                    f"precision@{K}": sum(r[2] for r in rows) / len(rows),
                }
                for cat, rows in per_cat.items()
            },
            "latency_ms": {stage: summarize_latency(v) for stage, v in times.items()},
        }
    return report


def mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def parse_scores(text: str) -> tuple[int, int] | None:
    match = re.search(r"\{.*?\}", text, re.S)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
        return int(data["correctness"]), int(data["faithfulness"])
    except (ValueError, KeyError, TypeError):
        return None


def is_refusal(answer: str) -> bool:
    return answer.strip() == NO_ANSWER or "không tìm thấy" in answer.lower()


def evaluate_generation(items, stack, judge_model: str | None) -> dict:
    settings = get_settings()
    llm = get_llm(settings.llm)
    judge = get_llm(settings.llm.model_copy(update={"model": judge_model})) if judge_model else llm
    rows, stage_times = [], defaultdict(list)

    for item in items:
        sessions = SessionStore()
        pipeline = RAGPipeline(
            stack.hybrid, stack.reranker, llm, QueryRewriter(llm), sessions, settings.rerank, settings.context
        )
        sid = f"eval-{item['id']}"
        for user, assistant in fmt_history(item):
            sessions.append(sid, user, assistant)
        try:
            result = pipeline.answer(sid, item["question"])
        except LLMError as e:
            rows.append({"id": item["id"], "category": item["category"], "error": str(e)})
            continue
        for stage, ms in result.timings.items():
            stage_times[stage].append(ms)

        row = {
            "id": item["id"], "category": item["category"], "question": item["question"],
            "standalone_query": result.standalone_query, "answer": result.answer,
            "refused": is_refusal(result.answer),
        }
        if item["category"] != "out_of_scope":
            try:
                verdict = judge.generate(
                    [ChatMessage("user", JUDGE_PROMPT.format(
                        question=item["question"], expected=item["expected_answer"],
                        context=result.context or "(empty)", answer=result.answer))],
                    temperature=0.0, max_tokens=60,
                ).text
                scores = parse_scores(verdict)
            except LLMError:
                scores = None
            if scores:
                row["correctness"], row["faithfulness"] = scores
        rows.append(row)
        print(f"  [{item['id']:>2}] {item['category']:<12} refused={row['refused']!s:<5} {result.answer[:70]!r}")

    answered = [r for r in rows if "error" not in r]
    in_scope = [r for r in answered if r["category"] != "out_of_scope"]
    out_scope = [r for r in answered if r["category"] == "out_of_scope"]
    graded = [r for r in in_scope if "correctness" in r]
    return {
        "judge_model": judge_model or settings.llm.model,
        "answer_model": settings.llm.model,
        "n_in_scope": len(in_scope),
        "correctness_mean": mean([r["correctness"] for r in graded]),
        "faithfulness_mean": mean([r["faithfulness"] for r in graded]),
        "false_refusal_rate": mean([float(r["refused"]) for r in in_scope]),
        "out_of_scope_refusal_rate": mean([float(r["refused"]) for r in out_scope]),
        "errors": len(rows) - len(answered),
        "latency_ms": {stage: summarize_latency(v) for stage, v in stage_times.items()},
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--generate", action="store_true", help="also run the full pipeline and LLM-judge answers")
    parser.add_argument("--judge-model", help="model used to grade answers (default: the answering model)")
    parser.add_argument("--no-rewrite", action="store_true", help="skip follow-up rewriting (ablation)")
    parser.add_argument("--limit", type=int, help="only the first N questions")
    args = parser.parse_args()

    settings = get_settings()
    items = load_dataset(args.limit)
    stack = build_retrieval(settings)
    rewriter = None if args.no_rewrite else QueryRewriter(get_llm(settings.llm))

    print(f"Evaluating {len(items)} questions ...")
    retrieval = evaluate_retrieval(items, standalone_queries(items, rewriter), stack)
    generation = evaluate_generation(items, stack, args.judge_model) if args.generate else None
    print_report(retrieval, generation)

    RESULTS_DIR.mkdir(exist_ok=True)
    out = RESULTS_DIR / f"{datetime.now():%Y%m%d-%H%M%S}.json"
    out.write_text(
        json.dumps({"retrieval": retrieval, "generation": generation}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nSaved {out}")


if __name__ == "__main__":
    main()
