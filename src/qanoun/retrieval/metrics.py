"""Retrieval metrics: did the search put the right articles near the top?

For one question with a set of relevant articles and a ranked list of results:
- hit@k: 1 if at least one relevant article is in the top k, else 0;
- recall@k: the share of relevant articles found in the top k;
- reciprocal rank (RR): 1 / position of the first relevant article (0 if none in the list).
Averaged over all questions, RR gives the MRR (mean reciprocal rank).
"""


def hit_at_k(ranked: list[str], relevant: set[str], k: int) -> float:
    return float(any(doc in relevant for doc in ranked[:k]))


def recall_at_k(ranked: list[str], relevant: set[str], k: int) -> float:
    if not relevant:
        return 0.0
    return len(relevant & set(ranked[:k])) / len(relevant)


def reciprocal_rank(ranked: list[str], relevant: set[str]) -> float:
    for position, doc in enumerate(ranked, start=1):
        if doc in relevant:
            return 1 / position
    return 0.0
