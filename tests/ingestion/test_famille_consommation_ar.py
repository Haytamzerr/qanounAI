"""Checks on the real Family Code (Law 70.03) and Consumer Protection (Law 31.08) PDFs.

Skipped where the PDFs have not been downloaded (see data/sources.csv for the URLs).
"""

import pytest

from qanoun.config import settings
from qanoun.ingestion.build import load_sources, parse_source
from qanoun.ingestion.quality import check_articles

pytestmark = pytest.mark.slow


def parse(file: str):
    if not (settings.raw_dir / file).exists():
        pytest.skip(f"{file} not downloaded")
    [source] = [s for s in load_sources(settings.data_dir / "sources.csv") if s.file == file]
    return {a.article_number: a for a in parse_source(source, settings.raw_dir)}


@pytest.fixture(scope="module")
def famille():
    return parse("code-famille-ar.pdf")


@pytest.fixture(scope="module")
def consommation():
    return parse("protection-consommateur-ar.pdf")


def test_family_code_has_400_articles_and_passes_checks(famille):
    assert list(famille) == [str(n) for n in range(1, 401)]
    assert check_articles(list(famille.values())) == []


def test_family_code_preliminary_chapter_and_sections(famille):
    assert famille["1"].hierarchy == ["باب تمهيدي: أحكام عامة"]
    assert famille["51"].hierarchy[-1] == "الفرع الأول: الزوجان"
    assert famille["19"].text.startswith("تكتمل أهلية الزواج")
    assert famille["209"].text == "سن الرشد القانوني 18 سنة شمسية كاملة."


def test_consumer_law_has_206_articles_and_passes_checks(consommation):
    assert list(consommation) == [str(n) for n in range(1, 207)]
    assert check_articles(list(consommation.values())) == []


def test_consumer_law_three_levels(consommation):
    assert consommation["74"].hierarchy == [
        "القسم السادس: الاستدانة",
        "الباب الأول: القروض الاستهلاكية",
        "الفرع 1: نطاق التطبيق",
    ]
    assert "بترجمة إلى العربية" in consommation["206"].text
