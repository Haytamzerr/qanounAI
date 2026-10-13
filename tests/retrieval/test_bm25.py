"""BM25 on a tiny corpus where the right answer is known."""

from qanoun.retrieval.bm25 import BM25Index

DOCS = {
    "notice": "يكون إنهاء عقد الشغل مبنيا على احترام أجل الإخطار",
    "leave": "يستحق كل أجير عطلة سنوية مؤدى عنها",
    "contract": "عقد الشغل عقد بين الأجير والمشغل عقد عقد",
    "fr": "La période d'essai du contrat de travail",
}


def test_rare_word_finds_its_article():
    index = BM25Index.build(DOCS)
    assert index.search("أجل الإخطار", k=1)[0][0] == "notice"
    assert index.search("العطلة السنوية", k=1)[0][0] == "leave"


def test_common_word_weighs_less_than_a_rare_one():
    index = BM25Index.build(DOCS)
    assert index.idf("اخطار") > index.idf("عقد")


def test_no_match_returns_nothing():
    index = BM25Index.build(DOCS)
    assert index.search("chhal dyal lconji", k=5) == []


def test_keywords_do_not_cross_languages():
    # The known weakness that embeddings will fix: a French query can't find Arabic text
    index = BM25Index.build(DOCS)
    assert [doc for doc, _ in index.search("préavis de licenciement", k=5)] == []
