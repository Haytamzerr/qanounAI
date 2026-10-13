"""Tests for PDF reading and article parsing, on a generated fake law."""

import pytest

from qanoun.ingestion.parse_law import LAYOUTS, article_number, normalize, parse_lines
from qanoun.ingestion.pdf_lines import Span, group_into_lines, read_lines

PROFILE = LAYOUTS["adala-word"]


@pytest.fixture
def articles(fake_law_pdf, source):
    lines = read_lines(fake_law_pdf, min_size=PROFILE.min_size)
    return parse_lines(lines, source, PROFILE)


@pytest.mark.parametrize(
    ("heading", "expected"),
    [
        ("Article premier", "1"),
        ("Article 2", "2"),
        ("Article 25 bis", "25 bis"),
        ("ARTICLE 7 :", "7"),
        ("Articles 3 et 4", None),
        ("Droit d’accès", None),
    ],
)
def test_article_number(heading, expected):
    assert article_number(heading) == expected


def test_normalize_keeps_wording_and_fixes_spaces():
    assert normalize("la  modification ,  l’extraction ") == "la modification, l’extraction"


def test_spans_on_one_baseline_become_one_line_with_spaces():
    spans = [
        Span(page=1, x0=70, x1=90, baseline=100.0, size=14, bold=False, text="Est"),
        Span(page=1, x0=120, x1=170, baseline=100.4, size=14, bold=False, text="réputée"),
    ]
    [line] = group_into_lines(spans, min_size=13.7)
    assert line.text == "Est réputée"


def test_footnote_marker_dropped_but_ordinal_kept():
    spans = [
        Span(page=1, x0=70, x1=200, baseline=100, size=14, bold=False, text="du traitement"),
        Span(page=1, x0=200.2, x1=205, baseline=96, size=9, bold=False, text="3"),
        Span(page=1, x0=70, x1=150, baseline=120, size=14, bold=False, text="article 11 (2"),
        Span(page=1, x0=150.2, x1=155, baseline=116.5, size=9, bold=False, text="e"),
        Span(page=1, x0=158, x1=200, baseline=120, size=14, bold=False, text="alinéa)"),
    ]
    lines = [line.text for line in group_into_lines(spans, min_size=13.7)]
    assert lines == ["du traitement", "article 11 (2e alinéa)"]


def test_finds_every_article_and_nothing_from_footnotes(articles):
    assert [a.article_number for a in articles] == ["1", "2"]
    assert all("Article 34" not in a.text and "décret" not in a.text for a in articles)


def test_front_matter_and_page_numbers_are_skipped(articles):
    full_text = " ".join(a.text for a in articles)
    assert "promulguée" not in full_text
    assert "- 1 -" not in full_text


def test_wrapped_chapter_and_section_build_the_hierarchy(articles):
    assert articles[0].hierarchy == [
        "CHAPITRE PREMIER: DISPOSITIONS GÉNÉRALES",
        "Section première: Définitions",
    ]
    assert articles[1].hierarchy == ["CHAPITRE II: DES DROITS"], "a new chapter resets the section"


def test_text_is_clean(articles):
    first = articles[0].text
    assert "traitement1" not in first, "footnote marker must be removed"
    assert "(2e alinéa)" in first, "ordinal superscript must be kept"
    assert "ci-dessus" in first, "hyphenated line break must be re-joined"
    assert first.count("\n") == 1, "two paragraphs separated by a larger vertical gap"


def test_article_subtitle_and_metadata(articles):
    second = articles[1]
    assert second.title == "Droit d'accès"
    assert second.text.startswith("Toute personne a le droit")
    assert second.id == "loi-00-00-fr-art-2"
    assert second.page_start == 2
