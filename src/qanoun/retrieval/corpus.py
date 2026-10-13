"""Load the article dataset and build the text each search method indexes."""

from pathlib import Path

from qanoun.config import settings
from qanoun.ingestion.models import Article


def load_articles(path: Path | None = None) -> list[Article]:
    path = path or settings.processed_dir / "articles.jsonl"
    with path.open(encoding="utf-8") as f:
        return [Article.model_validate_json(line) for line in f if line.strip()]


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
