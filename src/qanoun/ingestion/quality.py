"""Automatic quality checks on parsed articles.

A parser that silently loses or merges articles is worse than one that crashes: the assistant
would cite wrong text with confidence. These checks turn silent errors into loud ones.
"""

import re

from qanoun.ingestion.models import Article

FOOTNOTE_LEAKS = [
    re.compile(r"Bulletin Officiel n°", re.IGNORECASE),  # footnotes cite the BO; articles rarely do
    re.compile(r"^\s*Article \d+\s*:", re.MULTILINE),  # quoted articles of other texts
    re.compile(r"الجريدة الرسمية عدد"),  # Arabic footnotes cite the BO issue number
    re.compile(r"^\s*المادة\s*\d+\s*:", re.MULTILINE),
]


def _base_number(number: str) -> int | None:
    match = re.match(r"\d+", number)
    return int(match.group()) if match else None


def check_articles(articles: list[Article], min_chars: int = 40) -> list[str]:
    """Return a list of human-readable problems. An empty list means all checks passed."""
    problems: list[str] = []
    if not articles:
        return ["no articles parsed"]

    seen: set[str] = set()
    for a in articles:
        if a.id in seen:
            problems.append(f"duplicate article id {a.id}")
        seen.add(a.id)
        if len(a.text) < min_chars:
            problems.append(
                f"article {a.article_number} is suspiciously short ({len(a.text)} chars)"
            )
        for pattern in FOOTNOTE_LEAKS:
            if pattern.search(a.text):
                problems.append(f"article {a.article_number} may contain footnote text")

    numbers = [n for a in articles if (n := _base_number(a.article_number)) is not None]
    expected = 1
    for n in numbers:
        if n > expected:
            problems.append(f"gap in numbering: articles {expected} to {n - 1} are missing")
        expected = max(expected, n + 1)
    return problems
