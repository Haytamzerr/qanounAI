"""Parse any Adala law into articles, without a hand-made layout profile.

The five laws in `data/sources.csv` each have a layout profile measured by hand. That does not
scale to the ~960 laws of the Adala catalogue, so here the profile is measured automatically
on each PDF:

- the body font is the size most of the text is written in;
- the article font is the size of the lines that read exactly "المادة 5" / "الفصل الثالث";
- each heading level (book, part, title, chapter, section…) gets the size its heading words
  ("الكتاب", "الباب", "الفرع"…) are printed in, when they are bold.

The lines themselves come from `pdf_lines`, which already repairs reading order and broken
ligatures, and the articles are built by the same `parse_lines` as the curated laws.

Usage (after `python -m qanoun.ingestion.adala download`):
    uv run python -m qanoun.ingestion.adala_parse            # every downloaded law
    uv run python -m qanoun.ingestion.adala_parse --limit 20

Outputs:
    data/processed/adala_articles.jsonl   the articles of every law that parsed cleanly
    data/processed/adala_report.csv       one row per law: status, articles, problems
"""

import argparse
import csv
import re
import time
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from qanoun.config import settings
from qanoun.ingestion.adala import LAW_TYPES, CatalogEntry, is_law, load_catalog
from qanoun.ingestion.models import Article, Source
from qanoun.ingestion.parse_law import (
    PAGE_NUMBER,
    LanguageRules,
    LayoutProfile,
    normalize,
    parse_lines,
)
from qanoun.ingestion.pdf_lines import Line, group_into_lines, read_spans
from qanoun.ingestion.quality import check_articles

# --- Article numbers written as words -----------------------------------------------------

_UNITS = [
    ("الأول", "الأولى"),
    ("الثاني", "الثانية"),
    ("الثالث", "الثالثة"),
    ("الرابع", "الرابعة"),
    ("الخامس", "الخامسة"),
    ("السادس", "السادسة"),
    ("السابع", "السابعة"),
    ("الثامن", "الثامنة"),
    ("التاسع", "التاسعة"),
]
_TENS = ["العشرون", "الثلاثون", "الأربعون", "الخمسون", "الستون", "السبعون", "الثمانون", "التسعون"]


def _ordinals() -> dict[str, str]:
    """ "الأول"/"الأولى" -> "1" … "التاسع والتسعون" -> "99", masculine and feminine."""
    out: dict[str, str] = {}
    for n, (masc, fem) in enumerate(_UNITS, start=1):
        out[masc] = out[fem] = str(n)
    out["العاشر"] = out["العاشرة"] = "10"
    out["الحادي عشر"] = out["الحادية عشرة"] = "11"
    for n, (masc, fem) in enumerate(_UNITS[1:], start=12):
        out[f"{masc} عشر"] = out[f"{fem} عشرة"] = str(n)
    for t, tens in enumerate(_TENS, start=2):
        out[tens] = str(10 * t)
        out[f"الحادي و{tens}"] = out[f"الحادية و{tens}"] = str(10 * t + 1)
        for n, (masc, fem) in enumerate(_UNITS[1:], start=2):
            out[f"{masc} و{tens}"] = out[f"{fem} و{tens}"] = str(10 * t + n)
    # Spellings seen in the PDFs: without hamza, and with the ligature read backwards
    for word, n in list(out.items()):
        for variant in (word.replace("أ", "ا"), word.replace("الأ", "األ")):
            out.setdefault(variant, n)
    # "the sole article" of a one-article text
    for word in ("فريدة", "الفريدة", "فريد", "الفريد", "الوحيدة", "الوحيد"):
        out[word] = "1"
    return out


ORDINALS = _ordinals()
_ORDINAL_ALT = "|".join(re.escape(w) for w in sorted(ORDINALS, key=len, reverse=True))
_SUFFIXES = {
    "مكرر مرتين": "ter",
    "مكررة مرتين": "ter",
    "مكرر ثلاث مرات": "quater",
    "مكررة ثلاث مرات": "quater",
    "المكررة": "bis",
    "مكررة": "bis",
    "مكرر": "bis",
}
_SUFFIX_ALT = "|".join(re.escape(s) for s in sorted(_SUFFIXES, key=len, reverse=True))

