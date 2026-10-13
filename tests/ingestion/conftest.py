"""Shared fixtures: a small fake law, laid out like the Adala PDFs."""

from pathlib import Path

import pymupdf
import pytest

from qanoun.ingestion.models import Source

BOLD, REGULAR = "hebo", "helv"


@pytest.fixture
def source() -> Source:
    return Source(
        file="fake.pdf",
        law_number="00-00",
        law_title="Loi de test",
        language="fr",
        layout="adala-word",
        source_url="https://example.org/fake.pdf",
        bulletin_officiel="",
        consolidated_as_of="",
        downloaded_on="2026-10-13",
        is_official_version=False,
    )


@pytest.fixture
def fake_law_pdf(tmp_path: Path) -> Path:
    """Two pages that contain every trap found in the real Law 09-08 PDF."""
    doc = pymupdf.open()

    page = doc.new_page()
    y = 72.0

    def write(text: str, size: float, font: str = REGULAR, x: float = 72.0, step: float = 17.4):
        nonlocal y
        page.insert_text((x, y), text, fontname=font, fontsize=size)
        y += step

    def write_then_superscript(text: str, sup: str, after: str = ""):
        """Body text, then a small raised span glued to it, then optional text after."""
        nonlocal y
        page.insert_text((72, y), text, fontname=REGULAR, fontsize=14)
        x = 72 + pymupdf.get_text_length(text, fontname=REGULAR, fontsize=14) + 0.2
        page.insert_text((x, y - 4), sup, fontname=REGULAR, fontsize=9)
        if after:
            x += pymupdf.get_text_length(sup, fontname=REGULAR, fontsize=9) + 0.2
            page.insert_text((x, y), after, fontname=REGULAR, fontsize=14)
        y += 17.4

    # Cover title and promulgating dahir: must be skipped
    write("Loi de test", 22, BOLD, step=30)
    write("Est promulguée et sera publiée au Bulletin officiel.", 14, step=40)

    # A chapter heading wrapped on two lines, then a section
    write("CHAPITRE PREMIER: DISPOSITIONS", 16, BOLD)
    write("GÉNÉRALES", 16, BOLD, step=30)
    write("Section première: Définitions", 14, BOLD, step=30)

    # "Article premier", a footnote marker glued to a word, an ordinal superscript
    write("Article premier", 15, BOLD, step=24)
    write_then_superscript("Le responsable du traitement", "1")  # footnote marker
    write_then_superscript("applique l'article 11 (2", "e", after=" alinéa) ci-")  # ordinal
    write("dessus en toutes circonstances.", 14, step=24)
    write("Un second paragraphe commence ici après un espace plus grand.", 14, step=40)

    # A footnote quoting another text, including a fake "Article 34:" heading
    write("1 - Voir décret n° 2-09-165 ; Bulletin Officiel n° 5744.", 12)
    write("Article 34:", 12, BOLD)
    write("« Texte d'un autre décret qui ne doit pas être repris. »", 12)
    page.insert_text((290, 800), "- 1 -", fontname=REGULAR, fontsize=14)  # page number

    # Page 2: new chapter, an article with a sub-title, a paragraph continuing across pages
    page = doc.new_page()
    y = 72.0
    write("CHAPITRE II: DES DROITS", 16, BOLD, step=30)
    write("Article 2", 15, BOLD, step=24)
    write("Droit d'accès", 14, BOLD, step=24)
    write("Toute personne a le droit d'obtenir la confirmation que des", 14)
    write("données la concernant sont ou ne sont pas traitées.", 14)
    page.insert_text((290, 800), "- 2 -", fontname=REGULAR, fontsize=14)

    path = tmp_path / "fake.pdf"
    doc.save(path)
    doc.close()
    return path
