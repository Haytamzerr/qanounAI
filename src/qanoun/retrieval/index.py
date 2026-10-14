"""Embed every article and load the vectors into Qdrant.

Usage:
    docker compose up -d qdrant                         # start the vector database
    uv run python -m qanoun.retrieval.index             # embed the articles, then load Qdrant
    uv run python -m qanoun.retrieval.index --embed-only  # only compute the vectors file

Embedding 1,329 articles on a laptop CPU takes several minutes, so the vectors are saved to
`data/processed/embeddings/` with a fingerprint of the model and of every article's text. The
next run reuses them unless something changed: re-loading Qdrant then takes seconds.

`--embed-only` doesn't need Qdrant: it can run in a free cloud notebook (Kaggle, Colab) if the
laptop is too slow. Copy the resulting `.npz` file back into `data/processed/embeddings/`.
"""

import argparse
import hashlib
import time
from collections.abc import Sequence
from pathlib import Path

import numpy as np

from qanoun.config import settings
from qanoun.ingestion.models import Article
from qanoun.retrieval.corpus import load_articles, search_text
from qanoun.retrieval.embeddings import Embedder


def fingerprint(embedder_name: str, articles: Sequence[Article]) -> str:
    """Changes whenever the model, its settings, or any indexed text changes."""
    digest = hashlib.sha256(embedder_name.encode())
    for article in articles:
        digest.update(f"\0{article.id}\0{search_text(article)}".encode())
    return digest.hexdigest()


def cache_path(embedder_name: str, directory: Path | None = None) -> Path:
    slug = embedder_name.replace("/", "--").replace("@", "-")
    return (directory or settings.embeddings_dir) / f"{slug}.npz"


def load_cached(path: Path, expected_fingerprint: str) -> np.ndarray | None:
    if not path.exists():
        return None
    with np.load(path) as saved:
        if str(saved["fingerprint"]) != expected_fingerprint:
            return None
        return saved["vectors"]


def embed_articles(
    articles: Sequence[Article],
    embedder: Embedder,
    directory: Path | None = None,
    log=print,
) -> np.ndarray:
    """Vectors for `articles`, in the same order: from the cache if valid, else computed."""
    path = cache_path(embedder.name, directory)
    expected = fingerprint(embedder.name, articles)
    vectors = load_cached(path, expected)
    if vectors is not None:
        log(f"reusing {len(vectors)} vectors from {path.name}")
        return vectors

    log(f"embedding {len(articles)} articles with {embedder.name} (several minutes on a CPU)…")
    start = time.perf_counter()
    vectors = embedder.embed([search_text(a) for a in articles], show_progress=True)
    log(f"done in {time.perf_counter() - start:.0f} s")
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        path,
        vectors=vectors,
        ids=np.array([a.id for a in articles]),
        fingerprint=np.array(expected),
    )
    log(f"saved to {path}")
    return vectors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Embed the articles and load them into Qdrant.")
    parser.add_argument("--embed-only", action="store_true", help="don't touch Qdrant")
    parser.add_argument(
        "--backend", choices=["sentence-transformers", "onnx"], default=None,
        help="embedding model (default: QANOUN_EMBEDDING_BACKEND)",
    )  # fmt: skip
    parser.add_argument("--collection", default=None, help="Qdrant collection to fill")
    args = parser.parse_args(argv)

    # Imported here so `--help` answers instantly, without loading torch.
    from qanoun.retrieval.embeddings import make_embedder
    from qanoun.retrieval.vector_store import ArticleStore, QdrantUnavailable

    articles = load_articles()  # a missing dataset fails here, before anything is opened
    store = None
    if not args.embed_only:
        try:
            store = ArticleStore.connect(collection=args.collection)  # fail before embedding
        except QdrantUnavailable as error:
            print(error)
            return 1

    try:
        print(f"loading the embedding model ({args.backend or settings.embedding_backend})…")
        embedder = make_embedder(args.backend)
        vectors = embed_articles(articles, embedder)
        if store is not None:
            store.recreate(embedder.dim)
            store.upsert(articles, vectors)
            print(f"Qdrant collection '{store.collection}': {store.count()} articles")
    finally:
        # Always release Qdrant, even after an error: in folder mode an unreleased store keeps
        # the folder locked, and the next run in the same notebook fails with "already accessed".
        if store is not None:
            store.client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