RULES = LanguageRules(
    levels={
        "annex": re.compile(r"^(?:ال)?ملحق"),
        "book": re.compile(r"^الكتاب\s"),
        "part": re.compile(r"^الجزء\s"),
        "title": re.compile(r"^القسم\s(?!الفرعي)"),
        "chapter": re.compile(r"^(?:ال)?باب\s"),
        "chapter2": re.compile(r"^الفصل\s"),  # a chapter only where articles are "المادة"
        "section": re.compile(r"^الفرع\s"),
        "subsection": re.compile(r"^(?:القسم الفرعي|المبحث)\s"),
    },
    # "المادة 5", "الفصل 12-1", "المادة الثالثة", "الفصل 230 مكرر", "مادة فريدة",
    # "الفصل 13: وثيقة التجنيس" (a title on the heading line)
    article=re.compile(
        rf"^(?:ال)?(?:مادة|فصل)\s*(\d+(?:\s*[-.]\s*\d+)*|{_ORDINAL_ALT})"
        rf"(?:\s*({_SUFFIX_ALT}))?\s*(?:(?:\s*[:.\-–—])+\s*(.*))?$"
    ),
    first_article=frozenset(),
    suffixes=_SUFFIXES,
    sentence_end=re.compile(r"[.;:!?»؛]$"),
    ordinals=ORDINALS,
)
LEVEL_ORDER = list(RULES.levels)  # top first, used when two levels share a font size
TOLERANCE = 0.3
ARTICLE_SMALLER = 1.5  # points: article headings can be printed a little smaller than the body


# --- Measuring the layout -----------------------------------------------------------------


def _mode(values: list[float]) -> float:
    """The most frequent value; on a tie the smallest (chapters are printed bigger than articles
    and are fewer, so a tie between two sizes is rare and the smaller one is the article)."""
    counts = Counter(values)
    return min(counts, key=lambda v: (-counts[v], v))


def detect_profile(lines: list[Line]) -> LayoutProfile | None:
    """The fonts of one PDF, measured on its lines (all sizes kept). None: no article found."""
    weights: Counter[float] = Counter()
    for line in lines:
        weights[line.size] += len(line.text.strip())
    if not weights:
        return None
    body = weights.most_common(1)[0][0]

    texts = [normalize(line.text) for line in lines]
    articles = [
        line.size
        for line, text in zip(lines, texts, strict=True)
        if line.bold and line.size >= body - ARTICLE_SMALLER and RULES.article.match(text)
    ]
    if not articles:
        return None
    article_size = _mode(articles)

    levels: list[tuple[str, float]] = []
    for name, pattern in RULES.levels.items():
        sizes = [
            line.size
            for line, text in zip(lines, texts, strict=True)
            if line.bold
            and len(text) < 120
            and pattern.match(text)
            and line.size >= article_size - TOLERANCE
            and not (RULES.article.match(text) and abs(line.size - article_size) <= TOLERANCE)
        ]
        if name == "chapter2":  # "الفصل" is a chapter only when printed bigger than articles
            sizes = [s for s in sizes if s > article_size + TOLERANCE]
        if sizes:
            levels.append((name, _mode(sizes)))
    levels.sort(key=lambda lv: (-lv[1], LEVEL_ORDER.index(lv[0])))

    # Line spacing of the body text; a bigger gap starts a new paragraph
    gaps = [
        round(b.y - a.y)
        for a, b in zip(lines, lines[1:], strict=False)
        if a.page == b.page and a.size == b.size == body and 0 < b.y - a.y < 3 * body
    ]
    spacing = _mode(gaps) if gaps else body * 1.2
    return LayoutProfile(
        body_size=body,
        article_size=article_size,
        paragraph_gap=spacing + 2.5,
        levels=tuple(levels),
        tolerance=TOLERANCE,
    )


# --- Law metadata -------------------------------------------------------------------------

LAW_NUMBER = re.compile(r"(?:القانون|قانون)(?:\s+التنظيمي|\s*-\s*الإطار)?\s+رقم\s*(\d+[.\-]\d+)")
DAHIR_NUMBER = re.compile(r"رقم\s*(\d+[.\-]\d+[.\-]\d+)")
SHORT_TITLE = re.compile(
    r"(?:بتنفيذ|بإصدار|بالمصادقة على|بمثابة)\s+((?:ال)?(?:قانون|مجموعة|مدونة).*)$"
)
DAHIR_PREFIX = re.compile(r"^(?:ال)?ظهير[^)]{0,140}\)\s*")  # "ظهير شريف رقم … (5 يناير 1916)"
# Annual finance laws: hundreds of pages of budget tables, out of date every January
FINANCE_LAW = re.compile(r"قانون المالية|القانون المالي|السنة المالية|معدل للمالية|قانون مالية")
REPEALED_LAW = re.compile(r"\(\s*(?:نسخ|منسوخ|ملغى)\s*\)")  # "(نسخ)", not "(نسخ المواد 4 و5)"
# The 1962-1992 constitutions are history, not law in force (2011: "بتنفيذ نص الدستور")
OLD_CONSTITUTION = re.compile(r"دستور المملكة المغربية\s+لسنة")
PERSIAN = str.maketrans({"ی": "ي", "ک": "ك"})  # look-alike letters some PDFs use
# International treaties published or approved by a dahir ("الموافق بموجبه على الاتفاقية…",
# "ظهير بنشر الاتفاقية…"): their articles bind states, and they crowded out Moroccan laws in the
# answers to everyday questions (a rent question found the UN migrant workers convention)
TREATY = re.compile(
    r"الموافق بموجبه?\s+(?:من حيث المبدأ\s+)?على"
    r"|بنشر\s+(?:ال)?(?:اتفاق|ميثاق|بر[و]?توكول|تعديلات|معاهدة)"
    r"|^\s*(?:ال)?(?:اتفاقية|اتفاق|بر[و]?توكول|معاهدة)"
    r"|اتفاق(?:ية)?\s+بين"
)
CLOSING = re.compile(r"^و\s?حرر\s?ب|^وقعه\s+بالعطف")


