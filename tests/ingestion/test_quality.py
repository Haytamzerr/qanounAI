"""The quality checks must catch the silent errors a parser can make."""

from qanoun.ingestion.models import Article
from qanoun.ingestion.quality import check_articles

LONG_TEXT = "Texte d’article suffisamment long pour passer le contrôle de longueur."


def make(number: str, text: str = LONG_TEXT) -> Article:
    return Article(
        id=f"loi-00-00-fr-art-{number.replace(' ', '-')}",
        law_number="00-00",
        law_title="Loi de test",
        language="fr",
        article_number=number,
        hierarchy=["CHAPITRE PREMIER"],
        text=text,
        page_start=1,
        source_url="https://example.org",
        is_official_version=False,
    )


def test_clean_articles_pass():
    assert check_articles([make("1"), make("2"), make("2 bis"), make("3")]) == []


def test_gap_in_numbering_is_reported():
    assert check_articles([make("1"), make("4")]) == [
        "gap in numbering: articles 2 to 3 are missing"
    ]


def test_duplicate_and_short_articles_are_reported():
    problems = check_articles([make("1"), make("1"), make("2", "Texte trop court ici.")])
    assert any("duplicate" in p for p in problems)
    assert any("suspiciously short" in p for p in problems)


def test_footnote_leak_is_reported():
    leaked = LONG_TEXT + "\nArticle 34: texte d’un décret ; Bulletin Officiel n° 5744."
    assert any("footnote" in p for p in check_articles([make("1", leaked)]))


def test_empty_result_is_a_problem():
    assert check_articles([]) == ["no articles parsed"]
