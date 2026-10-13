"""Score a search method on the retrieval test set and write a report.

Usage:
    uv run python -m qanoun.retrieval.evaluate --method bm25
    uv run python -m qanoun.retrieval.evaluate --method bm25 dense hybrid   # compare methods

`dense` and `hybrid` need Qdrant running and loaded (see qanoun.retrieval.index).

The test set (eval/retrieval_set.jsonl) lists questions with the articles that answer them.
Results are broken down by language, because Darija is the hard case we must track.
"""

import argparse
import json
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from functools import cache
from pathlib import Path
from statistics import mean

from qanoun.config import PROJECT_ROOT
from qanoun.retrieval.bm25 import BM25Index
from qanoun.retrieval.corpus import load_articles, search_text
from qanoun.retrieval.metrics import hit_at_k, recall_at_k, reciprocal_rank

EVAL_DIR = PROJECT_ROOT / "eval"
K = 5
Searcher = Callable[[str, int], list[str]]  # (question, k) -> ranked article ids


@dataclass
class QuestionResult:
    id: str
    question: str
    language: str
    expected: list[str]
    ranked: list[str]

    @property
    def relevant(self) -> set[str]:
        return set(self.expected)


def load_questions(path: Path | None = None) -> list[dict]:
    path = path or EVAL_DIR / "retrieval_set.jsonl"
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


@cache
def _bm25() -> BM25Index:
    return BM25Index.build({a.id: search_text(a) for a in load_articles()})


@cache
def _dense():
    # Imported here: loading torch and the model takes a while and isn't needed for BM25.
    from qanoun.retrieval.embeddings import BGEM3Embedder
    from qanoun.retrieval.search import DenseSearcher
    from qanoun.retrieval.vector_store import ArticleStore

    store = ArticleStore.connect()
    expected = len(load_articles())
    if store.count() != expected:
        raise SystemExit(
            f"Qdrant holds {store.count()} articles, the corpus {expected}: "
            "run `uv run python -m qanoun.retrieval.index` first."
        )
    return DenseSearcher(BGEM3Embedder(), store)


def bm25_searcher() -> Searcher:
    index = _bm25()
    return lambda question, k: [doc for doc, _ in index.search(question, k)]


def dense_searcher() -> Searcher:
    return _dense()


def hybrid_searcher() -> Searcher:
    from qanoun.retrieval.search import HybridSearcher

    return HybridSearcher(_bm25(), _dense())


SEARCHERS: dict[str, Callable[[], Searcher]] = {
    "bm25": bm25_searcher,
    "dense": dense_searcher,
    "hybrid": hybrid_searcher,
}


def run(searcher: Searcher, questions: list[dict], depth: int = 10) -> list[QuestionResult]:
    return [
        QuestionResult(
            q["id"], q["question"], q["language"], q["expected"], searcher(q["question"], depth)
        )
        for q in questions
    ]


def summarize(results: list[QuestionResult]) -> dict[str, dict[str, float]]:
    """Average hit@5, recall@5 and MRR, overall and per language."""
    groups: dict[str, list[QuestionResult]] = defaultdict(list)
    for r in results:
        groups["all"].append(r)
        groups[r.language].append(r)
    return {
        name: {
            "questions": len(rs),
            f"hit@{K}": mean(hit_at_k(r.ranked, r.relevant, K) for r in rs),
            f"recall@{K}": mean(recall_at_k(r.ranked, r.relevant, K) for r in rs),
            "mrr": mean(reciprocal_rank(r.ranked, r.relevant) for r in rs),
        }
        for name, rs in groups.items()
    }


def report(method: str, results: list[QuestionResult]) -> str:
    summary = summarize(results)
    lines = [
        f"# Retrieval evaluation: {method}",
        "",
        f"{date.today().isoformat()} · {len(results)} questions · top {K}",
        "",
        f"| Group | Questions | Hit@{K} | Recall@{K} | MRR |",
        "| --- | --- | --- | --- | --- |",
    ]
    for name in _ordered(summary):
        s = summary[name]
        lines.append(
            f"| {name} | {s['questions']} | {s[f'hit@{K}']:.0%} | "
            f"{s[f'recall@{K}']:.0%} | {s['mrr']:.2f} |"
        )
    misses = [r for r in results if not hit_at_k(r.ranked, r.relevant, K)]
    lines += ["", f"## Misses ({len(misses)}): no relevant article in the top {K}", ""]
    for r in misses:
        found = ", ".join(r.ranked[:3]) or "nothing"
        lines.append(
            f"- `{r.id}` ({r.language}) {r.question} → expected {r.expected[0]}…, got {found}"
        )
    return "\n".join(lines) + "\n"


GROUP_ORDER = ["all", "ar", "fr", "darija-ar", "darija-latn"]


def _ordered(groups) -> list[str]:
    return sorted(groups, key=lambda n: GROUP_ORDER.index(n) if n in GROUP_ORDER else 99)


def comparison(results_by_method: dict[str, list[QuestionResult]]) -> str:
    """One row per method, hit@5 overall and per language: the table for the README."""
    summaries = {method: summarize(results) for method, results in results_by_method.items()}
    groups = _ordered({g for s in summaries.values() for g in s})
    lines = [
        f"# Retrieval comparison, hit@{K}",
        "",
        f"{date.today().isoformat()} · " + ", ".join(summaries),
        "",
        "| Method | " + " | ".join(groups) + " | MRR |",
        "| --- " * (len(groups) + 2) + "|",
    ]
    for method, summary in summaries.items():
        cells = [f"{summary[g][f'hit@{K}']:.0%}" if g in summary else "–" for g in groups]
        lines.append(f"| {method} | " + " | ".join(cells) + f" | {summary['all']['mrr']:.2f} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate a search method.")
    parser.add_argument("--method", nargs="+", choices=list(SEARCHERS), default=["bm25"])
    args = parser.parse_args(argv)

    reports_dir = EVAL_DIR / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    questions = load_questions()
    results_by_method = {}
    for method in args.method:
        results = results_by_method[method] = run(SEARCHERS[method](), questions)
        text = report(method, results)
        out = reports_dir / f"retrieval-{method}-{today}.md"
        out.write_text(text, encoding="utf-8")
        print(text)
        print(f"report written to {out}\n")
    if len(results_by_method) > 1:
        text = comparison(results_by_method)
        out = reports_dir / f"retrieval-comparison-{today}.md"
        out.write_text(text, encoding="utf-8")
        print(text)
        print(f"comparison written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
