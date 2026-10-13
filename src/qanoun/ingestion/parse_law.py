"""Parse a Moroccan law (French or Arabic PDF) into articles, using the fonts of each line.

The structure of a law is: chapters, optional sections, articles. Some articles have a short
sub-title (e.g. "Droit d’accès" / "الحق في الولوج"). Text before the first chapter (cover page,
promulgating dahir) is not part of the law's articles and is skipped.

Two things vary between documents, and each lives in its own table:
- the fonts, which depend on how the PDF was produced: a `LayoutProfile`;
- the heading words, which depend on the language: `LanguageRules`.
Supporting a new family of PDFs means adding a profile, not rewriting the parser.
"""

import re
import unicodedata
from dataclasses import dataclass, field

from qanoun.ingestion.models import Article, Language, Source
from qanoun.ingestion.pdf_lines import Line


@dataclass(frozen=True)
class LayoutProfile:
    body_size: float
    chapter_size: float
    section_size: float
    subtitle_size: float  # article sub-titles
    article_size: float
    paragraph_gap: float  # vertical gap (points) that starts a new paragraph
    tolerance: float = 0.3

    @property
    def min_size(self) -> float:
        """Anything smaller than the body text is a footnote or a footnote marker."""
        return self.body_size - self.tolerance


LAYOUTS: dict[str, LayoutProfile] = {
    # Adala texts exported from Word, measured on Law 09-08 (Oct 2026)
    "adala-word": LayoutProfile(
        body_size=14.0,
        chapter_size=16.0,
        section_size=14.0,
        subtitle_size=14.0,
        article_size=15.0,
        paragraph_gap=20.0,
    ),
    "adala-word-ar": LayoutProfile(
        body_size=16.0,
        chapter_size=20.0,
        section_size=19.0,
        subtitle_size=18.0,
        article_size=16.0,
        paragraph_gap=21.0,
    ),
}


@dataclass(frozen=True)
class LanguageRules:
    chapter: re.Pattern[str]
    section: re.Pattern[str]
    article: re.Pattern[str]  # group 1: number or ordinal word, group 2: optional suffix
    first_article: frozenset[str]  # words meaning "first"
    suffixes: dict[str, str]  # e.g. "مكرر" -> "bis"
    sentence_end: re.Pattern[str]


RULES: dict[Language, LanguageRules] = {
    "fr": LanguageRules(
        chapter=re.compile(r"^CHAPITRE\s", re.IGNORECASE),
        section=re.compile(r"^Section\s", re.IGNORECASE),
        article=re.compile(
            r"^Article\s+(premier|\d+)(?:\s*(bis|ter|quater))?\s*[:.]?$", re.IGNORECASE
        ),
        first_article=frozenset({"premier"}),
        suffixes={"bis": "bis", "ter": "ter", "quater": "quater"},
        sentence_end=re.compile(r"[.;:!?»]$"),
    ),
    "ar": LanguageRules(
        chapter=re.compile(r"^الباب\s"),
        section=re.compile(r"^الفرع\s"),
        article=re.compile(r"^المادة\s*(الأولى|\d+)(?:\s*(المكررة|مكررة|مكرر))?\s*[:.]?$"),
        first_article=frozenset({"الأولى"}),
        suffixes={"المكررة": "bis", "مكررة": "bis", "مكرر": "bis"},
        sentence_end=re.compile(r"[.;:!?»؛]$"),
    ),
}

PAGE_NUMBER = re.compile(r"^-\s*\d+\s*-$")


def normalize(text: str) -> str:
    """Unicode normalisation and whitespace clean-up, without changing the wording."""
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"\s+", " ", text).strip()
    return re.sub(r"\s+([,.،])", r"\1", text)


def article_number(heading: str, language: Language = "fr") -> str | None:
    """'Article premier' / 'المادة الأولى' -> '1', 'Article 25 bis' -> '25 bis', else None."""
    rules = RULES[language]
    match = rules.article.match(normalize(heading))
    if not match:
        return None
    raw = match.group(1)
    number = "1" if raw.lower() in rules.first_article else raw
    suffix = match.group(2)
    return f"{number} {rules.suffixes[suffix.lower()]}" if suffix else number


def _close(a: float, b: float, tol: float) -> bool:
    return abs(a - b) <= tol


@dataclass
class _Draft:
    number: str
    page: int
    hierarchy: list[str]
    title: str | None = None
    paragraphs: list[str] = field(default_factory=list)
    last_line: Line | None = None

    def add_body(self, line: Line, profile: LayoutProfile, rules: LanguageRules) -> None:
        text = line.text.strip()
        prev = self.last_line
        if prev is None or not self.paragraphs:
            self.paragraphs.append(text)
        else:
            if line.page == prev.page:
                new_paragraph = line.y - prev.y > profile.paragraph_gap
            else:  # across a page break, trust punctuation
                new_paragraph = bool(rules.sentence_end.search(self.paragraphs[-1]))
            if new_paragraph:
                self.paragraphs.append(text)
            elif self.paragraphs[-1].endswith("-") and not self.paragraphs[-1].endswith(" -"):
                self.paragraphs[-1] += text  # "ci-" + "dessus" -> "ci-dessus"
            else:
                self.paragraphs[-1] += " " + text
        self.last_line = line


def parse_lines(lines: list[Line], source: Source, profile: LayoutProfile) -> list[Article]:
    """Build the list of articles from the lines of one PDF."""
    rules = RULES[source.language]
    tol = profile.tolerance
    chapter: str | None = None
    section: str | None = None
    last_heading: str | None = None  # "chapter" or "section" while a heading may still wrap
    drafts: list[_Draft] = []
    current: _Draft | None = None

    for line in lines:
        text = normalize(line.text)
        if not text or PAGE_NUMBER.match(text):
            continue

        if line.bold and _close(line.size, profile.chapter_size, tol):
            if last_heading == "chapter" and chapter and not rules.chapter.match(text):
                chapter = f"{chapter} {text}"  # heading wrapped onto another line
            else:
                chapter, section, current = text, None, None
            last_heading = "chapter"
            continue

        if chapter is None:
            continue  # cover page and promulgating dahir

        if line.bold and _close(line.size, profile.article_size, tol):
            number = article_number(text, source.language)
            if number is not None:
                hierarchy = [chapter] + ([section] if section else [])
                current = _Draft(number=number, page=line.page, hierarchy=hierarchy)
                drafts.append(current)
                last_heading = None
                continue

        if line.bold and _close(line.size, profile.section_size, tol):
            if rules.section.match(text):
                section, current, last_heading = text, None, "section"
                continue
            if last_heading == "section" and section:
                section = f"{section} {text}"
                continue

        is_subtitle = line.bold and _close(line.size, profile.subtitle_size, tol)
        if is_subtitle and current is not None and not current.paragraphs:
            current.title = f"{current.title} {text}" if current.title else text
            continue

        if current is not None:
            current.add_body(line, profile, rules)
            last_heading = None

    return [_to_article(d, source) for d in drafts]


def _to_article(draft: _Draft, source: Source) -> Article:
    slug = draft.number.replace(" ", "-")
    return Article(
        id=f"loi-{source.law_number}-{source.language}-art-{slug}",
        law_number=source.law_number,
        law_title=source.law_title,
        language=source.language,
        article_number=draft.number,
        title=draft.title,
        hierarchy=draft.hierarchy,
        text="\n".join(normalize(p) for p in draft.paragraphs),
        page_start=draft.page,
        source_url=source.source_url,
        bulletin_officiel=source.bulletin_officiel,
        consolidated_as_of=source.consolidated_as_of,
        is_official_version=source.is_official_version,
    )
