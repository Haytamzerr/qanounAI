"""Dense and hybrid search end to end, with Qdrant in memory and the fake embedder."""

import numpy as np
import pytest
from qdrant_client import QdrantClient

from qanoun.ingestion.models import Article
from qanoun.retrieval.bm25 import BM25Index
from qanoun.retrieval.corpus import search_text
from qanoun.retrieval.embeddings import HashingEmbedder
from qanoun.retrieval.search import DenseSearcher, HybridSearcher, rrf
from qanoun.retrieval.vector_store import ArticleStore, point_id


def make_article(law: str, language: str, number: int, text: str) -> Article:
    return Article(
        id=f"loi-{law}-{language}-art-{number}",
        law_number=law,
        law_title=f"Loi {law}",
        language=language,
        article_number=str(number),
        title=None,
        hierarchy=[],
        text=text,
        page_start=1,
        source_url="https://example.org",
        bulletin_officiel=None,
        consolidated_as_of=None,
        is_official_version=language == "ar",
    )


ARTICLES = [
    make_article("65-99", "ar", 13, "مدة فترة الاختبار في العقود غير محددة المدة"),
    make_article("65-99", "ar", 231, "العطلة السنوية المؤدى عنها يوم ونصف عن كل شهر"),
    make_article("70-03", "ar", 19, "تكتمل أهلية الزواج بإتمام الفتى والفتاة المتمتعين بقواهما"),
    make_article("09-08", "fr", 7, "Droit d'accès de la personne concernée à ses données"),
]


@pytest.fixture
def store():
    embedder = HashingEmbedder()
    store = ArticleStore(QdrantClient(":memory:"), "test")
    store.recreate(embedder.dim)
    store.upsert(ARTICLES, embedder.embed([search_text(a) for a in ARTICLES]))
    return store


def test_rrf_rewards_agreement():
    # "b" is second in both lists; "a" and "c" are first in one list and absent from the other
    fused = dict(rrf([["a", "b"], ["c", "b"]]))
    assert max(fused, key=fused.get) == "b"
    assert fused["a"] == pytest.approx(1 / 61)


def test_point_ids_are_stable_uuids():
    assert point_id("loi-09-08-fr-art-1") == point_id("loi-09-08-fr-art-1")
    assert point_id("loi-09-08-fr-art-1") != point_id("loi-09-08-ar-art-1")


def test_store_counts_and_filters(store):
    assert store.count() == len(ARTICLES)
    vector = HashingEmbedder().embed(["العطلة السنوية"])[0]
    assert store.search(vector, 1)[0][0] == "loi-65-99-ar-art-231"
    only_family = store.search(vector, 5, law_number="70-03")
    assert [doc for doc, _ in only_family] == ["loi-70-03-ar-art-19"]
    assert all(doc.split("-")[3] == "fr" for doc, _ in store.search(vector, 5, language="fr"))


def test_upsert_twice_does_not_duplicate(store):
    embedder = HashingEmbedder()
    store.upsert(ARTICLES[:1], embedder.embed([search_text(ARTICLES[0])]))
    assert store.count() == len(ARTICLES)


def test_upsert_checks_lengths(store):
    with pytest.raises(ValueError):
        store.upsert(ARTICLES, np.zeros((1, 256), dtype=np.float32))


def test_dense_and_hybrid_find_the_article(store):
    dense = DenseSearcher(HashingEmbedder(), store)
    assert dense("فترة الاختبار", 1) == ["loi-65-99-ar-art-13"]

    bm25 = BM25Index.build({a.id: search_text(a) for a in ARTICLES})
    hybrid = HybridSearcher(bm25, dense, depth=4)
    ranked = hybrid("droit d'accès aux données", 2)
    assert ranked[0] == "loi-09-08-fr-art-7"
    assert len(ranked) == 2


def test_clear_message_when_qdrant_is_not_running():
    from qanoun.retrieval.vector_store import QdrantUnavailable

    with pytest.raises(QdrantUnavailable, match="docker compose up -d qdrant"):
        ArticleStore.connect("http://127.0.0.1:9")  # nothing listens on port 9


def test_folder_mode_keeps_the_data(tmp_path):
    folder = str(tmp_path / "qdrant")
    embedder = HashingEmbedder()
    store = ArticleStore.connect(folder, "test")
    store.recreate(embedder.dim)
    store.upsert(ARTICLES, embedder.embed([search_text(a) for a in ARTICLES]))
    store.client.close()  # only one process may open the folder at a time
    assert ArticleStore.connect(folder, "test").count() == len(ARTICLES)
