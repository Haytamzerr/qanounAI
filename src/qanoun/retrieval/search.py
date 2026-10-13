"""Search methods: keywords (BM25), meaning (dense vectors), and both combined (hybrid).

Hybrid search runs the two searches and merges their rankings with Reciprocal Rank Fusion (RRF):
each article scores 1 / (k + rank) in every list where it appears, and the scores are added.
RRF only looks at ranks, never at raw scores, so it doesn't matter that a BM25 score of 12.3 and
a cosine of 0.61 are on unrelated scales. An article ranked well by both searches beats one
ranked first by only one of them.
"""

from collections import defaultdict
from collections.abc import Sequence

from qanoun.retrieval.bm25 import BM25Index
from qanoun.retrieval.embeddings import Embedder
from qanoun.retrieval.vector_store import ArticleStore

RRF_K = 60  # the usual constant from the original RRF paper (Cormack et al., 2009)


def rrf(rankings: Sequence[Sequence[str]], k: int = RRF_K) -> list[tuple[str, float]]:
    """Merge several rankings (best first) into one, as (id, fused score) best first."""
    scores: dict[str, float] = defaultdict(float)
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking, start=1):
            scores[doc_id] += 1 / (k + rank)
    return sorted(scores.items(), key=lambda pair: -pair[1])


class DenseSearcher:
    """Embed the question, then ask Qdrant for the nearest articles."""

    def __init__(self, embedder: Embedder, store: ArticleStore):
        self.embedder = embedder
        self.store = store

    def search(self, question: str, k: int = 10) -> list[tuple[str, float]]:
        [vector] = self.embedder.embed([question])
        return self.store.search(vector, k)

    def __call__(self, question: str, k: int = 10) -> list[str]:
        return [doc_id for doc_id, _ in self.search(question, k)]


class HybridSearcher:
    """BM25 and dense search, each taking its top `depth`, fused with RRF."""

    def __init__(self, bm25: BM25Index, dense: DenseSearcher, depth: int = 50):
        self.bm25 = bm25
        self.dense = dense
        self.depth = depth

    def search(self, question: str, k: int = 10) -> list[tuple[str, float]]:
        keyword = [doc_id for doc_id, _ in self.bm25.search(question, self.depth)]
        meaning = [doc_id for doc_id, _ in self.dense.search(question, self.depth)]
        return rrf([keyword, meaning])[:k]

    def __call__(self, question: str, k: int = 10) -> list[str]:
        return [doc_id for doc_id, _ in self.search(question, k)]
