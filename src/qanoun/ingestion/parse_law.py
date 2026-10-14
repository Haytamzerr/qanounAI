"""Parse a Moroccan law (French or Arabic PDF) into articles, using the fonts of each line.

A law is a tree of headings (book, title, chapter, section, sub-section; most laws use only
some of them) whose leaves are articles. Some articles have a short sub-title (e.g. "Droit
d’accès" / "الحق في الولوج"). Text before the first heading (cover page, promulgating dahir,
preamble) is not part of the articles and is skipped.

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
    article_size: float
    paragraph_gap: float  # vertical gap (points) that starts a new paragraph
    levels: tuple[tuple[str, float], ...]  # heading levels, top first: (name, font size)
    subtitle_size: float | None = None  # article sub-titles, if the layout has them
    tolerance: float = 0.3

    @property
    def min_size(self) -> float:
        """Anything smaller than the body text is a footnote or a footnote marker."""
        return self.body_size - self.tolerance


LAYOUTS: dict[str, LayoutProfile] = {
    # Adala texts exported from Word, measured on Law 09-08 (Oct 2026)
    "adala-word": LayoutProfile(
        body_size=14.0,
        article_size=15.0,
        paragraph_gap=20.0,
        levels=(("chapter", 16.0), ("section", 14.0)),
        subtitle_size=14.0,
    ),
    "adala-word-ar": LayoutProfile(
        body_size=16.0,
        article_size=16.0,
        paragraph_gap=21.0,
        levels=(("chapter", 20.0), ("section", 19.0)),
        subtitle_size=18.0,
    ),
    # Adala codes in Arabic with books and titles, measured on the Labour Code (July 2026)
    "adala-code-ar": LayoutProfile(
        body_size=15.8,
        article_size=15.8,
        paragraph_gap=21.5,
        levels=(
            ("book", 21.8),
            ("title", 21.0),
            ("chapter", 20.3),
            ("section", 18.8),
            ("subsection", 18.0),
        ),
    ),
    # Family Code in Arabic (July 2021 consolidation): chapters and sections share a font
    "adala-family-ar": LayoutProfile(
        body_size=16.0,
        article_size=16.0,
        paragraph_gap=31.0,
        levels=(("book", 22.0), ("title", 20.0), ("chapter", 18.0), ("section", 18.0)),
    ),
    # Consumer Protection law in Arabic (December 2020 consolidation)
    "adala-consumer-ar": LayoutProfile(
        body_size=16.1,
        article_size=16.1,
        paragraph_gap=21.5,
        levels=(("title", 22.1), ("chapter", 21.1), ("section", 19.9)),
    ),
}


@dataclass(frozen=True)
class LanguageRules:
    levels: dict[str, re.Pattern[str]]  # words that start each heading level
    article: re.Pattern[str]  # group 1: number or ordinal word, group 2: optional suffix
    first_article: frozenset[str]  # words meaning "first"
    suffixes: dict[str, str]  # e.g. "مكرر" -> "bis"
    sentence_end: re.Pattern[str]
    ordinals: dict[str, str] = field(default_factory=dict)  # e.g. "الثالث" -> "3"


RULES: dict[Language, LanguageRules] = {
    "fr": LanguageRules(
        levels={
            "book": re.compile(r"^LIVRE\s", re.IGNORECASE),
            "title": re.compile(r"^TITRE\s", re.IGNORECASE),
            "chapter": re.compile(r"^CHAPITRE\s", re.IGNORECASE),
            "section": re.compile(r"^Section\s", re.IGNORECASE),
            "subsection": re.compile(r"^Sous-section\s", re.IGNORECASE),
        },
        article=re.compile(
            r"^Article\s+(premier|\d+)(?:\s*(bis|ter|quater))?\s*[:.]?$", re.IGNORECASE
        ),
        first_article=frozenset({"premier"}),
        suffixes={"bis": "bis", "ter": "ter", "quater": "quater"},
        sentence_end=re.compile(r"[.;:!?»]$"),
    ),
    "ar": LanguageRules(
        levels={
            "book": re.compile(r"^الكتاب\s"),
            "title": re.compile(r"^القسم\s(?!الفرعي)"),
            "chapter": re.compile(r"^(?:ال)?باب\s"),  # also "باب تمهيدي" (preliminary)
            "section": re.compile(r"^الفرع\s"),
            "subsection": re.compile(r"^القسم الفرعي\s"),
        },
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


def article_heading(
    heading: str, language: Language = "fr", rules: LanguageRules | None = None
) -> tuple[str, str | None] | None:
    """The number of an article heading, and the title printed on the same line if any.

    'Article premier' / 'المادة الأولى' -> ('1', None), 'Article 25 bis' -> ('25 bis', None),
    'الفصل 13: وثيقة التجنيس' -> ('13', 'وثيقة التجنيس') when the rules allow inline titles
    (a third regex group). Anything else -> None.
    """
    rules = rules or RULES[language]
    match = rules.article.match(normalize(heading))
    if not match:
        return None
    raw = match.group(1)
    if raw.lower() in rules.first_article:
        number = "1"
    else:
        number = rules.ordinals.get(raw, re.sub(r"\s+", "", raw))
    suffix = match.group(2)
    if suffix:
        number = f"{number} {rules.suffixes[suffix.lower()]}"
    title = match.group(3) if match.re.groups >= 3 else None
    return number, (title.strip() or None) if title else None


def article_number(
    heading: str, language: Language = "fr", rules: LanguageRules | None = None
) -> str | None:
    """'Article premier' / 'المادة الأولى' -> '1', 'Article 25 bis' -> '25 bis', else None."""
    found = article_heading(heading, language, rules)
    return found[0] if found else None


def _close(a: float, b: float, tol: float) -> bool:
    return abs(a - b) <= tol


def rescue_misformatted_headings(
    all_lines: list[Line], profile: LayoutProfile, language: Language
) -> list[Line]:
    """Find article headings printed by mistake in the small footnote font.

    In the Labour Code PDF, "المادة 517" is printed at 12.8 points like a footnote, so it would
    be dropped and its text merged into article 516. A small line that is exactly an article
    heading (no colon) and is directly followed by body text is such a heading. Footnotes that
    quote other texts ("Article 34:") end with a colon and are followed by small text.
    """
    rescued = []
    for i, line in enumerate(all_lines):
        text = normalize(line.text)
        if line.size >= profile.min_size or text.endswith(":"):
            continue
        if article_number(text, language) is None:
            continue
        following = next(
            (
                m
                for m in all_lines[i + 1 :]
                if m.page == line.page
                and normalize(m.text)
                and not PAGE_NUMBER.match(normalize(m.text))
            ),
            None,
        )
        if (
            following is not None
            and _close(following.size, profile.body_size, profile.tolerance)
            and following.y - line.y < 2 * profile.paragraph_gap
        ):
            rescued.append(Line(line.page, line.y, profile.article_size, True, line.text))
    return rescued


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


def _heading_candidates(line: Line, profile: LayoutProfile) -> list[int]:
    """Heading levels whose font matches the line. Several levels can share a font."""
    if not line.bold:
        return []
    return [
        index
        for index, (_, size) in enumerate(profile.levels)
        if _close(line.size, size, profile.tolerance)
    ]


def parse_lines(
    lines: list[Line],
    source: Source,
    profile: LayoutProfile,
    rules: LanguageRules | None = None,
    start_on_article: bool = False,
) -> list[Article]:
    """Build the list of articles from the lines of one PDF.

    By default the law starts at its first heading (book, chapter…): text before it is the
    cover page and the promulgating dahir. Short texts have no headings at all, only articles:
    `start_on_article` lets the first article start the law too.
    """
    rules = rules or RULES[source.language]
    tol = profile.tolerance
    headings: list[tuple[int, str]] = []  # open headings, top level first: (level, text)
    started = False
    last_heading: int | None = None  # level of the heading that may still wrap onto a new line
    drafts: list[_Draft] = []
    current: _Draft | None = None

    for line in lines:
        text = normalize(line.text)
        if not text or PAGE_NUMBER.match(text):
            continue

        candidates = _heading_candidates(line, profile)
        level = next(
            (i for i in candidates if rules.levels[profile.levels[i][0]].match(text)), None
        )
        if level is not None:  # the font and the heading word agree
            headings = [h for h in headings if h[0] < level] + [(level, text)]
            started, current, last_heading = True, None, level
            continue
        wraps = last_heading in candidates and headings and headings[-1][0] == last_heading
        if wraps and article_number(text, rules=rules) is None:
            headings[-1] = (last_heading, f"{headings[-1][1]} {text}")  # heading wrapped
            continue

        is_heading = line.bold and _close(line.size, profile.article_size, tol)
        found = article_heading(text, rules=rules) if is_heading else None
        number, inline_title = found or (None, None)
        if not started and not (start_on_article and number is not None):
            continue  # cover page, promulgating dahir, preamble

        if is_heading and number is not None:
            started = True
            current = _Draft(
                number=number,
                page=line.page,
                hierarchy=[t for _, t in headings],
            )
            if inline_title and (
                len(inline_title) > 100 or rules.sentence_end.search(inline_title)
            ):  # "الفصل الأول. - يحدث مجلس…": the heading line already holds the text
                current.paragraphs.append(inline_title)
                current.last_line = line
            else:
                current.title = inline_title
            drafts.append(current)
            last_heading = None
            continue

        is_subtitle = (
            line.bold
            and profile.subtitle_size is not None
            and _close(line.size, profile.subtitle_size, tol)
        )
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
