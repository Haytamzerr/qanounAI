"""The whole answer pipeline with a scripted model and a fixed retriever."""

import json

from qanoun.generation.answer import Answerer
from qanoun.generation.ask import render

from ..retrieval.test_search import ARTICLES


class ScriptedLLM:
    name = "scripted"

    def __init__(self, *replies: dict | str):
        self.replies = list(replies)
        self.prompts: list[tuple[str, str]] = []

    def generate(self, system, user, *, json_schema=None):
        self.prompts.append((system, user))
        reply = self.replies.pop(0)
        return reply if isinstance(reply, str) else json.dumps(reply, ensure_ascii=False)


def retriever(query, k):
    return ARTICLES[:k]


def ok(text, used=(1,)):
    return {"status": "answered", "answer": text, "used_sources": list(used)}


def test_answer_cites_sources_in_the_question_language():
    llm = ScriptedLLM(ok("3ndek l7e9 f 1.5 nhar f chhar [2].", used=[2]))
    answer = Answerer(retriever, llm, k=3).answer("chhal dyal lconji 3ndi f l3am?")
    assert answer.verified and answer.attempts == 1
    assert answer.language == "darija-latn"
    assert [a.article_number for a in answer.cited_articles] == ["231"]
    system, user = llm.prompts[0]
    assert "Latin letters" in system
    assert user.startswith("SOURCES\n\n[1] ")
    assert "[3] " in user and "[4] " not in user  # k = 3 sources


def test_bad_citation_gets_one_retry_with_the_problems():
    llm = ScriptedLLM(ok("Selon l'article 99 [1]."), ok("Selon la loi [1]."))
    answer = Answerer(retriever, llm).answer("Quelle est la période d'essai ?")
    assert answer.verified and answer.attempts == 2
    assert "article 99" in llm.prompts[1][1]  # the retry explains what was wrong


def test_still_wrong_after_retry_is_flagged_not_hidden():
    llm = ScriptedLLM(ok("Règle [8]."), ok("Règle [8]."))
    answer = Answerer(retriever, llm).answer("Quelle est la période d'essai ?")
    assert not answer.verified
    assert "Citation check failed" in render(answer)


def test_not_covered_needs_no_citation():
    reply = {"status": "not_covered", "answer": "", "used_sources": []}
    answer = Answerer(retriever, ScriptedLLM(reply)).answer("Comment créer une SARL ?")
    assert answer.status == "not_covered" and answer.verified
    assert "avocat" in answer.text  # the standard refusal, in French


def test_plain_text_reply_is_tolerated():
    answer = Answerer(retriever, ScriptedLLM("Réponse sans JSON [1].")).answer("Question ?")
    assert answer.verified and answer.cited == [1]


def test_render_lists_cited_sources():
    answer = Answerer(retriever, ScriptedLLM(ok("Réponse [1].", used=[1]))).answer("Question ?")
    text = render(answer)
    assert "Sources:" in text and "[1] Loi 65-99, المادة 13 (official text)" in text


def test_retry_sees_its_previous_answer():
    llm = ScriptedLLM(ok("Selon l'article 99 [1]."), ok("Selon la loi [1]."))
    answer = Answerer(retriever, llm).answer("Quelle est la période d'essai ?")
    retry_prompt = llm.prompts[1][1]
    assert "YOUR PREVIOUS ANSWER:\nSelon l'article 99 [1]." in retry_prompt
    assert answer.history == [
        "attempt 1: answered — rejected: mentions article 99, which is not among the cited sources",
        "attempt 2: answered",
    ]


def test_a_refusal_on_retry_does_not_replace_the_first_answer():
    """Seen on Kaggle: the first answer was rejected, the retry refused although the right
    article was among the sources. The first answer is kept, shown as unverified."""
    refusal = {"status": "not_covered", "answer": "", "used_sources": []}
    llm = ScriptedLLM(ok("Règle (article 99) [1]."), refusal)
    answer = Answerer(retriever, llm).answer("Quelle est la période d'essai ?")
    assert answer.status == "answered" and not answer.verified
    assert answer.text == "Règle (article 99) [1]."
    assert "attempt 2: not_covered" in render(answer)


def test_progress_steps_are_reported_in_order():
    steps = []
    llm = ScriptedLLM(ok("Réponse [1]."))
    Answerer(retriever, llm, k=2).answer("Question ?", on_step=lambda n, d: steps.append((n, d)))
    assert [name for name, _ in steps] == ["understood", "sources", "writing"]
    assert steps[0][1]["language"] == "fr"
    assert steps[1][1]["articles"] == [a.id for a in ARTICLES[:2]]
