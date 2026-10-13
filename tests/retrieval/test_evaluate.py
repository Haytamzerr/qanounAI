"""Metrics and the evaluation report, on hand-made results."""

import pytest

from qanoun.retrieval.evaluate import QuestionResult, report, run, summarize
from qanoun.retrieval.metrics import hit_at_k, recall_at_k, reciprocal_rank


def test_metrics_on_one_ranking():
    ranked, relevant = ["a", "b", "c", "d", "e", "f"], {"c", "f"}
    assert hit_at_k(ranked, relevant, 5) == 1.0
    assert recall_at_k(ranked, relevant, 5) == 0.5
    assert reciprocal_rank(ranked, relevant) == pytest.approx(1 / 3)
    assert reciprocal_rank(["x"], relevant) == 0.0


def test_summary_and_report_by_language():
    questions = [
        {"id": "q1", "question": "سؤال", "language": "ar", "expected": ["a"]},
        {"id": "q2", "question": "chno?", "language": "darija-latn", "expected": ["b"]},
    ]
    results = run(lambda q, k: ["a", "x"], questions)
    summary = summarize(results)
    assert summary["all"]["hit@5"] == 0.5
    assert summary["ar"]["mrr"] == 1.0
    assert summary["darija-latn"]["hit@5"] == 0.0
    text = report("fake", results)
    assert "| ar | 1 | 100% |" in text
    assert "`q2` (darija-latn)" in text  # misses are listed for error analysis


def test_question_result_relevant_set():
    r = QuestionResult("q", "?", "fr", ["a", "b"], [])
    assert r.relevant == {"a", "b"}
