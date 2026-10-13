"""Checks on the real Law 09-08 PDF.

The PDF is not committed (data/raw is git-ignored), so these tests are skipped in CI and run on
any machine where the file has been downloaded (see data/sources.csv for the URL).
"""

import pytest

from qanoun.config import settings
from qanoun.ingestion.build import load_sources, parse_source
from qanoun.ingestion.quality import check_articles

PDF = settings.raw_dir / "loi-09-08-fr.pdf"
pytestmark = [
    pytest.mark.slow,
    pytest.mark.skipif(not PDF.exists(), reason="Law 09-08 PDF not downloaded"),
]


@pytest.fixture(scope="module")
def articles():
    sources = load_sources(settings.data_dir / "sources.csv")
    [source] = [s for s in sources if s.file == PDF.name]
    return {a.article_number: a for a in parse_source(source, settings.raw_dir)}


def test_all_67_articles_in_order(articles):
    assert list(articles) == [str(n) for n in range(1, 68)]


def test_quality_checks_pass(articles):
    assert check_articles(list(articles.values())) == []


def test_article_1_starts_the_law(articles):
    assert articles["1"].text.startswith("L’informatique est au service du citoyen")
    assert articles["1"].hierarchy[1].startswith("Section première")


def test_footnotes_do_not_leak(articles):
    # Article 49's page carries a long footnote quoting the copyright law (article 11)
    assert "ayants droit de l'auteur" not in articles["49"].text
    assert articles["49"].text.endswith("droits voisins.")


def test_ordinals_are_kept(articles):
    assert "article 11 (2e alinéa)" in articles["49"].text


def test_chapter_two_subtitles(articles):
    assert articles["7"].title == "Droit d’accès"
    assert articles["7"].hierarchy == ["CHAPITRE II: DES DROITS DE LA PERSONNE CONCERNEE"]
