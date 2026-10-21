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


def test_each_legal_idea_of_a_darija_question_gets_its_own_search():
    """o08: "I hit him / he started / prison?" → one search per idea, so self-defence is found."""
    retriever = RecordingRetriever()
    llm = ScriptedLLM(ok("Un jour et demi par mois [1]."))
    Answerer(retriever, llm).answer("wach ila darbt chi wa7ed w howa bda bdarb, ghadi n7bes?")
    assert retriever.queries[0].startswith("wach ila darbt")  # the question's own search first
    ideas = retriever.queries[1:]
    assert any("الدفاع الشرعي" in q and "الحبس" not in q for q in ideas)
    assert len(ideas) == 3


def test_a_question_with_one_legal_idea_gets_one_search():
    retriever = RecordingRetriever()
    Answerer(retriever, ScriptedLLM(ok("Un jour et demi par mois [1]."))).answer(
        "Combien de jours de congé par mois ?"
    )
    assert len(retriever.queries) == 1


def test_a_single_word_idea_is_a_party_not_an_issue():
    """o05: rent · المكري · repairs · paying rent → the landlord alone is not searched."""
    retriever = RecordingRetriever()
    Answerer(retriever, ScriptedLLM(ok("Un jour et demi par mois [1]."))).answer(
        "كريت شقة، مول الدار ما بغاش يصلح الما اللي كيقطر من السقف، "
        "واش نقدر ما نخلصش الكرا حتى يصلح؟"
    )
    ideas = retriever.queries[1:]
    assert "المكري" not in ideas and len(ideas) == 3
    assert any("الإصلاحات" in q for q in ideas) and any(q.startswith("أداء") for q in ideas)


def test_what_the_person_selected_reaches_the_plan_and_the_writer():
    llm = ScriptedLLM(PLAN, SECTIONS)
    facts = ["Sujet: Travail", "Je suis: Salarié(e)", "Quand: Il y a 1 à 12 mois"]
    answer = Answerer(RecordingRetriever(), llm).answer(
        "On m'a licencié sans motif après 7 ans.", mode="analysis", facts=facts
    )
    assert answer.language == "fr"  # detected on the person's own words, not the labels
    plan_prompt, write_prompt = llm.prompts[0][1], llm.prompts[1][1]
    assert "WHAT THE PERSON SELECTED" in plan_prompt and "- Je suis: Salarié(e)" in plan_prompt
    assert "Quand: Il y a 1 à 12 mois" in write_prompt


def test_the_clauses_of_a_document_are_checked_one_by_one():
    """Owner's contract: two unlawful clauses (no notice, waiver) were missed because only the
    story reached the analysis."""
    clauses = [
        "L'employeur peut mettre fin au présent contrat à tout moment, sans préavis ni indemnité.",
        "La salariée renonce par avance à toute indemnité de licenciement.",
    ]
    plan = dict(PLAN, searches=[f"بحث {i}" for i in range(1, 8)])
    llm = ScriptedLLM(plan, SECTIONS)
    retriever = RecordingRetriever()
    Answerer(retriever, llm).answer(
        "Je suis assistante administrative en CDI.", mode="analysis", document=clauses
    )
    plan_prompt, write_prompt = llm.prompts[0][1], llm.prompts[1][1]
    assert "CLAUSES OF THE PERSON'S DOCUMENT" in plan_prompt and "sans préavis" in plan_prompt
    assert (
        "check each one against the sources" in write_prompt
        and "renonce par avance" in write_prompt
    )
    assert retriever.queries[:2] == clauses  # each clause searched with its own words first
    assert retriever.queries[2:8] == [f"بحث {i}" for i in range(1, 7)]  # then 6 plan searches


def test_the_model_is_told_not_to_compute_totals():
    from qanoun.generation.prompts import analysis_system, system_prompt

    for system in (system_prompt("fr"), analysis_system("fr")):
        assert "Never" in system and "compute a total yourself" in system


def test_each_clause_is_searched_with_its_own_words_and_comes_first():
    """Owner's contract: the plan forgot "dismissal without notice"; art. 43/51 never came."""
    clauses = ["L'employeur peut mettre fin au contrat sans préavis ni indemnité."]
    llm = ScriptedLLM(PLAN, SECTIONS)
    retriever = RecordingRetriever()
    answer = Answerer(retriever, llm).answer("Mon contrat.", mode="analysis", document=clauses)
    assert retriever.queries[0] == clauses[0]  # searched before the plan's searches
    first_clause_hit = ARTICLES[0]  # RecordingRetriever's first answer
    assert answer.sources[0] == first_clause_hit


def test_a_clause_verdict_must_rest_on_a_source():
    from qanoun.generation.prompts import analysis_system

    assert "never judged from memory" in analysis_system("fr")
