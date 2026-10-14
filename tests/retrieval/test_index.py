"""The vector cache: reused when nothing changed, recomputed when anything did."""

import numpy as np

from qanoun.retrieval.embeddings import HashingEmbedder
from qanoun.retrieval.index import cache_path, embed_articles

from .test_search import ARTICLES, make_article


class CountingEmbedder(HashingEmbedder):
    def __init__(self):
        super().__init__()
        self.calls = 0

    def embed(self, texts, show_progress=False):
        self.calls += 1
        return super().embed(texts, show_progress)


def test_hashing_vectors_are_unit_length():
    vectors = HashingEmbedder().embed(["عقد الشغل", "contrat de travail", ""])
    assert vectors.shape == (3, 256)
    assert np.allclose(np.linalg.norm(vectors[:2], axis=1), 1)
    assert not vectors[2].any()  # empty text: zero vector, no division by zero


def test_cache_is_reused_then_invalidated(tmp_path):
    embedder = CountingEmbedder()
    first = embed_articles(ARTICLES, embedder, tmp_path, log=lambda _: None)
    assert cache_path(embedder.name, tmp_path).exists()

    again = embed_articles(ARTICLES, embedder, tmp_path, log=lambda _: None)
    assert embedder.calls == 1  # second run read the file
    assert np.array_equal(first, again)

    edited = [*ARTICLES[:-1], make_article("09-08", "fr", 7, "Texte modifié")]
    embed_articles(edited, embedder, tmp_path, log=lambda _: None)
    assert embedder.calls == 2  # one article changed: everything is recomputed


def test_a_smaller_corpus_reuses_the_saved_vectors(tmp_path):
    embedder = CountingEmbedder()
    full = embed_articles(ARTICLES, embedder, tmp_path, log=lambda _: None)
    fewer = embed_articles(ARTICLES[1:], embedder, tmp_path, log=lambda _: None)
    assert embedder.calls == 1  # articles removed: rows taken from the file, nothing computed
    assert np.array_equal(fewer, full[1:])
    edited = [*ARTICLES[1:-1], make_article("09-08", "fr", 7, "Texte modifié")]
    embed_articles(edited, embedder, tmp_path, log=lambda _: None)
    assert embedder.calls == 2  # an edited article still forces a new computation


def test_cache_file_name_is_safe():
    assert cache_path("BAAI/bge-m3@1024").name == "BAAI--bge-m3-1024.npz"


def test_cached_names_match_the_real_embedders():
    """The index finds cached vectors by name before loading any model: names must agree."""
    from types import SimpleNamespace

    from qanoun.config import settings
    from qanoun.retrieval.embeddings import OnnxEmbedder, embedder_name

    from .test_onnx_embedder import FakeSession, FakeTokenizer

    onnx = OnnxEmbedder(session=FakeSession(), tokenizer=FakeTokenizer())
    assert embedder_name("onnx") == onnx.name
    full = SimpleNamespace(name=f"{settings.embedding_model}@{settings.embedding_max_tokens}")
    assert embedder_name("sentence-transformers") == full.name == "BAAI/bge-m3@1024"
