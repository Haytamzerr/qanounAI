"""Catalogue and download the legal texts published on Adala (adala.justice.gov.ma).

Adala, the Ministry of Justice's portal, lists about 5,500 documents under 63 subjects: laws and
dahirs, but also decrees, circulars, treaties, reports. Its pages are built with Next.js, which
delivers each page's data as JSON; we read that JSON instead of scraping the HTML.

Usage (on a machine that can reach Adala):
    uv run python -m qanoun.ingestion.adala catalog     # list everything (~400 requests, ~10 min)
    uv run python -m qanoun.ingestion.adala stats       # what the catalogue contains, by type
    uv run python -m qanoun.ingestion.adala download    # the PDFs of the chosen types

Politeness: one request per second, an identifying User-Agent, every page cached on disk so an
interrupted run resumes where it stopped and nothing is downloaded twice.
"""

import argparse
import hashlib
import json
import re
import time
from collections import Counter
from collections.abc import Callable, Iterable
from pathlib import Path
from urllib.parse import quote

import httpx
from pydantic import BaseModel

from qanoun.config import settings

BASE = "https://adala.justice.gov.ma"
USER_AGENT = "QanounAI/0.1 (student research project; github.com/Haytamzerr/qanounAI)"
NEXT_DATA = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)
# Laws: dahirs, dahirs with force of law, laws, organic laws, codes. Decrees, circulars,
# treaties and reports are left out.
LAW_TYPES = ("ظهير", "ظهير بمثابة قانون", "قانون", "قانون تنظيمي", "مدونة")
DAHIR_TITLE = re.compile(r"\s*(?:ال)?ظه[يی]ر")


def is_law(entry: "CatalogEntry", types: Iterable[str] = LAW_TYPES) -> bool:
    """A law by its type, or a law Adala filed as a decree: the Highway Code (52.05) is listed
    as "مرسوم" although its title is "ظهير شريف … بتنفيذ القانون رقم 52.05"."""
    if entry.law_type in types:
        return True
    return entry.law_type == "مرسوم" and bool(DAHIR_TITLE.match(entry.object))


class CatalogEntry(BaseModel):
    path: str  # "uploads/2024/05/22/….pdf": the PDF, and our unique key
    name: str
    object: str  # the full official title ("ظهير شريف رقم … بتنفيذ القانون رقم …")
    law_type: str  # ظهير, مرسوم, منشور…
    law_number: str | None
    themes: list[str]  # a text can sit under several subjects
    resource: str | None
    date: str | None  # Gregorian, ISO
    language: str  # "AR" or "FR"

    @property
    def url(self) -> str:
        return f"{BASE}/api/{quote(self.path)}"

    @property
    def file_name(self) -> str:
        """A short stable name for the downloaded PDF (the real names are long Arabic titles)."""
        return hashlib.sha1(self.path.encode()).hexdigest()[:16] + ".pdf"


def next_data(html: str) -> dict:
    """The JSON a Next.js page embeds in <script id="__NEXT_DATA__">."""
    found = NEXT_DATA.search(html)
    if not found:
        raise ValueError("no __NEXT_DATA__ in the page: has Adala changed its site?")
    return json.loads(found.group(1))


def entries_from_results(results: Iterable[dict]) -> list[CatalogEntry]:
    entries = []
    for item in results:
        meta = item.get("fileMeta") or {}
        entries.append(
            CatalogEntry(
                path=item["path"],
                name=item.get("name") or "",
                object=meta.get("object") or item.get("name") or "",
                law_type=((meta.get("LawType") or {}).get("name") or "").strip(),
                law_number=meta.get("lawNumber") or None,
                themes=[t] if (t := (meta.get("theme") or {}).get("name")) else [],
                resource=(meta.get("fileRessource") or {}).get("name"),
                date=meta.get("gregorianDate"),
                language=item.get("language") or "AR",
            )
        )
    return entries


def merge(entries: Iterable[CatalogEntry]) -> list[CatalogEntry]:
    """One entry per PDF; subjects of duplicates are combined."""
    by_path: dict[str, CatalogEntry] = {}
    for e in entries:
        if e.path in by_path:
            known = by_path[e.path]
            known.themes = sorted(set(known.themes) | set(e.themes))
        else:
            by_path[e.path] = e.model_copy()
    return list(by_path.values())


