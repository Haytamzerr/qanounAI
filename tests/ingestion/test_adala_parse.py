"""The generic Adala parser: layout measured on each PDF, and the law-level choices.

Line sizes and wordings reproduce what was measured on real Adala PDFs (Oct 2026): body text
at 16 pt, article headings bold at 16 pt (15 pt in the co-ownership law, 19 pt with a title on
the same line in the nationality code), headings bold and bigger.
"""

import pytest

from qanoun.ingestion.adala import CatalogEntry
from qanoun.ingestion.adala_parse import (
    ORDINALS,
    RULES,
    article_word,
    detect_profile,
    is_repealed,
    law_key,
    select,
    short_title,
)
from qanoun.ingestion.models import Article, Source
from qanoun.ingestion.parse_law import article_heading, parse_lines
from qanoun.ingestion.pdf_lines import Line

SOURCE = Source(
    file="x.pdf",
    law_number="18-00",
    law_title="القانون رقم 18.00",
    language="ar",
    layout="auto",
    source_url="https://example.org/x.pdf",
    downloaded_on="2026-10-14",
    is_official_version=False,
)
BODY = "تسري أحكام هذا القانون على العقارات المبنية المقسمة إلى شقق أو طبقات أو محلات."


def line(text: str, size: float = 16.0, bold: bool = False, page: int = 1, y: float = 100.0):
    return Line(page=page, y=y, size=size, bold=bold, text=text)


def entry(obj: str, law_type: str = "ظهير", date: str = "2020-01-01", path: str = "a.pdf"):
    return CatalogEntry(
        path=path,
        name=obj,
        object=obj,
        law_type=law_type,
        law_number=None,
        themes=[],
        resource=None,
        date=date,
        language="AR",
    )


@pytest.mark.parametrize(
    ("heading", "expected"),
    [
        ("المادة 5", ("5", None)),
        ("الفصل 1", ("1", None)),
        ("الفصل1", ("1", None)),  # glued, as old dahirs print it
        ("المادة الأولى", ("1", None)),
        ("الفصل الثالث", ("3", None)),
        ("الفصل الحادي عشر", ("11", None)),
        ("الفصل الثاني والعشرون", ("22", None)),
        ("المادة 4-82", ("4-82", None)),
        ("الفصل 230 مكرر", ("230 bis", None)),
        ("الفصل 231 مكرر مرتين", ("231 ter", None)),
        ("مادة فريدة", ("1", None)),
        ("الفصل 13: وثيقة التجنيس", ("13", "وثيقة التجنيس")),
        ("الفصل الأول.", ("1", None)),
    ],
)
def test_article_headings(heading, expected):
    assert article_heading(heading, rules=RULES) == expected


@pytest.mark.parametrize(
    "text",
    [
        "الفصل 26 و27 من هذا القانون",  # a reference inside body text
        "المادة 2 من القانون رقم 70.03",
        "الفصول 1 إلى 5",
    ],
)
def test_references_in_the_text_are_not_headings(text):
    assert article_heading(text, rules=RULES) is None


def test_ordinals_cover_spellings_seen_in_the_pdfs():
    assert ORDINALS["الأولى"] == ORDINALS["الاولى"] == ORDINALS["األولى"] == "1"
    assert ORDINALS["التاسعة والتسعون"] == "99"


def test_profile_is_measured_from_the_lines():
    lines = [
        line("الباب الأول: أحكام عامة", 20.0, True, y=60),
        line("المادة 1", 15.0, True, y=90),  # a little smaller than the body
        *[line(BODY, y=110 + 27 * i) for i in range(5)],
        line("الفرع الأول", 18.0, True, y=260),
        line("المادة 2", 15.0, True, y=290),
        line(BODY, y=310),
        line("1 - الجريدة الرسمية عدد 5054", 13.0, y=700),  # footnote
    ]
    profile = detect_profile(lines)
    assert profile.body_size == 16.0
    assert profile.article_size == 15.0
    assert profile.levels == (("chapter", 20.0), ("section", 18.0))
    assert profile.paragraph_gap == 27 + 2.5


def test_fasl_is_a_chapter_only_when_printed_bigger_than_the_articles():
    lines = [
        line("الفصل الأول: أحكام عامة", 19.0, True, y=60),
        line("المادة 1", 16.0, True, y=90),
        line(BODY, y=110),
    ]
    assert detect_profile(lines).levels == (("chapter2", 19.0),)
    old_dahir = [line("الفصل 1", 16.0, True, y=90), line(BODY, y=110)]
    assert detect_profile(old_dahir).levels == ()


def test_no_article_heading_means_no_profile():
    assert detect_profile([line(BODY), line("الباب الأول", 20.0, True)]) is None


