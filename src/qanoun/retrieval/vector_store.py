"""Store article vectors in Qdrant and find the nearest ones to a question.

Qdrant is a vector database: given a question's vector, it returns the closest article vectors
quickly, and can filter on fields stored next to each vector (the payload), such as the law or
the language. It runs in Docker (`docker compose up -d qdrant`); tests use its in-memory mode.

Each point holds one article: its vector, and the full article record as payload, so a search
result carries everything needed to show and cite the article.
"""

import uuid
import warnings
from collections.abc import Sequence
from pathlib import Path

import numpy as np
from qdrant_client import QdrantClient, models

from qanoun.config import settings
from qanoun.ingestion.models import Article


class QdrantUnavailable(RuntimeError):
    pass


def point_id(article_id: str) -> str:
    """Qdrant ids must be numbers or UUIDs: derive a stable UUID from the article id."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"qanoun:{article_id}"))


class ArticleStore:
    def __init__(self, client: QdrantClient, collection: str | None = None):
        self.client = client
        self.collection = collection or settings.qdrant_collection

    @classmethod
    def connect(cls, url: str | None = None, collection: str | None = None) -> "ArticleStore":
        """Connect to Qdrant, with a clear message if it isn't running.

        An http(s) URL means the Qdrant server (Docker). Anything else is a folder: Qdrant then
        runs inside this Python process and saves to that folder, with no server at all. Handy
        in a cloud notebook or on a PC short of memory; fine for a few thousand articles.
        """
        url = url or settings.qdrant_url
        if not url.startswith(("http://", "https://")):
            Path(url).mkdir(parents=True, exist_ok=True)
            return cls(QdrantClient(path=url), collection)
        # Versions are pinned together (docker-compose.yml, uv.lock); our own check below gives
        # a clearer message than the client's version warning when the server is down.
        client = QdrantClient(url=url, timeout=30, check_compatibility=False)
        try:
            client.get_collections()
        except Exception as error:
            raise QdrantUnavailable(
                f"Can't reach Qdrant at {url}. Start Docker Desktop, then run "
                "`docker compose up -d qdrant`."
            ) from error
        return cls(client, collection)

    def recreate(self, dim: int) -> None:
        """Start from an empty collection of `dim`-sized vectors compared by cosine."""
        if self.client.collection_exists(self.collection):
            self.client.delete_collection(self.collection)
        self.client.create_collection(
            self.collection,
            vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE),
        )
        with warnings.catch_warnings():  # the folder mode ignores indexes, and warns about it
            warnings.simplefilter("ignore", UserWarning)
            for field in ("law_number", "language"):  # fields we filter on get an index
                self.client.create_payload_index(
                    self.collection, field, field_schema=models.PayloadSchemaType.KEYWORD
                )

    def upsert(self, articles: Sequence[Article], vectors: np.ndarray, batch: int = 128) -> None:
        if len(articles) != len(vectors):
            raise ValueError(f"{len(articles)} articles but {len(vectors)} vectors")
        for start in range(0, len(articles), batch):
            points = [
                models.PointStruct(
                    id=point_id(article.id),
                    vector=vector.tolist(),
                    payload=article.model_dump(mode="json"),
                )
                for article, vector in zip(
                    articles[start : start + batch], vectors[start : start + batch], strict=True
                )
            ]
            self.client.upsert(self.collection, points=points, wait=True)

    def count(self) -> int:
        if not self.client.collection_exists(self.collection):
            return 0
        return self.client.count(self.collection, exact=True).count

    def search(
        self,
        vector: np.ndarray,
        k: int = 10,
        *,
        law_number: str | None = None,
        language: str | None = None,
    ) -> list[tuple[str, float]]:
        """The `k` nearest articles as (article id, cosine similarity), best first."""
        conditions = [
            models.FieldCondition(key=key, match=models.MatchValue(value=value))
            for key, value in (("law_number", law_number), ("language", language))
            if value is not None
        ]
        response = self.client.query_points(
            self.collection,
            query=vector.tolist(),
            limit=k,
            query_filter=models.Filter(must=conditions) if conditions else None,
            with_payload=["id"],
        )
        return [(point.payload["id"], point.score) for point in response.points]


class NumpyStore:
    """The saved article vectors searched directly in memory, without a database.

    Qdrant's folder mode rewrites its files on every insert and slows down past 20,000 articles:
    loading the 34,106 articles of the full corpus on the 8 GB PC did not finish. Comparing a
    question with every article is one matrix product (34,106 × 1,024 numbers, a few
    milliseconds), and the vectors file computed once on Kaggle is all it needs: no index step.
    Enable with QANOUN_VECTOR_STORE=numpy (decision 66).
    """

    def __init__(self, articles: Sequence[Article], vectors: np.ndarray):
        if len(articles) != len(vectors):
            raise ValueError(f"{len(articles)} articles but {len(vectors)} vectors")
        self.ids = [a.id for a in articles]
        self.vectors = np.ascontiguousarray(vectors, dtype=np.float32)
        self.law_numbers = np.array([a.law_number for a in articles])
        self.languages = np.array([a.language for a in articles])

    @classmethod
    def from_cache(cls, articles: Sequence[Article], names: Sequence[str]) -> "NumpyStore":
        """Vectors from the first cache file (one per embedder name) that matches `articles`."""
        from qanoun.retrieval.index import article_hashes, cache_path, fingerprint, load_cached

        for name in names:
            vectors = load_cached(
                cache_path(name), fingerprint(name, articles), article_hashes(name, articles)
            )
            if vectors is not None:
                return cls(articles, vectors)
        tried = ", ".join(cache_path(n).name for n in names)
        raise FileNotFoundError(
            f"No vectors file matches the {len(articles)} articles (looked for {tried} in "
            f"{settings.embeddings_dir}). Compute it with `python -m qanoun.retrieval.index "
            "--embed-only` (a Kaggle GPU works) and copy it there."
        )

    def count(self) -> int:
        return len(self.ids)

    def search(
        self,
        vector: np.ndarray,
        k: int = 10,
        *,
        law_number: str | None = None,
        language: str | None = None,
    ) -> list[tuple[str, float]]:
        """The `k` nearest articles as (article id, cosine similarity), best first."""
        scores = self.vectors @ np.asarray(vector, dtype=np.float32)  # unit vectors: cosine
        if law_number is not None:
            scores = np.where(self.law_numbers == law_number, scores, -np.inf)
        if language is not None:
            scores = np.where(self.languages == language, scores, -np.inf)
        k = min(k, len(scores))
        top = np.argpartition(-scores, k - 1)[:k] if k else np.array([], dtype=int)
        top = top[np.argsort(-scores[top])]
        return [(self.ids[i], float(scores[i])) for i in top if np.isfinite(scores[i])]

    def close(self) -> None:  # same shape as a Qdrant client, nothing to release
        pass
