"""Ask Qanoun AI a question from the terminal.

    uv run python -m qanoun.generation.ask "chhal dyal lconji 3ndi f l3am?"
    uv run python -m qanoun.generation.ask "…" --retriever bm25   # no embedding model needed

`dense` (the default, best) needs the BGE-M3 model and Qdrant; `bm25` only needs the articles
file, for a PC short of memory.
"""

import argparse
import sys
from functools import cache

from qanoun.generation.answer import Answer, Answerer, Retriever
from qanoun.generation.llm import GeminiLLM
from qanoun.retrieval.corpus import load_articles, search_text


@cache
def _articles() -> dict:
    return {a.id: a for a in load_articles()}


def bm25_retriever() -> Retriever:
    from qanoun.retrieval.bm25 import BM25Index

    index = BM25Index.build({a.id: search_text(a) for a in _articles().values()})
    return lambda query, k: [_articles()[doc] for doc, _ in index.search(query, k)]


def dense_retriever() -> Retriever:
    from qanoun.retrieval.embeddings import BGEM3Embedder
    from qanoun.retrieval.search import DenseSearcher
    from qanoun.retrieval.vector_store import ArticleStore

    searcher = DenseSearcher(BGEM3Embedder(), ArticleStore.connect())
    return lambda query, k: [_articles()[doc] for doc in searcher(query, k)]


RETRIEVERS = {"dense": dense_retriever, "bm25": bm25_retriever}


def render(answer: Answer) -> str:
    lines = [answer.text, ""]
    if answer.cited:
        lines.append("Sources:")
        for n in answer.cited:
            a = answer.sources[n - 1]
            label = "Article" if a.language == "fr" else "المادة"
            official = "official text" if a.is_official_version else "translation"
            lines.append(f"  [{n}] {a.law_title}, {label} {a.article_number} ({official})")
            lines.append(f"      {a.source_url}")
    if not answer.verified:
        lines.append("\n⚠ Citation check failed: " + "; ".join(answer.problems))
    timing = ", ".join(f"{k} {v:.1f} s" for k, v in answer.seconds.items())
    lines.append(f"\n[{answer.language} · {answer.status} · {timing} · attempts {answer.attempts}]")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ask a question about Moroccan law.")
    parser.add_argument("question")
    parser.add_argument("--retriever", choices=list(RETRIEVERS), default="dense")
    parser.add_argument("--k", type=int, default=5, help="articles given to the model")
    args = parser.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")  # Arabic in the Windows terminal
    answerer = Answerer(RETRIEVERS[args.retriever](), GeminiLLM(), k=args.k)
    print(render(answerer.answer(args.question)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
