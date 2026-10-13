"""BM25 keyword search, written out in full.

BM25 scores a document for a query by adding up, for each query word found in the document:
- how rare the word is in the whole corpus (IDF): "تعويض" matters more than "عقد";
- how often it appears in the document, with diminishing returns (parameter k1);
- a correction for document length, so long articles don't win just by being long (parameter b).

It is the classic baseline of information retrieval: fast, explainable, and very good at exact
terms ("article 43", "CNSS"). Its weakness is meaning: it can't match "fired" with "dismissal",
or Darija with legal Arabic. That is what embeddings will add.
"""

import math
from collections import Counter
from dataclasses import dataclass, field

from qanoun.retrieval.text import tokenize


@dataclass
class BM25Index:
    k1: float = 1.5
    b: float = 0.75
    ids: list[str] = field(default_factory=list)
    doc_freqs: list[Counter] = field(default_factory=list)
    doc_lengths: list[int] = field(default_factory=list)
    df: Counter = field(default_factory=Counter)  # in how many documents each word appears

    @classmethod
    def build(cls, documents: dict[str, str], k1: float = 1.5, b: float = 0.75) -> "BM25Index":
        index = cls(k1=k1, b=b)
        for doc_id, text in documents.items():
            counts = Counter(tokenize(text))
            index.ids.append(doc_id)
            index.doc_freqs.append(counts)
            index.doc_lengths.append(sum(counts.values()))
            index.df.update(counts.keys())
        return index

    @property
    def avg_length(self) -> float:
        return sum(self.doc_lengths) / max(len(self.doc_lengths), 1)

    def idf(self, word: str) -> float:
        n, df = len(self.ids), self.df.get(word, 0)
        return math.log(1 + (n - df + 0.5) / (df + 0.5))

    def search(self, query: str, k: int = 10) -> list[tuple[str, float]]:
        """The `k` best (document id, score) pairs, best first."""
        words = tokenize(query)
        avg = self.avg_length
        scores = []
        for doc_id, freqs, length in zip(self.ids, self.doc_freqs, self.doc_lengths, strict=True):
            score = 0.0
            for word in words:
                tf = freqs.get(word, 0)
                if tf:
                    norm = tf + self.k1 * (1 - self.b + self.b * length / avg)
                    score += self.idf(word) * tf * (self.k1 + 1) / norm
            if score > 0:
                scores.append((doc_id, score))
        scores.sort(key=lambda pair: -pair[1])
        return scores[:k]