def test_a_text_without_headings_starts_at_its_first_article():
    lines = [
        line("ظهير شريف رقم 1.73.250", 22.0, True, y=60),  # title page
        line("يعلم من ظهيرنا الشريف هذا أننا أصدرنا أمرنا بما يأتي:", y=90),
        line("الفصل 1", 16.0, True, y=120),
        line(BODY, y=140),
        line("الفصل 2: التأليف", 16.0, True, y=170),
        line(BODY, y=190),
    ]
    profile = detect_profile(lines)
    first, second = parse_lines(lines, SOURCE, profile, rules=RULES, start_on_article=True)
    assert (first.article_number, first.text) == ("1", BODY)
    assert (second.article_number, second.title) == ("2", "التأليف")
    # without start_on_article (the curated laws' behaviour) nothing starts
    assert parse_lines(lines, SOURCE, profile, rules=RULES) == []


def test_text_on_the_heading_line_is_the_article_text_not_a_title():
    lines = [line("الفصل الأول. - يحدث مجلس وطني للشباب.", 16.0, True), line(BODY, y=120)]
    [article] = parse_lines(lines, SOURCE, detect_profile(lines), RULES, start_on_article=True)
    assert article.title is None
    assert article.text.startswith("يحدث مجلس وطني للشباب.")


def _article(text: str) -> Article:
    return Article(
        id="x",
        law_number="1",
        law_title="t",
        language="ar",
        article_number="1",
        hierarchy=[],
        text=text,
        page_start=1,
        source_url="https://example.org",
        is_official_version=False,
    )


@pytest.mark.parametrize("text", ["(نسخ).", "نسخت", "( ألغي ).", "", "نسخ.\nالفصل 3 المكرر نسخ."])
def test_repealed_articles_are_recognised(text):
    assert is_repealed(_article(text))


def test_short_real_articles_are_kept():
    assert not is_repealed(_article("للملك قائمة مدنية."))


@pytest.mark.parametrize(
    ("title", "key", "short"),
    [
        (
            "ظهير شريف رقم 1.03.194 صادر في 14 من رجب 1424 (11 سبتمبر 2003) "
            "بتنفيذ القانون رقم 65.99 المتعلق بمدونة الشغل",
            "65-99",
            "القانون رقم 65.99 المتعلق بمدونة الشغل",
        ),
        (
            "ظهير شريف رقم 1.59.413 صادر في 28 جمادى الأولى 1382 (26 نونبر 1962) "
            "بالمصادقة على مجموعة القانون الجنائي",
            "dahir-1-59-413",
            "مجموعة القانون الجنائي",
        ),
        (
            "ظهیر شريف رقم 1.57.387 صادر في 16 رجب 1377 (6 فبراير 1958) بشأن العفو",
            "dahir-1-57-387",
            "ظهير بشأن العفو",
        ),
        ("القانون رقم58.00 بإحداث الوكالة", "58-00", "القانون رقم58.00 بإحداث الوكالة"),
    ],
)
def test_law_key_and_short_title(title, key, short):
    e = entry(title)
    assert (law_key(e), short_title(e)) == (key, short)


def test_selection_keeps_one_current_pdf_per_law():
    old = entry("بتنفيذ القانون رقم 15.95 المتعلق بمدونة التجارة", date="2019-01-01", path="o")
    new = entry("بتنفيذ القانون رقم 15.95 المتعلق بمدونة التجارة", date="2024-01-01", path="n")
    chosen = select(
        [
            old,
            new,
            entry("بتنفيذ قانون المالية رقم 55.23 للسنة المالية 2024", path="f"),  # budget
            entry("بتنفيذ القانون رقم 05.00 بشأن التعليم الأولي (نسخ)", path="r"),  # repealed
            entry("بتنفيذ القانون رقم 65.99 المتعلق بمدونة الشغل", path="c"),  # curated
            entry("مرسوم رقم 2.20.292", law_type="مرسوم", path="d"),  # not a law
            entry("دستور المملكة المغربية لسنة 1970", path="h"),  # history
        ],
        types={"ظهير"},
        skip_keys={"65-99"},
    )
    assert chosen == [new]


def test_a_law_filed_as_a_decree_is_still_a_law():
    road_code = entry(
        "ظهير شريف رقم 1.10.07 صادر في 26 من صفر 1431 (11 فبراير 2010) "
        "بتنفيذ القانون رقم 52.05 المتعلق بمدونة السير على الطرق",
        law_type="مرسوم",
    )
    assert select([road_code], types={"ظهير"}, skip_keys=set()) == [road_code]


def test_citations_use_the_word_the_law_uses():
    penal = [line("الفصل 400", 16.0, True), line(BODY), line("الفصل 401", 16.0, True)]
    assert article_word(penal) == "الفصل"
    assert article_word([line("المادة 1", 16.0, True), line(BODY)]) == "المادة"
    assert _article("نص").label == "المادة"
    assert _article("نص").model_copy(update={"article_word": "الفصل"}).label == "الفصل"
