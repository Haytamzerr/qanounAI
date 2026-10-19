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


def _long_article():
    from .test_search import make_article

    items = "\n".join(f"{n}. مخالفة رقم {n} " + "تفاصيل " * 20 for n in range(1, 16))
    lead = "يعاقب بغرامة من خمسمائة إلى ألف درهم كل شخص ارتكب مخالفة من الدرجة الثانية."
    return make_article("52-05", "ar", 185, f"{lead}\n{items}\nالهاتف ممسوكا باليد أثناء السياقة")


def test_long_articles_get_passages_that_keep_the_opening_sentence():
    from qanoun.retrieval.passages import split_passages

    article = _long_article()
    passages = split_passages(article)
    assert len(passages) >= 2
    assert all(p.article_id == article.id for p in passages)
    assert all("يعاقب بغرامة من خمسمائة" in p.text for p in passages)  # the penalty travels
    assert any("الهاتف ممسوكا" in p.text for p in passages)
    items = [p for p in passages if "مخالفة رقم" in p.text]
    assert all(p.text.count("مخالفة رقم") == 1 for p in items)  # one list item per passage
    assert split_passages(ARTICLES[0]) == []  # short articles: none


def test_an_article_scores_as_its_best_passage():
    from qanoun.retrieval.passages import split_passages

    article = _long_article()
    articles = [*ARTICLES, article]
    embedder = HashingEmbedder()
    vectors = embedder.embed([a.text for a in articles])
    passages = split_passages(article)
    passage_vectors = embedder.embed([p.text for p in passages])
    [q] = embedder.embed(["الهاتف ممسوكا باليد أثناء السياقة"])
    plain = NumpyStore(articles, vectors).search(q, len(articles))
    with_passages = NumpyStore(
        articles, vectors, [p.article_id for p in passages], passage_vectors
    ).search(q, len(articles))
    score = {i: s for i, s in plain}
    boosted = {i: s for i, s in with_passages}
    assert boosted[article.id] > score[article.id]
    rank = [i for i, _ in plain].index(article.id)
    assert [i for i, _ in with_passages].index(article.id) <= rank  # never moves down


def test_passage_vectors_are_saved_and_reloaded(tmp_path, monkeypatch):
    from qanoun.config import settings
    from qanoun.retrieval.passages import all_passages, embed_passages

    monkeypatch.setattr(settings, "data_dir", tmp_path)
    articles = [*ARTICLES, _long_article()]
    embedder = HashingEmbedder()
    embed_articles(articles, embedder, log=lambda _: None)
    embed_passages(all_passages(articles), embedder, log=lambda _: None)
    store = NumpyStore.from_cache(articles, [embedder.name])
    assert store.passages == len(all_passages(articles)) > 0


def test_short_articles_that_list_cases_get_one_passage_per_case():
    from qanoun.retrieval.passages import split_passages

    penal_124 = ARTICLES[0].model_copy(
        update={
            "text": "لا جناية ولا جنحة ولا مخالفة في الأحوال الآتية:\n"
            "1 - إذا كان الفعل قد أوجبه القانون وأمرت به السلطة الشرعية.\n"
            "2 - إذا اضطر الفاعل ماديا إلى ارتكاب الجريمة.\n"
            "3 - إذا كانت الجريمة قد استلزمتها ضرورة حالة للدفاع الشرعي عن نفس الفاعل."
        }
    )
    passages = split_passages(penal_124)
    assert len(passages) == 3
    assert all(p.text.count("في الأحوال الآتية") == 1 for p in passages)  # the opening kept
    assert "للدفاع الشرعي" in passages[2].text and "السلطة" not in passages[2].text
    one_item = penal_124.model_copy(update={"text": "يعاقب على ما يلي:\n1 - السرقة."})
    assert split_passages(one_item) == []  # a single item is not a list


class FailingAfter(HashingEmbedder):
    def __init__(self, calls):
        super().__init__()
        self.calls = calls

    def embed(self, texts, show_progress=False):
        if self.calls == 0:
            raise RuntimeError("stopped")
        self.calls -= 1
        return super().embed(texts, show_progress)


def test_an_interrupted_passage_run_resumes_where_it_stopped(tmp_path, monkeypatch):
    from qanoun.config import settings
    from qanoun.retrieval.passages import all_passages, embed_passages, load_passage_vectors

    monkeypatch.setattr(settings, "data_dir", tmp_path)
    passages = all_passages([_long_article()])
    assert len(passages) >= 3
    with pytest.raises(RuntimeError):
        embed_passages(passages, FailingAfter(2), log=lambda _: None, batch=1)
    saved, _ = load_passage_vectors(HashingEmbedder().name, passages)
    assert len(saved) == 2  # the first two batches were kept
    resumed = FailingAfter(len(passages) - 2)  # fails if asked to redo the saved ones
    vectors = embed_passages(passages, resumed, log=lambda _: None, batch=1)
    assert vectors.shape[0] == len(passages)
