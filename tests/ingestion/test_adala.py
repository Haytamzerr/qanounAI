"""The Adala catalogue on pages shaped like the real site (fixtures cut from saved pages)."""

import json
from pathlib import Path

import httpx
import pytest

from qanoun.ingestion.adala import (
    Adala,
    CatalogEntry,
    entries_from_results,
    load_catalog,
    merge,
    next_data,
    save_catalog,
    stats,
)

FIXTURES = Path(__file__).parent / "fixtures"
SEARCH = json.loads((FIXTURES / "adala_search_page.json").read_text(encoding="utf-8"))
THEMES = json.loads((FIXTURES / "adala_themes_page.json").read_text(encoding="utf-8"))


def as_html(data: dict) -> str:
    script = f'<script id="__NEXT_DATA__" type="application/json">{json.dumps(data)}</script>'
    return f"<html>{script}</html>"


def entry(path="uploads/a.pdf", law_type="ظهير", themes=("المادة المدنية",)) -> CatalogEntry:
    return CatalogEntry(path=path, name="n", object="o", law_type=law_type, law_number=None,
                        themes=list(themes), resource=None, date=None, language="AR")  # fmt: skip


def test_real_result_fields_are_read():
    results = SEARCH["props"]["pageProps"]["searchResult"]["data"]
    first = entries_from_results(results)[0]
    assert first.path.startswith("uploads/") and first.path.endswith(".pdf")
    assert first.law_type == "مرسوم" and first.law_number == "2.18.32"
    assert first.themes == ["المادة المدنية"]
    assert first.url.startswith("https://adala.justice.gov.ma/api/uploads/")
    assert " " not in first.url  # the Arabic file name is URL-encoded
    assert first.file_name.endswith(".pdf") and len(first.file_name) == 20


def test_next_data_is_required():
    with pytest.raises(ValueError, match="changed its site"):
        next_data("<html>no data</html>")


def test_duplicates_across_subjects_are_merged():
    merged = merge([entry(themes=["A"]), entry(themes=["B"]), entry(path="uploads/b.pdf")])
    assert len(merged) == 2
    assert merged[0].themes == ["A", "B"]


def fake_site(pages_served: list[str]):
    def handler(request: httpx.Request) -> httpx.Response:
        pages_served.append(str(request.url))
        if request.url.path == "/themes":
            return httpx.Response(200, text=as_html(THEMES))
        if request.url.path == "/search":
            data = json.loads(json.dumps(SEARCH))
            data["props"]["pageProps"]["searchResult"]["total"] = 4  # 2 pages of 3, then empty
            if request.url.params["page"] == "2":
                data["props"]["pageProps"]["searchResult"]["data"] = data["props"]["pageProps"][
                    "searchResult"
                ]["data"][:1]
            return httpx.Response(200, text=as_html(data))
        if request.url.path.startswith("/api/uploads/"):
            return httpx.Response(200, content=b"%PDF-1.7 fake")
        return httpx.Response(404)

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_catalog_walks_every_subject_and_page_then_resumes_from_cache(tmp_path):
    served: list[str] = []
    adala = Adala(cache_dir=tmp_path, client=fake_site(served), sleep=lambda s: None,
                  log=lambda _: None)  # fmt: skip
    entries = adala.catalog()
    themes = THEMES["props"]["pageProps"]["themes"]
    assert len(served) == 1 + 2 * len(themes)  # themes page + 2 pages per subject (3 + 1 results)
    assert len(entries) == 3  # the same PDFs under both subjects are merged
    names = {t["name"].strip() for t in themes}
    assert names <= set(entries[0].themes)  # every subject it was listed under is kept

    served.clear()
    Adala(cache_dir=tmp_path, client=fake_site(served), sleep=lambda s: None,
          log=lambda _: None).catalog()  # fmt: skip
    assert served == []  # everything came from the cache


def test_requests_are_spaced_out(tmp_path):
    waits = []
    adala = Adala(cache_dir=tmp_path, client=fake_site([]), sleep=waits.append, delay=1.0)
    adala.get("https://adala.justice.gov.ma/themes")
    adala.get("https://adala.justice.gov.ma/themes")
    assert waits and 0 < waits[0] <= 1.0


def test_download_keeps_pdfs_once(tmp_path):
    served: list[str] = []
    adala = Adala(cache_dir=tmp_path, client=fake_site(served), sleep=lambda s: None)
    target = adala.download(entry(), tmp_path / "pdf")
    adala.download(entry(), tmp_path / "pdf")
    assert target.read_bytes().startswith(b"%PDF") and len(served) == 1


def test_save_load_and_stats(tmp_path):
    entries = [entry(), entry(path="uploads/b.pdf", law_type="منشور"),
               entry(path="uploads/c.pdf", law_type="منشور")]  # fmt: skip
    path = save_catalog(entries, tmp_path / "c.jsonl")
    assert load_catalog(path) == sorted(entries, key=lambda e: (e.law_type, e.date or "", e.path))
    text = stats(entries)
    assert text.startswith("3 documents (AR: 3)")
    assert "    2  منشور" in text