def law_key(entry: CatalogEntry) -> str:
    """A short readable key for article ids: "65-99" for a law, "dahir-1-73-250" otherwise."""
    title = entry.object.translate(PERSIAN)
    if found := LAW_NUMBER.search(title):
        return found.group(1).replace(".", "-")
    if found := DAHIR_NUMBER.search(title):
        return "dahir-" + found.group(1).replace(".", "-")
    return "adala-" + entry.file_name.removesuffix(".pdf")[:10]


def short_title(entry: CatalogEntry) -> str:
    """'القانون رقم 65.99 المتعلق بمدونة الشغل' rather than the whole promulgating dahir, and
    'ظهير بشأن العفو' rather than 'ظهير شريف رقم 1.57.387 صادر في … (6 فبراير 1958) بشأن العفو'."""
    title = re.sub(r"\s+", " ", entry.object).strip().translate(PERSIAN)
    if re.match(r"(?:ال)?(?:قانون|مدونة|مجموعة|دستور)", title):
        return title
    if found := SHORT_TITLE.search(title):
        return found.group(1)
    if (found := DAHIR_PREFIX.match(title)) and len(title) > found.end() + 5:
        return "ظهير " + title[found.end() :]
    return title


def select(entries: list[CatalogEntry], types: set[str], skip_keys: set[str]) -> list[CatalogEntry]:
    """The laws to parse: chosen types, no finance laws, repealed laws, old constitutions or
    treaties, one PDF per law (the newest), and none of the laws curated by hand (`skip_keys`)."""
    newest: dict[str, CatalogEntry] = {}
    for e in entries:
        if (
            not is_law(e, types)
            or FINANCE_LAW.search(e.object)
            or OLD_CONSTITUTION.search(e.object)
            or TREATY.search(e.object.translate(PERSIAN))
        ):
            continue
        if REPEALED_LAW.search(e.object) or REPEALED_LAW.search(e.name):
            continue
        key = law_key(e)
        if key in skip_keys:
            continue
        if key not in newest or (e.date or "") > (newest[key].date or ""):
            newest[key] = e
    return list(newest.values())


# --- Parsing one law ----------------------------------------------------------------------


@dataclass
class Report:
    key: str
    file: str
    title: str
    status: str  # ok | scanned | no_articles | garbled | error
    pages: int = 0
    articles: int = 0
    problems: int = 0
    first_problem: str = ""
    seconds: float = 0.0


ARABIC = re.compile(r"[ء-ي]")


REPEAL_WORDS = re.compile(r"نسخت|نسخ|ينسخ|منسوخة|منسوخ|ألغيت|ألغي|الفصل|المادة|المكرر|مكرر|\d+")


def is_repealed(article: Article) -> bool:
    """'(نسخ).', 'نسخت', '(ألغي).': an article kept only to say it was repealed, or empty."""
    return len(ARABIC.findall(REPEAL_WORDS.sub("", article.text))) < 3


def article_word(lines: list[Line]) -> str:
    """ "الفصل" or "المادة": the word most article headings of this law start with."""
    words = Counter(
        "الفصل" if "فصل" in text.split()[0] else "المادة"
        for line in lines
        if line.bold and RULES.article.match(text := normalize(line.text))
    )
    return words.most_common(1)[0][0] if words else "المادة"


def _drop_closing(article: Article) -> Article:
    """Cut the signature ("وحرر بالرباط في…") that follows the last article of old dahirs."""
    paragraphs = article.text.split("\n")
    for i, p in enumerate(paragraphs):
        if i and CLOSING.match(p):
            return article.model_copy(update={"text": "\n".join(paragraphs[:i])})
    return article


