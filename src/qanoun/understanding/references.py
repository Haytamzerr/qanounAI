"""Articles the question names itself: "l'article 400 du Code pénal", "المادة 53 من مدونة الشغل".

Meaning search finds articles by what they say. When a person names an article, it must be
looked up directly, for two reasons (decision 71):

- the question may rest on a false premise ("according to article 400 of the Penal Code, theft
  is punished by 10 years…"): the assistant can only correct it if it reads article 400;
- the article may not exist ("article 1500 of the Labour Code"): the assistant must say so
  rather than search for something close and answer as if it were that article.

A reference is a law named by its usual name (Code pénal, مدونة الأسرة, Moudawana…) or by its
number ("loi 67.12", "القانون رقم 31.08"), and one or more article numbers.
"""

import re
from collections import Counter, defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

from qanoun.ingestion.models import Article

# Usual names of the main laws → a pattern matched against the law titles of the corpus
LAW_NAMES: list[tuple[re.Pattern, re.Pattern]] = [
    (re.compile(p, re.IGNORECASE), re.compile(t))
    for p, t in [
        (r"code\s+p[ée]nal|القانون الجنائي|ال9انون الجنائي|l9anoun l?jina2i", r"^مجموعة القانون الجنائي"),  # noqa: E501
        (r"code\s+du\s+travail|مدونة الشغل|moudawan(?:a|at)\s+(?:a|e)?ch?ghol", r"مدونة الشغل"),
        (r"code\s+de\s+la\s+famille|moudawan(?:a|at)\s+(?:al)?\s*osra|\bmoudawana\b(?!\s+(?:du|de|a?ch?ghol|t[ie]jara|sir|l))|مدونة الأسرة|مدونة الاسرة", r"مدونة الأسرة"),  # noqa: E501
        (r"\bD\.?O\.?C\b|code\s+des\s+obligations|قانون الالتزامات", r"^قانون الالتزامات و ?العقود"),  # noqa: E501
        (r"code\s+de\s+commerce|مدونة التجارة", r"مدونة التجارة"),
        (r"code\s+de\s+la\s+route|مدونة السير", r"مدونة السير"),
        (r"proc[ée]dure\s+p[ée]nale|المسطرة الجنائية", r"^القانون رقم 22\.01 "),
        (r"proc[ée]dure\s+civile|المسطرة المدنية", r"^القانون رقم 58\.25 "),
        (r"droits\s+r[ée]els|الحقوق العينية", r"مدونة الحقوق العينية"),
        (r"constitution|الدستور", r"بتنفيذ نص الدستور"),
        (r"code\s+de\s+la\s+nationalit[ée]|قانون الجنسية", r"قانون الجنسية المغربية"),
        (r"protection\s+du\s+consommateur|حماية المستهلك", r"حماية المستهلك"),
    ]
]  # fmt: skip
LAW_NUMBER = re.compile(
    r"(?:\bloi|القانون|قانون)\s*(?:n°|no\.?|رقم)?\s*(\d{1,3})\s*[.\-/]\s*(\d{2})\b", re.I
)
ARTICLE = re.compile(
    r"(?:l'?article|\barticles?|\bart\.|المادة|المواد|الفصل|الفصول|\blmad+a|\blfasl|\bfasl)"
    r"\s*(?:رقم\s*)?(\d{1,4}(?:\s*[-.]\s*\d{1,3})?)(?:\s*(bis|ter|مكرر))?",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Reference:
    law_number: str
    law_title: str
    article_number: str
    article: Article | None  # None: the law has no such article
    last_article: int | None  # highest article number of the law, for the note


class ReferenceResolver:
    def __init__(self, articles: Sequence[Article]):
        self.by_number: dict[tuple[str, str], list[Article]] = defaultdict(list)
        sizes: Counter[str] = Counter()
        self.titles: dict[str, str] = {}
        self.last: dict[str, int] = {}
        for a in articles:
            self.by_number[(a.law_number, a.article_number)].append(a)
            sizes[a.law_number] += 1
            self.titles.setdefault(a.law_number, a.law_title)
            if (n := re.match(r"\d+", a.article_number)) and "-" not in a.article_number:
                self.last[a.law_number] = max(self.last.get(a.law_number, 0), int(n.group()))
        self.sizes = sizes

    def _law_for_name(self, title_pattern: re.Pattern) -> str | None:
        matches = [k for k, t in self.titles.items() if title_pattern.search(t)]
        return max(matches, key=lambda k: self.sizes[k]) if matches else None

    def laws_named(self, question: str) -> list[str]:
        laws = [self._law_for_name(t) for p, t in LAW_NAMES if p.search(question)]
        for a, b in LAW_NUMBER.findall(question):
            for key in (f"{a}-{b}", f"{int(a):02d}-{b}", f"{a.zfill(3)}-{b}"):
                if key in self.titles:
                    laws.append(key)
                    break
        return list(dict.fromkeys(k for k in laws if k))

    def resolve(self, question: str, language: str = "ar") -> list[Reference]:
        """The articles named in the question, when it names exactly one law."""
        laws = self.laws_named(question)
        numbers = [
            re.sub(r"\s+", "", n) + (" bis" if suffix else "")
            for n, suffix in ARTICLE.findall(question)
        ]
        if len(laws) != 1 or not numbers:
            return []
        law = laws[0]
        refs = []
        for number in dict.fromkeys(numbers):
            found = self.by_number.get((law, number), [])
            preferred = [a for a in found if a.language == ("fr" if language == "fr" else "ar")]
            article = (preferred or found or [None])[0]
            refs.append(Reference(law, self.titles[law], number, article, self.last.get(law)))
        return refs


def note(reference: Reference) -> str | None:
    """What the model must be told about a reference it cannot read."""
    if reference.article is not None:
        return None
    span = f" (its articles go up to {reference.last_article})" if reference.last_article else ""
    return (
        f"The question mentions article {reference.article_number} of «{reference.law_title}». "
        f"This article does not exist in the official text{span}. Say so clearly; if the sources "
        "answer the underlying question, give the right articles."
    )
