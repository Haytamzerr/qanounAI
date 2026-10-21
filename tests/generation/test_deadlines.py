"""Deadlines are shown only when the article really states them (decision 82)."""

from qanoun.generation.answer import Answerer
from qanoun.generation.deadlines import verify
from qanoun.ingestion.models import Article

from .test_answer import ScriptedLLM


def article(id_, text):
    return Article(
        id=id_, law_number="x", law_title="t", language="ar", article_number=id_.split("-")[-1],
        hierarchy=[], text=text, page_start=1, source_url="https://e.org", is_official_version=True,
    )  # fmt: skip


ART_65 = article(
    "loi-65-99-ar-art-65",
    "يجب، تحت طائلة سقوط الحق، رفع دعوى الفصل أمام المحكمة المختصة، في أجل تسعين يوما من "
    "تاريخ توصل الأجير بمقرر الفصل.",
)
ART_10 = article(
    "loi-67-12-ar-art-10",
    "إذا تم إشعار المكري بالطرق المنصوص عليها قانونا بالقيام بالإصلاحات التي تقع على عاتقه ولم "
    "ينجزها في أجل شهر، جاز للمكتري أن يستصدر أمرا من رئيس المحكمة الابتدائية.",
)
SOURCES = [ART_65, ART_10]


def d(**over):
    base = {
        "what": "رفع دعوى الفصل", "amount": 90, "unit": "days", "source": 1, "from_event": "التوصل",
        "quote": "في أجل تسعين يوما من تاريخ توصل الأجير بمقرر الفصل",
    }  # fmt: skip
    return base | over


def test_a_deadline_stated_by_its_article_is_kept():
    [kept] = verify([d()], SOURCES)
    assert (kept.amount, kept.unit, kept.article_id) == (90, "days", "loi-65-99-ar-art-65")


def test_one_month_written_as_the_unit_alone():
    [kept] = verify([d(amount=1, unit="months", source=2, quote="ولم ينجزها في أجل شهر")], SOURCES)
    assert kept.article_id == "loi-67-12-ar-art-10"


def test_vowel_marks_and_letter_variants_do_not_matter():
    assert verify([d(quote="فى أجل تسعين يوماً من تاريخ توصل الاجير")], SOURCES)


def test_invented_or_wrong_deadlines_are_dropped():
    assert verify([d(amount=60)], SOURCES) == []  # the article says ninety
    assert verify([d(unit="months")], SOURCES) == []  # ninety days, not months
    assert (
        verify([d(quote="في أجل ستين يوما من تاريخ التوصل", amount=60)], SOURCES) == []
    )  # not in it
    assert verify([d(source=7)], SOURCES) == []  # no such source
    assert verify([d(source=2)], SOURCES) == []  # the quote is from source 1
    assert verify([{"what": "x", "amount": "abc"}], SOURCES) == []


def test_the_analysis_returns_only_verified_deadlines():
    plan = {"situation": "s", "searches": ["الفصل"], "articles": [], "missing": []}
    sections = {
        "status": "answered", "situation": "s", "law": "عندك تسعين يوم [1].", "application": "a",
        "steps": "1) رفع دعوى [1].", "missing": "", "used_sources": [1],
        "deadlines": [d(), d(amount=30, quote="في أجل ثلاثين يوما")],
    }  # fmt: skip
    answer = Answerer(lambda q, k: SOURCES[:k], ScriptedLLM(plan, sections)).answer(
        "جراو عليا من الخدمة", mode="analysis"
    )
    assert [x.amount for x in answer.deadlines] == [90]
