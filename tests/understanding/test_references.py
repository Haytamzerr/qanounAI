"""Articles the question names itself are looked up directly (decision 71)."""

import pytest

from qanoun.generation.answer import Answerer
from qanoun.ingestion.models import Article
from qanoun.understanding.references import ReferenceResolver, note

from ..generation.test_answer import ScriptedLLM


def art(law: str, title: str, number: str, text: str = "نص المادة.", language="ar") -> Article:
    return Article(
        id=f"loi-{law}-{language}-art-{number.replace(' ', '-')}",
        law_number=law,
        law_title=title,
        language=language,
        article_number=number,
        hierarchy=[],
        text=text,
        page_start=1,
        source_url="https://example.org",
        is_official_version=True,
    )


PENAL = "مجموعة القانون الجنائي"
LABOUR = "القانون رقم 65.99 المتعلق بمدونة الشغل"
RENT = "القانون رقم 67.12 المتعلق بتنظيم العلاقات التعاقدية بين المكري والمكتري"
ARTICLES = [
    art("dahir-1-59-413", PENAL, "400", "من ارتكب عمدا ضد غيره جرحا أو ضربا… يعاقب بالحبس"),
    art("dahir-1-59-413", PENAL, "505", "من اختلس عمدا مالا مملوكا للغير يعد سارقا"),
    *[art("65-99", LABOUR, str(n)) for n in (1, 231, 589)],
    art("67-12", RENT, "34", "تحدد نسبة الزيادة في 8%"),
    art("37-10", "القانون رقم 37.10 القاضي بتغيير القانون الجنائي", "1"),  # a small namesake
]
resolve = ReferenceResolver(ARTICLES).resolve


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        (
            "D'après l'article 400 du Code pénal, le vol est puni de 10 ans ?",
            [("dahir-1-59-413", "400")],
        ),
        ("شنو كيقول الفصل 505 من القانون الجنائي؟", [("dahir-1-59-413", "505")]),
        ("chno kayqoul lmadda 231 dyal moudawanat chghol?", [("65-99", "231")]),
        ("المادة 34 من القانون رقم 67.12", [("67-12", "34")]),
        ("Que dit l'article 34 de la loi 67-12 ?", [("67-12", "34")]),
    ],
)
def test_named_articles_are_found(question, expected):
    refs = resolve(question)
    assert [(r.law_number, r.article_number) for r in refs] == expected
    assert all(r.article is not None for r in refs)


def test_an_article_that_does_not_exist_is_reported():
    [ref] = resolve("D'après l'article 1500 du Code du travail, combien de jours de congé ?")
    assert ref.article is None and ref.last_article == 589
    assert "does not exist" in note(ref) and "589" in note(ref)


@pytest.mark.parametrize(
    "question",
    [
        "واش الفصل من الشغل بلا سبب قانوني؟",  # الفصل = dismissal, no number
        "article 5",  # no law named
        "l'article 5 du Code pénal et l'article 3 du Code du travail",  # two laws: ambiguous
    ],
)
def test_no_reference_when_unclear(question):
    assert resolve(question) == []


def test_answerer_reads_the_named_article_first_and_may_correct_the_premise():
    llm = ScriptedLLM(
        {
            "status": "answered",
            "answer": "لا، الفصل 400 يتعلق بالضرب والجرح [1]، والسرقة في الفصل 505 [2].",
            "used_sources": [1, 2],
        }
    )
    answerer = Answerer(lambda q, k: [ARTICLES[1]], llm, references=resolve)
    answer = answerer.answer("D'après l'article 400 du Code pénal, le vol est puni de 10 ans ?")
    assert answer.sources[0].article_number == "400"
    assert answer.verified and answer.status == "answered"


def test_a_missing_article_is_explained_to_the_model_and_may_be_repeated():
    llm = ScriptedLLM(
        {
            "status": "answered",
            "answer": "L'article 1500 n'existe pas ; le congé annuel est à l'article 231 [1].",
            "used_sources": [1],
        }
    )
    answerer = Answerer(lambda q, k: [ARTICLES[3]], llm, references=resolve)
    answer = answerer.answer("D'après l'article 1500 du Code du travail, combien de jours ?")
    assert "does not exist" in llm.prompts[0][1]
    assert answer.verified  # 1500 comes from the question, not from memory


def test_too_vague_questions_get_a_question_back():
    llm = ScriptedLLM(
        {"status": "clarify", "answer": "Vous parlez du travail, du logement ou de la famille ?",
         "used_sources": []}
    )  # fmt: skip
    answer = Answerer(lambda q, k: ARTICLES[:2], llm).answer("حقوقي")
    assert answer.status == "clarify" and answer.verified
    assert answer.text.startswith("Vous parlez")
