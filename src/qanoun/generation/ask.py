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
from qanoun.generation.llm import STATE_PATH, GeminiLLM, configure_logging
from qanoun.retrieval.corpus import load_articles, search_text
from qanoun.understanding.llm_rewrite import LLMRewriter


@cache
def _articles() -> dict:
    return {a.id: a for a in load_articles()}


@cache  # one per process: a notebook can ask, then evaluate, without reloading or relocking
def bm25_retriever() -> Retriever:
    from qanoun.retrieval.bm25 import BM25Index

    index = BM25Index.build({a.id: search_text(a) for a in _articles().values()})
    return _with_sections(lambda query, k: [doc for doc, _ in index.search(query, k)])


@cache  # the model loads once, and Qdrant's folder is opened once (it allows one client)
def dense_retriever() -> Retriever:
    from qanoun.retrieval.embeddings import make_embedder
    from qanoun.retrieval.search import DenseSearcher
    from qanoun.retrieval.vector_store import ArticleStore

    searcher = DenseSearcher(make_embedder(), ArticleStore.connect())
    return _with_sections(searcher)


def _with_sections(search, extra: int = 3) -> Retriever:
    """Top k results, plus up to `extra` opening articles of their main section (decision 50)."""
    from qanoun.retrieval.search import SectionExpander

    expander = SectionExpander(list(_articles().values()))
    return lambda query, k: [_articles()[i] for i in expander.expand(search(query, k), extra)]


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
    if len(answer.history) > 1 or not answer.verified:
        lines += ["", *(f"  {line}" for line in answer.history)]
    timing = ", ".join(f"{k} {v:.1f} s" for k, v in answer.seconds.items())
    lines.append(
        f"\n[{answer.language} · {answer.status} · {timing} · attempts {answer.attempts}"
        f" · {answer.model}]"
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ask a question about Moroccan law.")
    parser.add_argument("question")
    parser.add_argument("--retriever", choices=list(RETRIEVERS), default="dense")
    parser.add_argument(
        "--k", type=int, default=6, help="search results (+ up to 3 from their section)"
    )
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):  # a terminal, not a notebook
        sys.stdout.reconfigure(encoding="utf-8")  # Arabic in the Windows terminal
    configure_logging()  # one line per model attempt, with its time
    llm = GeminiLLM(state_path=STATE_PATH)
    rewriter = None if args.no_rewrite else LLMRewriter(llm)
    answerer = Answerer(RETRIEVERS[args.retriever](), llm, k=args.k, rewriter=rewriter)
    print(render(answerer.answer(args.question)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