class Adala:
    """A polite client: one request per `delay` seconds, retries, and a page cache on disk."""

    def __init__(
        self,
        cache_dir: Path | None = None,
        client: httpx.Client | None = None,
        delay: float = 1.0,
        sleep: Callable[[float], None] = time.sleep,
        log=print,
    ):
        self.cache_dir = cache_dir or settings.data_dir / "cache" / "adala"
        self.client = client or httpx.Client(
            timeout=30, headers={"User-Agent": USER_AGENT}, follow_redirects=True
        )
        self.delay = delay
        self.sleep = sleep
        self.log = log
        self._last = 0.0

    def get(self, url: str, params: dict | None = None) -> httpx.Response:
        for attempt in range(3):
            wait = self.delay - (time.monotonic() - self._last)
            if wait > 0:
                self.sleep(wait)
            self._last = time.monotonic()
            try:
                response = self.client.get(url, params=params)
                if response.status_code < 500:
                    response.raise_for_status()
                    return response
            except httpx.TransportError as error:
                self.log(f"  network error ({error}), retrying")
            self.sleep(5 * (attempt + 1))
        raise RuntimeError(f"Adala did not answer for {url}")

    def page_data(
        self, path: str, params: dict | None = None, cache_key: str | None = None
    ) -> dict:
        """pageProps of an Adala page, from the cache if already fetched."""
        cached = self.cache_dir / "pages" / f"{cache_key}.json" if cache_key else None
        if cached and cached.exists():
            return json.loads(cached.read_text(encoding="utf-8"))
        props = next_data(self.get(f"{BASE}{path}", params).text)["props"]["pageProps"]
        if cached:
            cached.parent.mkdir(parents=True, exist_ok=True)
            cached.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
        return props

    def themes(self) -> list[dict]:
        return self.page_data("/themes", cache_key="themes")["themes"]

    def search_page(self, theme_id: int, page: int) -> tuple[list[CatalogEntry], int]:
        params = {"term": "", "themes": theme_id, "start_date": "", "end_date": "", "page": page}
        props = self.page_data("/search", params, cache_key=f"theme-{theme_id}-page-{page}")
        result = props["searchResult"]
        return entries_from_results(result["data"]), int(result["total"])

    def catalog(self) -> list[CatalogEntry]:
        """Every document of every subject, merged by PDF."""
        collected: list[CatalogEntry] = []
        themes = self.themes()
        for n, theme in enumerate(themes, start=1):
            page, received = 1, 0
            while True:  # count what arrives rather than assume a page size
                entries, total = self.search_page(theme["id"], page)
                for e in entries:  # also record the subject it was listed under
                    e.themes = sorted(set(e.themes) | {theme["name"].strip()})
                collected += entries
                received += len(entries)
                if not entries or received >= total:
                    break
                page += 1
            self.log(f"[{n}/{len(themes)}] {theme['name'].strip()}: {total} documents")
        return merge(collected)

    def download(self, entry: CatalogEntry, folder: Path) -> Path:
        target = folder / entry.file_name
        if not target.exists():
            folder.mkdir(parents=True, exist_ok=True)
            content = self.get(entry.url).content
            if not content.startswith(b"%PDF"):
                raise ValueError(f"not a PDF: {entry.url}")
            target.write_bytes(content)
        return target


def catalog_path() -> Path:
    return settings.data_dir / "catalog" / "adala.jsonl"


def save_catalog(entries: list[CatalogEntry], path: Path | None = None) -> Path:
    path = path or catalog_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for e in sorted(entries, key=lambda e: (e.law_type, e.date or "", e.path)):
            f.write(e.model_dump_json() + "\n")
    return path


def load_catalog(path: Path | None = None) -> list[CatalogEntry]:
    with (path or catalog_path()).open(encoding="utf-8") as f:
        return [CatalogEntry.model_validate_json(line) for line in f if line.strip()]


def stats(entries: list[CatalogEntry]) -> str:
    by_type = Counter(e.law_type or "(none)" for e in entries)
    by_language = Counter(e.language for e in entries)
    lines = [f"{len(entries)} documents ({', '.join(f'{k}: {v}' for k, v in by_language.items())})"]
    lines += [f"  {count:>5}  {law_type}" for law_type, count in by_type.most_common()]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Catalogue and download Adala's legal texts.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("catalog", help="list every document of every subject")
    sub.add_parser("stats", help="what the catalogue contains")
    download = sub.add_parser("download", help="download the PDFs of the chosen types")
    download.add_argument("--types", default=",".join(LAW_TYPES), help="comma-separated")
    download.add_argument("--limit", type=int, default=None)
    args = parser.parse_args(argv)

    if args.command == "catalog":
        entries = Adala().catalog()
        path = save_catalog(entries)
        print(f"\n{stats(entries)}\n\nsaved to {path}")
    elif args.command == "stats":
        print(stats(load_catalog()))
    else:
        types = {t.strip() for t in args.types.split(",")}
        chosen = [e for e in load_catalog() if is_law(e, types)][: args.limit]
        folder = settings.raw_dir / "adala"
        adala = Adala()
        failed = []
        for n, entry in enumerate(chosen, start=1):
            try:
                adala.download(entry, folder)
                print(f"[{n}/{len(chosen)}] {entry.name[:80]}")
            except (RuntimeError, ValueError, httpx.HTTPError) as error:
                failed.append(entry.path)
                print(f"[{n}/{len(chosen)}] FAILED {entry.name[:60]}: {error}")
        print(f"\n{len(chosen) - len(failed)} PDFs in {folder}, {len(failed)} failed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
