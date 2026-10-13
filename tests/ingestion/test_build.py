"""The build command must fail loudly instead of silently writing an empty dataset."""

import shutil

import pytest

from qanoun.config import settings
from qanoun.ingestion import build

CSV_HEADER = (
    "file,law_number,law_title,language,layout,source_url,"
    "bulletin_officiel,consolidated_as_of,downloaded_on,is_official_version\n"
)


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    """An isolated data/ folder listing one source: the fake law."""
    (tmp_path / "raw").mkdir()
    (tmp_path / "sources.csv").write_text(
        CSV_HEADER
        + "fake.pdf,00-00,Loi de test,fr,adala-word,https://example.org/fake.pdf,,,2026-10-13,false\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    return tmp_path


def test_missing_pdf_fails_and_keeps_existing_dataset(data_dir, capsys):
    out = data_dir / "processed" / "articles.jsonl"
    out.parent.mkdir()
    out.write_text("previous good dataset\n", encoding="utf-8")

    assert build.main([]) == 1
    assert "MISSING fake.pdf" in capsys.readouterr().out
    assert out.read_text(encoding="utf-8") == "previous good dataset\n"


def test_allow_missing_with_nothing_present_still_fails(data_dir):
    assert build.main(["--allow-missing"]) == 1
    assert not (data_dir / "processed" / "articles.jsonl").exists()


def test_build_writes_articles_when_pdf_is_present(data_dir, fake_law_pdf):
    shutil.copy(fake_law_pdf, data_dir / "raw" / "fake.pdf")
    assert build.main([]) == 0
    lines = (data_dir / "processed" / "articles.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
