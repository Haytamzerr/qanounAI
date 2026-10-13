"""Checks on the real Labour Code PDF (Law 65.99, Arabic, consolidated 16 July 2026).

Skipped where the PDF has not been downloaded (see data/sources.csv for the URL).
"""

import re

import pytest

from qanoun.config import settings
from qanoun.ingestion.build import load_sources, parse_source
from qanoun.ingestion.quality import check_articles

PDF = settings.raw_dir / "code-travail-ar.pdf"
pytestmark = pytest.mark.skipif(not PDF.exists(), reason="Labour Code PDF not downloaded")


@pytest.fixture(scope="module")
def parsed():
    [source] = [s for s in load_sources(settings.data_dir / "sources.csv") if s.file == PDF.name]
    notes: list[str] = []
    articles = {a.article_number: a for a in parse_source(source, settings.raw_dir, notes)}
    return articles, notes


@pytest.fixture(scope="module")
def articles(parsed):
    return parsed[0]


def test_all_589_articles_in_order(articles):
    assert list(articles) == [str(n) for n in range(1, 590)]


def test_quality_checks_pass(articles):
    assert check_articles(list(articles.values())) == []


def test_article_517_heading_was_rescued(parsed):
    articles, notes = parsed
    assert notes == ["rescued mis-formatted heading on p. 140: المادة 517"]
    assert articles["517"].text.startswith("يجب أن يكون عقد الشغل الخاص بالأجانب")
    assert "الخاص بالأجانب" not in articles["516"].text


def test_eight_books(articles):
    books = list(dict.fromkeys(a.hierarchy[0] for a in articles.values()))
    assert len(books) == 8
    assert books[0] == "الكتاب التمهيدي"
    assert books[-1] == "الكتاب السابع: مقتضيات ختامية"


def test_deep_hierarchy(articles):
    assert articles["53"].hierarchy == [
        "الكتاب الأول: الاتفاقيات المتعلقة بالشغل",
        "القسم الأول: عقد الشغل",
        "الباب الخامس: توقف عقد الشغل وإنهاؤه",
        "الفرع الرابع: التعويض عن الفصل",
    ]


def test_shadowed_headings_are_clean(articles):
    headings = {h for a in articles.values() for h in a.hierarchy}
    assert "الباب الأول: فترة الاختبار" in headings
    doubled = [h for h in headings if re.search(r"األ|الأأ|ااخ|اإلإ|البابالباب", h)]
    assert doubled == []


def test_key_rules_are_readable(articles):
    assert "96 ساعة من الأجرة" in articles["53"].text
    assert "يوم ونصف يوم من أيام الشغل الفعلي عن كل شهر" in articles["231"].text
