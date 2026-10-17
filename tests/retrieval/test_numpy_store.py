"""The in-memory store must rank exactly like Qdrant, and load the saved vectors file."""

import numpy as np
import pytest
from qdrant_client import QdrantClient

from qanoun.retrieval.embeddings import HashingEmbedder
from qanoun.retrieval.index import embed_articles
from qanoun.retrieval.vector_store import ArticleStore, NumpyStore

from .test_search import ARTICLES


@pytest.fixture
def vectors():
    return HashingEmbedder().embed([a.text for a in ARTICLES])


def test_same_ranking_as_qdrant(vectors):
    qdrant = ArticleStore(QdrantClient(":memory:"), "test")
    qdrant.recreate(vectors.shape[1])
    qdrant.upsert(ARTICLES, vectors)
    memory = NumpyStore(ARTICLES, vectors)
    for question in [a.text[:40] for a in ARTICLES[:4]]:  # words that occur: no ties at zero
        [q] = HashingEmbedder().embed([question])
        expected = qdrant.search(q, len(ARTICLES))
        got = memory.search(q, len(ARTICLES))
        assert np.allclose([s for _, s in got], [s for _, s in expected], atol=1e-5)
        # same ids for every score above zero (articles sharing no word tie at zero)
        assert [i for i, s in got if s > 1e-6] == [i for i, s in expected if s > 1e-6]


def test_filters_and_small_corpus(vectors):
    store = NumpyStore(ARTICLES, vectors)
    [q] = HashingEmbedder().embed(["contrat"])
    assert all(i.split("-")[3] == "fr" for i, _ in store.search(q, 10, language="fr"))
    assert len(store.search(q, 1000)) == store.count() == len(ARTICLES)


def test_loads_the_saved_vectors_file(tmp_path, monkeypatch):
    from qanoun.config import settings

    monkeypatch.setattr(settings, "data_dir", tmp_path)
    embedder = HashingEmbedder()
    saved = embed_articles(ARTICLES, embedder, log=lambda _: None)
    store = NumpyStore.from_cache(ARTICLES[1:], ["missing@1", embedder.name])  # a smaller corpus
    assert np.array_equal(store.vectors, saved[1:])
    with pytest.raises(FileNotFoundError):
        NumpyStore.from_cache(ARTICLES, ["missing@1"])
