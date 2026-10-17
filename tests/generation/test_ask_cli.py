"""Run the `ask` command end to end with a fake model and a fixed retriever.

Added after a bug: an option was used in the code but never declared, and no test ran the
command itself.
"""

import pytest

from qanoun.generation import ask

from ..retrieval.test_search import ARTICLES
from .test_answer import ScriptedLLM, ok


@pytest.fixture
def fake_world(monkeypatch):
    llm = ScriptedLLM(
        "هل يستحق الأجير عطلة سنوية؟",  # the rewrite of the Arabizi question
        ok("3ndek l7e9 f lconji [2].", used=[2]),
    )
    monkeypatch.setattr(ask, "GeminiLLM", lambda **_: llm)
    monkeypatch.setattr(ask, "RETRIEVERS", {"dense": lambda: lambda query, k: ARTICLES[:k]})
    from qanoun.understanding.references import ReferenceResolver

    monkeypatch.setattr(ask, "reference_resolver", lambda: ReferenceResolver(ARTICLES).resolve)
    return llm


def test_ask_prints_a_cited_answer(fake_world, capsys):
    assert ask.main(["chhal dyal lconji 3ndi f l3am?"]) == 0
    out = capsys.readouterr().out
    assert "3ndek l7e9 f lconji [2]." in out
    assert "Sources:" in out and "المادة 231" in out
    assert len(fake_world.prompts) == 2  # rewrite, then answer


def test_no_rewrite_skips_the_extra_call(fake_world, capsys):
    fake_world.replies.pop(0)  # no rewrite reply needed
    assert ask.main(["chhal dyal lconji 3ndi f l3am?", "--no-rewrite"]) == 0
    assert len(fake_world.prompts) == 1
