"""Score a search method on the retrieval test set and write a report.

Usage:
    uv run python -m qanoun.retrieval.evaluate --method bm25

The test set (eval/retrieval_set.jsonl) lists questions with the articles that answer them.
Results are broken down by language, because Darija is the hard case we must track.
"""

import argparse
import json
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
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


def bm25_searcher() -> Searcher:
    index = BM25Index.build({a.id: search_text(a) for a in load_articles()})
    return lambda question, k: [doc for doc, _ in index.search(question, k)]


SEARCHERS: dict[str, Callable[[], Searcher]] = {"bm25": bm25_searcher}


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
    order = ["all", "ar", "fr", "darija-ar", "darija-latn"]
    for name in sorted(summary, key=lambda n: order.index(n) if n in order else 99):
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate a search method.")
    parser.add_argument("--method", choices=sorted(SEARCHERS), default="bm25")
    args = parser.parse_args(argv)

    results = run(SEARCHERS[args.method](), load_questions())
    text = report(args.method, results)
    out = EVAL_DIR / "reports" / f"retrieval-{args.method}-{date.today().isoformat()}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(text)
    print(f"report written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
