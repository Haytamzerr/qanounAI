"""Load the article dataset and build the text each search method indexes."""

from pathlib import Path

from qanoun.config import settings
from qanoun.ingestion.models import Article


def load_articles(path: Path | None = None) -> list[Article]:
    """The articles of `path`, or of the configured corpus (QANOUN_CORPUS=core|full)."""
    articles: list[Article] = []
    for file in [path] if path else settings.corpus_files:
        with file.open(encoding="utf-8") as f:
            articles += [Article.model_validate_json(line) for line in f if line.strip()]
    return articles


def search_text(article: Article) -> str:
    """What gets indexed: the law, where the article sits, its sub-title, then its text.

    The headings add context the article text often lacks: an article on "notice periods" may
    never say "work contract", but its chapter does.
    """
    parts = [article.law_title, *article.hierarchy]
    if article.title:
        parts.append(article.title)
    parts.append(article.text)
    return "\n".join(parts)
