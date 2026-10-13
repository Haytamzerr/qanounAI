"""Build the article dataset from the PDFs listed in data/sources.csv.

Usage:
    uv run python -m qanoun.ingestion.build                  # every source must be present
    uv run python -m qanoun.ingestion.build --allow-missing  # build from what is downloaded

Outputs:
    data/interim/<file>.txt          readable dump of the parsed articles, for manual checks
    data/processed/articles.jsonl    one JSON record per article (the dataset)
"""

import argparse
import csv
import sys
from pathlib import Path

from qanoun.config import settings
from qanoun.ingestion.models import Article, Source
from qanoun.ingestion.parse_fr import LAYOUTS, parse_lines
from qanoun.ingestion.pdf_lines import read_lines
from qanoun.ingestion.quality import check_articles

SOURCES_CSV = "sources.csv"


def load_sources(path: Path) -> list[Source]:
    with path.open(encoding="utf-8", newline="") as f:
        return [Source.model_validate(row) for row in csv.DictReader(f)]


def parse_source(source: Source, raw_dir: Path) -> list[Article]:
    if source.language != "fr":
        raise NotImplementedError("Arabic parsing comes later in Phase 1")
    profile = LAYOUTS[source.layout]
    lines = read_lines(raw_dir / source.file, min_size=profile.min_size)
    return parse_lines(lines, source, profile)


def write_dump(articles: list[Article], path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        for a in articles:
            f.write(f"=== {a.id} (p. {a.page_start}) {' > '.join(a.hierarchy)}\n")
            if a.title:
                f.write(f"[{a.title}]\n")
            f.write(a.text + "\n\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the article dataset from data/raw/.")
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="build from the PDFs that are present instead of failing when some are missing",
    )
    args = parser.parse_args(argv)

    sources = load_sources(settings.data_dir / SOURCES_CSV)
    missing = [s for s in sources if not (settings.raw_dir / s.file).exists()]
    for s in missing:
        print(f"MISSING {s.file}: download it from {s.source_url}")
        print(f"        and save it as {settings.raw_dir / s.file}")
    if missing and not args.allow_missing:
        print("Nothing written: the existing dataset is left untouched.")
        print("Download the missing files, or run again with --allow-missing.")
        return 1

    all_articles: list[Article] = []
    failed = False
    for source in sources:
        if source in missing:
            continue
        articles = parse_source(source, settings.raw_dir)
        problems = check_articles(articles)
        status = "OK  " if not problems else "FAIL"
        print(f"{status} {source.file}: {len(articles)} articles")
        for p in problems:
            print(f"     - {p}")
        failed |= bool(problems)
        settings.interim_dir.mkdir(parents=True, exist_ok=True)
        write_dump(articles, settings.interim_dir / f"{Path(source.file).stem}.txt")
        all_articles.extend(articles)

    if not all_articles:
        print("No articles parsed: nothing written.")
        return 1

    settings.processed_dir.mkdir(parents=True, exist_ok=True)
    out = settings.processed_dir / "articles.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for a in all_articles:
            f.write(a.model_dump_json() + "\n")
    print(f"wrote {len(all_articles)} articles to {out}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
