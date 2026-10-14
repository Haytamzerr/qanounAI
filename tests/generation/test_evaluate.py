from qanoun.generation.answer import Answerer
from qanoun.generation.evaluate import report, run, summarize

from ..retrieval.test_search import ARTICLES
from .test_answer import ScriptedLLM, ok

QUESTIONS = [
    {"id": "q1", "question": "chhal dyal lconji?", "language": "darija-latn",
     "expected": ["loi-65-99-ar-art-231"]},
    {"id": "q2", "question": "Période d'essai ?", "language": "fr",
     "expected": ["loi-65-99-ar-art-13"]},
    {"id": "q3", "question": "Âge du mariage ?", "language": "fr",
     "expected": ["loi-70-03-ar-art-19"]},
    {"id": "q4", "question": "boom", "language": "fr", "expected": ["x"]},
]  # fmt: skip


class Boom(ScriptedLLM):
    def generate(self, system, user, *, json_schema=None):
        if "boom" in user:
            raise RuntimeError("API down")
        return super().generate(system, user, json_schema=json_schema)


def test_metrics_on_scripted_answers():
    llm = Boom(
        ok("3ndek l7e9 [2].", used=[2]),  # q1: cites 231, the expected one
        ok("La période… [2].", used=[2]),  # q2: cites 231, wrong article
        {"status": "not_covered", "answer": "", "used_sources": []},  # q3: refuses; 19 was given
    )
    results = run(Answerer(lambda q, k: ARTICLES[:k], llm, k=4), QUESTIONS, log=lambda _: None)
    assert [r.correct_citation for r in results] == [True, False, False, False]
    assert results[2].refused_with_answer_in_hand
    assert results[3].error == "RuntimeError: API down"  # the run went on

    fr = summarize(results)["fr"]
    assert fr["questions"] == 3 and fr["errors"] == 1
    assert fr["answered"] == 1 / 3
    text = report("test", results)
    assert "| all | 4 | 75% | 50% | 25% |" in text  # q1-q3 had an expected article in the sources
    assert "### `q1` (darija-latn) correct" in text