def parse_entry(entry: CatalogEntry, pdf: Path, key: str) -> tuple[list[Article], Report]:
    start = time.perf_counter()
    report = Report(key=key, file=entry.file_name, title=short_title(entry)[:120], status="ok")
    spans = read_spans(pdf)
    pages = max((s.page for s in spans), default=0)
    report.pages = pages
    text = "".join(s.text for s in spans)
    if pages and len(text) / pages < 200:
        report.status = "scanned"  # image-only pages: needs OCR
        return [], report
    if len(ARABIC.findall(text)) < 0.5 * len(re.sub(r"\s", "", text)):
        report.status = "garbled"  # a font without a usable character map
        return [], report

    profile = detect_profile(group_into_lines(spans, min_size=0.0))
    if profile is None:
        report.status = "no_articles"
        return [], report
    min_size = min(profile.body_size, profile.article_size) - TOLERANCE  # drops footnotes
    lines = [
        line
        for line in group_into_lines(spans, min_size=min_size)
        if not PAGE_NUMBER.match(normalize(line.text))
    ]
    source = Source(
        file=entry.file_name,
        law_number=key,
        law_title=short_title(entry),
        language="ar",
        layout="auto",
        source_url=entry.url,
        downloaded_on=date.today().isoformat(),
        is_official_version=True,  # the Arabic text (consolidated), not a translation
    )
    articles = parse_lines(lines, source, profile, rules=RULES, start_on_article=True)
    word = article_word(lines)
    articles = [
        a.model_copy(update={"text": a.text.translate(PERSIAN), "article_word": word})
        for a in map(_drop_closing, articles)
        if not is_repealed(a)
    ]
    articles = _dedupe_ids(articles)
    problems = check_articles(articles)
    report.articles, report.problems = len(articles), len(problems)
    report.first_problem = problems[0] if problems else ""
    if not articles:
        report.status = "no_articles"
    report.seconds = round(time.perf_counter() - start, 1)
    return articles, report


def _dedupe_ids(articles: list[Article]) -> list[Article]:
    """A number seen twice (an annex restarting at 1, a quoted article) gets "-2", "-3"…"""
    seen: Counter[str] = Counter()
    out = []
    for a in articles:
        seen[a.id] += 1
        out.append(a if seen[a.id] == 1 else a.model_copy(update={"id": f"{a.id}-{seen[a.id]}"}))
    return out


# --- Command line -------------------------------------------------------------------------

DEFAULT_TYPES = LAW_TYPES


def curated_keys() -> set[str]:
    """Law numbers of the hand-curated sources ("65-99"…), which take precedence."""
    path = settings.data_dir / "sources.csv"
    if not path.exists():
        return set()
    with path.open(encoding="utf-8", newline="") as f:
        return {row["law_number"] for row in csv.DictReader(f)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Parse the downloaded Adala laws into articles.")
    parser.add_argument("--types", default=",".join(DEFAULT_TYPES), help="comma-separated")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--raw-dir", type=Path, default=None, help="where the PDFs are")
    args = parser.parse_args(argv)

    raw_dir = args.raw_dir or settings.raw_dir / "adala"
    types = {t.strip() for t in args.types.split(",")}
    chosen = select(load_catalog(), types, curated_keys())
    chosen = [e for e in chosen if (raw_dir / e.file_name).exists()][: args.limit]
    print(f"{len(chosen)} laws to parse from {raw_dir}")

    all_articles: list[Article] = []
    reports: list[Report] = []
    for n, entry in enumerate(chosen, start=1):
        key = law_key(entry)
        try:
            articles, report = parse_entry(entry, raw_dir / entry.file_name, key)
        except Exception as error:  # one broken PDF must not stop the other 959
            articles, report = [], Report(key, entry.file_name, short_title(entry), "error")
            report.first_problem = f"{type(error).__name__}: {error}"[:200]
        reports.append(report)
        if report.status == "ok":
            all_articles += articles
        status = f"{report.status:<11} {report.articles:>4} art."
        print(f"[{n}/{len(chosen)}] {status}  {report.title[:70]}")

    out_dir = settings.processed_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "adala_articles.jsonl").open("w", encoding="utf-8") as f:
        for a in all_articles:
            f.write(a.model_dump_json() + "\n")
    with (out_dir / "adala_report.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(Report.__dataclass_fields__))
        writer.writeheader()
        writer.writerows(vars(r) for r in reports)

    by_status = Counter(r.status for r in reports)
    print(f"\n{len(all_articles)} articles from {by_status['ok']} laws")
    print("  " + ", ".join(f"{s}: {c}" for s, c in by_status.most_common()))
    print(f"  laws with numbering or length warnings: {sum(r.problems > 0 for r in reports)}")
    print(f"saved to {out_dir / 'adala_articles.jsonl'} and adala_report.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
