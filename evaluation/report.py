"""Console report for evaluation results (markdown tables)."""
from evaluation.metrics import K


def _fmt(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.2f}"


def print_report(retrieval: dict, generation: dict | None) -> None:
    print(f"\n### Retrieval (top-{K}, in-scope questions)\n")
    print(f"| mode | n | Recall@{K} | MRR | Precision@{K} |\n|---|---|---|---|---|")
    for mode, rep in retrieval.items():
        m = rep["metrics"]["ALL"]
        print(f"| {mode} | {m['n']} | {m[f'recall@{K}']:.3f} | {m['mrr']:.3f} | {m[f'precision@{K}']:.3f} |")

    print(f"\n### Recall@{K} / MRR by category\n")
    cats = [c for c in next(iter(retrieval.values()))["metrics"] if c != "ALL"]
    print("| mode | " + " | ".join(cats) + " |\n|---|" + "---|" * len(cats))
    for mode, rep in retrieval.items():
        cells = [f"{rep['metrics'][c][f'recall@{K}']:.2f} / {rep['metrics'][c]['mrr']:.2f}" for c in cats]
        print(f"| {mode} | " + " | ".join(cells) + " |")

    print("\n### Retrieval latency (ms)\n")
    print("| mode | retrieval p50 | retrieval p95 | rerank p50 | rerank p95 |\n|---|---|---|---|---|")
    for mode, rep in retrieval.items():
        lat = rep["latency_ms"]
        r, rr = lat.get("retrieval", {}), lat.get("rerank", {})
        print(f"| {mode} | {r.get('p50', 0):.0f} | {r.get('p95', 0):.0f} | {rr.get('p50', 0):.0f} | {rr.get('p95', 0):.0f} |")

    if generation:
        g = generation
        print(f"\n### Generation (answer={g['answer_model']}, judge={g['judge_model']})\n")
        print(f"- correctness (1-5): {_fmt(g['correctness_mean'])}\n- faithfulness (1-5): {_fmt(g['faithfulness_mean'])}")
        print(f"- false refusals on in-scope questions: {_fmt(g['false_refusal_rate'])}")
        print(f"- correct refusals on out-of-scope questions: {_fmt(g['out_of_scope_refusal_rate'])}")
        print(f"- LLM errors: {g['errors']}\n\n| stage | p50 ms | p95 ms |\n|---|---|---|")
        for stage, v in g["latency_ms"].items():
            print(f"| {stage} | {v['p50']:.0f} | {v['p95']:.0f} |")
