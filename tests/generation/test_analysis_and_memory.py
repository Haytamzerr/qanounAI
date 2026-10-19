"""Analysis mode (plan → searches → sections) and conversation memory (decisions 75, 76)."""

from qanoun.generation.answer import Answerer, Turn
from qanoun.generation.ask import render

from ..retrieval.test_search import ARTICLES
from .test_answer import ScriptedLLM, ok

BY_ID = {a.id: a for a in ARTICLES}


class RecordingRetriever:
    def __init__(self):
        self.queries: list[str] = []

    def __call__(self, query, k):
        self.queries.append(query)
        return ARTICLES[len(self.queries) - 1 : len(self.queries) - 1 + k][:k] or ARTICLES[:1]


PLAN = {
    "situation": "Licencié après 7 ans sans motif.",
    "searches": ["الفصل التعسفي للأجير", "التعويض عن الفصل حسب الأقدمية"],
    "missing": ["Avez-vous reçu une lettre de licenciement ?"],
}
SECTIONS = {
    "status": "answered",
    "situation": "Vous avez été licencié sans motif après 7 ans.",
    "law": "Le congé annuel est d'un jour et demi par mois [1].",
    "application": "Vous pouvez réclamer vos droits [1].",
    "steps": "Adressez-vous à l'inspection du travail.",
    "missing": "Avez-vous reçu une lettre ?",
    "used_sources": [1],
}


def test_analysis_plans_runs_each_search_and_answers_in_sections():
    llm = ScriptedLLM(PLAN, SECTIONS)
    retriever = RecordingRetriever()
    steps = []
    answer = Answerer(retriever, llm).answer(
        "On m'a licencié après 7 ans sans motif, quels sont mes droits ?",
        lambda name, details: steps.append((name, details)),
        mode="analysis",
    )
    assert answer.mode == "analysis" and answer.verified and answer.status == "answered"
    assert answer.plan == PLAN["searches"]
    assert retriever.queries[:2] == PLAN["searches"]  # one search per planned question
    assert len(retriever.queries) == 3  # + the question itself
    assert set(answer.sections) == {"situation", "law", "application", "steps", "missing"}
    assert "planned" in [name for name, _ in steps]
    system, user = llm.prompts[1]
    assert '"law"' in system and "Facts not given" in user  # missing facts passed on
    assert "## What the law says" in render(answer)


def test_analysis_sections_are_checked_like_an_answer():
    bad = dict(SECTIONS, law="Selon l'article 999 [7].", used_sources=[7])
    llm = ScriptedLLM(PLAN, bad, SECTIONS)
    answer = Answerer(RecordingRetriever(), llm).answer("Licencié sans motif ?", mode="analysis")
    assert answer.attempts == 2 and answer.verified  # the retry fixed it
    assert "article 999" in llm.prompts[2][1]


def test_a_broken_plan_falls_back_to_a_quick_answer():
    llm = ScriptedLLM("not json at all", ok("Un jour et demi par mois [1]."))
    answer = Answerer(RecordingRetriever(), llm).answer("Combien de congé ?", mode="analysis")
    assert answer.mode == "quick" and answer.verified


def test_a_follow_up_is_rewritten_with_the_conversation_and_keeps_the_cited_articles():
    first = ARTICLES[1]
    llm = ScriptedLLM(
        "Combien de jours de congé a un salarié qui a des enfants ?",  # standalone question
        ok("Le congé reste d'un jour et demi par mois [1]."),
    )
    retriever = RecordingRetriever()
    history = [Turn("Combien de jours de congé ?", "Un jour et demi par mois [1].", (first.id,))]
    answer = Answerer(retriever, llm, lookup=BY_ID.get).answer(
        "Et si j'ai des enfants ?", history=history
    )
    assert answer.standalone.startswith("Combien de jours de congé")
    assert retriever.queries == [answer.standalone]  # search uses the standalone question
    assert first in answer.sources  # the previous answer's article stays available
    _, user = llm.prompts[1]
    assert "CONVERSATION SO FAR" in user and "Combien de jours de congé ?" in user
    assert user.rstrip().endswith("Et si j'ai des enfants ?")  # answered as asked


def test_a_failed_rewrite_still_answers_the_follow_up():
    class Flaky(ScriptedLLM):
        def generate(self, system, user, *, json_schema=None):
            if json_schema is None:
                raise RuntimeError("busy")
            return super().generate(system, user, json_schema=json_schema)

    llm = Flaky(ok("Oui [1]."))
    history = [Turn("Question ?", "Réponse [1].")]
    answer = Answerer(RecordingRetriever(), llm).answer("Et après ?", history=history)
    assert answer.verified and answer.standalone is None


def test_the_plan_may_suggest_articles_which_are_looked_up_not_trusted():
    from qanoun.understanding.references import ReferenceResolver

    plan = dict(PLAN, articles=["loi 65.99 article 231", "loi 65.99 article 9999"])
    llm = ScriptedLLM(plan, SECTIONS)
    steps = []
    answer = Answerer(
        lambda q, k: [ARTICLES[0]], llm, references=ReferenceResolver(ARTICLES).resolve
    ).answer("Licencié après 7 ans ?", lambda n, d: steps.append((n, d)), mode="analysis")
    lead = BY_ID["loi-65-99-ar-art-231"]
    assert answer.leads == [lead.id]  # the article that does not exist is dropped
    assert answer.sources[:2] == [lead, ARTICLES[0]]  # leads come before what search found
    assert dict(steps)["planned"]["articles"] == [lead.id]


def test_a_plan_without_suggested_articles_still_works():
    llm = ScriptedLLM(PLAN, SECTIONS)  # an older plan without "articles"
    answer = Answerer(RecordingRetriever(), llm).answer("Licencié ?", mode="analysis")
    assert answer.mode == "analysis" and answer.leads == []
