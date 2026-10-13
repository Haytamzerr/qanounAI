"""Checks on the real Arabic Law 09-08 PDF (the official version).

Skipped where the PDF has not been downloaded (see data/sources.csv for the URL).
"""

import pytest

from qanoun.config import settings
from qanoun.ingestion.build import load_sources, parse_source
from qanoun.ingestion.quality import check_articles

PDF = settings.raw_dir / "loi-09-08-ar.pdf"
FR_PDF = settings.raw_dir / "loi-09-08-fr.pdf"
pytestmark = [
    pytest.mark.slow,
    pytest.mark.skipif(not PDF.exists(), reason="Arabic Law 09-08 PDF not downloaded"),
]


def parse(file: str):
    [source] = [s for s in load_sources(settings.data_dir / "sources.csv") if s.file == file]
    return {a.article_number: a for a in parse_source(source, settings.raw_dir)}


@pytest.fixture(scope="module")
def articles():
    return parse(PDF.name)


def test_all_67_articles_in_order(articles):
    assert list(articles) == [str(n) for n in range(1, 68)]


def test_quality_checks_pass(articles):
    assert check_articles(list(articles.values())) == []


def test_it_is_the_official_version(articles):
    assert all(a.is_official_version for a in articles.values())


def test_ligatures_and_reading_order(articles):
    first = articles["1"]
    assert first.hierarchy == ["الباب الأول: أحكام عامة", "الفرع الأول: تعاريف ونطاق التطبيق"]
    assert first.text.startswith("المعلوميات في خدمة المواطن")
    assert "ويجب ألا تمس بالهوية" in first.text
    assert "لإفشاء أسرار الحياة الخاصة للمواطنين." in first.text


def test_no_broken_ligatures_left(articles):
    # The exact misreadings observed before the repair. Letter patterns alone would not do:
    # "الإلكتروني" legitimately contains "لإل".
    full = " ".join(a.text for a in articles.values())
    for broken in ("األولى", "أال تمس", "لإلنسان", "ألجل تطبيق", "هللا"):
        assert broken not in full


def test_chapter_two_subtitles(articles):
    assert articles["7"].title == "الحق في الولوج"


def test_numbers_stay_left_to_right(articles):
    assert "القانون رقم 34.05" in articles["49"].text


@pytest.mark.skipif(not FR_PDF.exists(), reason="French Law 09-08 PDF not downloaded")
def test_french_and_arabic_have_the_same_articles(articles):
    assert list(parse(FR_PDF.name)) == list(articles)
