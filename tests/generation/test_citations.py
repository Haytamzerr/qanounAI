from qanoun.generation.citations import check

from ..retrieval.test_search import make_article

SOURCES = [
    make_article("65-99", "ar", 231, "يستحق الأجير عطلة سنوية مؤدى عنها"),
    make_article("65-99", "ar", 43, "يكون الإنهاء مبنيا على احترام أجل الإخطار وفق المادة 37"),
]


def test_valid_answer():
    result = check("Tu as droit à 1,5 jour par mois [1].", SOURCES)
    assert result.ok and result.cited == [1]


def test_unknown_marker_is_removed_and_reported():
    result = check("Règle A [1]. Règle B [7].", SOURCES)
    assert result.text == "Règle A [1]. Règle B ."
    assert result.cited == [1]
    assert result.problems == ["marker [7] is not one of the 2 sources"]


def test_answer_without_citation_is_rejected():
    assert check("Tu as droit à un congé.", SOURCES).problems == ["the answer cites no source"]
    assert check("Je ne sais pas.", SOURCES, answered=False).ok  # refusals need no source


def test_used_sources_count_as_citations():
    assert check("Tu as droit à un congé.", SOURCES, used=[2, 9]).cited == [2]


def test_article_numbers_must_come_from_cited_sources():
    assert check("selon المادة 231 [1]", SOURCES).ok
    assert check("selon l'article 37 [2]", SOURCES).ok  # mentioned inside source [2]
    invented = check("selon lmadda 52 [1]", SOURCES)
    assert invented.problems == ["mentions article 52, which is not among the cited sources"]
