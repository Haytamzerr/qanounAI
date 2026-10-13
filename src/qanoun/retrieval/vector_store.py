"""Store article vectors in Qdrant and find the nearest ones to a question.

Qdrant is a vector database: given a question's vector, it returns the closest article vectors
quickly, and can filter on fields stored next to each vector (the payload), such as the law or
the language. It runs in Docker (`docker compose up -d qdrant`); tests use its in-memory mode.

Each point holds one article: its vector, and the full article record as payload, so a search
result carries everything needed to show and cite the article.
"""

import uuid
from collections.abc import Sequence

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
        """Connect to the Qdrant server, with a clear message if it isn't running."""
        url = url or settings.qdrant_url
        client = QdrantClient(url=url, timeout=30)
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
