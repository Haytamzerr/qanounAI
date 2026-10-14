"""Measure the answers, not just the search.

For every test question we ask the full assistant and record:
- answered: it gave an answer rather than "not covered";
- correct citation: it cites at least one of the articles that really answer the question;
- verified: the citation check passed (no unknown source, no invented article number);
- refused with the answer in hand: an expected article was among the sources, yet it refused;
- time to answer.

Usage (needs the embedding model, Qdrant and a Gemini key):
    uv run python -m qanoun.generation.evaluate
    uv run python -m qanoun.generation.evaluate --questions eval/darija_holdout.jsonl --limit 5

The free Gemini tier allows a few requests per minute, so questions are spaced out (`--pause`).
"""

import argparse
import json
import time
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from statistics import mean, median

from qanoun.generation.answer import Answerer
from qanoun.retrieval.evaluate import EVAL_DIR, GROUP_ORDER, load_questions


@dataclass
class AnswerResult:
    id: str
    question: str
    language: str
    expected: list[str]
    status: str
    answer: str
    sources: list[str]
    cited: list[str]
    verified: bool
    problems: list[str]
    attempts: int
    model: str
    seconds: float
    error: str = ""

    @property
    def answered(self) -> bool:
        return self.status == "answered"

    @property
    def correct_citation(self) -> bool:
        return self.answered and bool(set(self.cited) & set(self.expected))

    @property
    def refused_with_answer_in_hand(self) -> bool:
        return not self.answered and not self.error and bool(set(self.sources) & set(self.expected))


def run(
    answerer: Answerer, questions: list[dict], pause: float = 0, log=print
) -> list[AnswerResult]:
    results = []
    for n, q in enumerate(questions, start=1):
        start = time.perf_counter()
        try:
            a = answerer.answer(q["question"])
            result = AnswerResult(
                q["id"], q["question"], q["language"], q["expected"], a.status, a.text,
                [s.id for s in a.sources], [s.id for s in a.cited_articles], a.verified,
                a.problems, a.attempts, a.model, time.perf_counter() - start,
            )  # fmt: skip
        except Exception as error:  # one failing question must not stop the whole run
            result = AnswerResult(
                q["id"], q["question"], q["language"], q["expected"], "error", "", [], [],
                False, [], 0, "", time.perf_counter() - start, f"{type(error).__name__}: {error}",
            )  # fmt: skip
        results.append(result)
        mark = "✓" if result.correct_citation else ("·" if not result.answered else "✗")
        log(f"{n:>3}/{len(questions)} {mark} {q['id']} {result.status} ({result.seconds:.1f} s)")
        if pause and n < len(questions):
            time.sleep(pause)
    return results


def _share_verified(results: list[AnswerResult]) -> float:
    """Among the answers given, the share whose citations passed the check."""
    answered = [r for r in results if r.answered]
    return mean(r.verified for r in answered) if answered else 0.0


def summarize(results: list[AnswerResult]) -> dict[str, dict[str, float]]:
    groups: dict[str, list[AnswerResult]] = defaultdict(list)
    for r in results:
        groups["all"].append(r)
        groups[r.language].append(r)
    return {
        name: {
            "questions": len(rs),
            "answered": mean(r.answered for r in rs),
            "correct citation": mean(r.correct_citation for r in rs),
            "verified": _share_verified(rs),
            "refused with answer in hand": mean(r.refused_with_answer_in_hand for r in rs),
            "errors": sum(bool(r.error) for r in rs),
            "median seconds": median(r.seconds for r in rs),
        }
        for name, rs in groups.items()
    }


def report(label: str, results: list[AnswerResult]) -> str:
    summary = summarize(results)
    names = sorted(summary, key=lambda n: GROUP_ORDER.index(n) if n in GROUP_ORDER else 99)
    models = ", ".join(sorted({r.model for r in results if r.model})) or "none"
    lines = [
        f"# Answer evaluation: {label}",
        "",
        f"{date.today().isoformat()} · {len(results)} questions · models: {models}",
        "",
        "| Group | Questions | Answered | Correct citation | Verified | Refused with answer "
        "in hand | Errors | Median s |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for name in names:
        s = summary[name]
        lines.append(
            f"| {name} | {s['questions']} | {s['answered']:.0%} | {s['correct citation']:.0%} | "
            f"{s['verified']:.0%} | {s['refused with answer in hand']:.0%} | {s['errors']} | "
            f"{s['median seconds']:.1f} |"
        )
    lines += ["", "## Every answer", ""]
    for r in results:
        verdict = "correct" if r.correct_citation else r.status
        lines += [f"### `{r.id}` ({r.language}) {verdict}", "", f"> {r.question}", ""]
        lines.append(r.error or r.answer)
        lines.append("")
        lines.append(f"cited: {', '.join(r.cited) or '—'} · expected: {', '.join(r.expected)}")
        if r.problems:
            lines.append(f"problems: {'; '.join(r.problems)}")
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    from qanoun.generation.ask import RETRIEVERS
    from qanoun.generation.llm import STATE_PATH, GeminiLLM, configure_logging

    parser = argparse.ArgumentParser(description="Evaluate full answers on a question set.")
    parser.add_argument("--questions", type=Path, default=None)
    parser.add_argument("--retriever", choices=list(RETRIEVERS), default="dense")
    parser.add_argument("--limit", type=int, default=None, help="only the first N questions")
    parser.add_argument("--pause", type=float, default=4.0, help="seconds between questions")
    args = parser.parse_args(argv)

    configure_logging()
    questions = load_questions(args.questions)[: args.limit]
    answerer = Answerer(RETRIEVERS[args.retriever](), GeminiLLM(state_path=STATE_PATH))
    results = run(answerer, questions, pause=args.pause)

    label = f"{args.retriever}" + ("" if args.questions is None else f"-{args.questions.stem}")
    out = EVAL_DIR / "reports" / f"answers-{label}-{date.today().isoformat()}"
    out.parent.mkdir(parents=True, exist_ok=True)
    text = report(label, results)
    out.with_suffix(".md").write_text(text, encoding="utf-8")
    with out.with_suffix(".jsonl").open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(asdict(r), ensure_ascii=False) + "\n")
    print("\n".join(text.split("\n## Every answer")[0].splitlines()[4:]))
    print(f"\nfull report: {out.with_suffix('.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
