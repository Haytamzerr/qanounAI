"""Turn text into vectors that capture meaning.

Two texts with the same meaning get nearby vectors even when they share no word: "licencié",
"الفصل من الشغل" and "tjrrat mn lkhedma" can land close together. BM25 can't do that, because it
only matches words. Every vector has length 1, so the similarity of two texts is their dot product
(the cosine of the angle between them).

- `BGEM3Embedder` is the real model: BGE-M3, multilingual (100+ languages including Arabic and
  French), run locally on the CPU through sentence-transformers.
- `HashingEmbedder` is a tiny stand-in for tests: it needs no download and runs in microseconds.
"""

import zlib
from collections.abc import Sequence
from typing import Protocol

import numpy as np

from qanoun.config import settings
from qanoun.retrieval.text import tokenize


class Embedder(Protocol):
    name: str  # identifies the model and its settings: a different name means different vectors
    dim: int

    def embed(self, texts: Sequence[str], show_progress: bool = False) -> np.ndarray:
        """One unit-length float32 row per text, shape (len(texts), dim)."""
        ...


class BGEM3Embedder:
    """BAAI/bge-m3 through sentence-transformers.

    The model (about 2.3 GB) is downloaded from Hugging Face the first time, then read from the
    local cache. BGE-M3 needs no "query:" / "passage:" prefixes: questions and articles are
    embedded the same way.
    """

    def __init__(
        self,
        model_name: str | None = None,
        max_tokens: int | None = None,
        batch_size: int | None = None,
    ):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as error:  # CI installs without the embeddings group
            raise RuntimeError(
                "The embedding model needs the `embeddings` dependency group: run `uv sync`."
            ) from error

        model_name = model_name or settings.embedding_model
        self.max_tokens = max_tokens or settings.embedding_max_tokens
        self.batch_size = batch_size or settings.embedding_batch_size
        self.model = SentenceTransformer(model_name)  # uses the GPU if there is one
        self.model.max_seq_length = self.max_tokens
        self.name = f"{model_name}@{self.max_tokens}"
        self.dim = int(self.embed(["test"]).shape[1])

    def embed(self, texts: Sequence[str], show_progress: bool = False) -> np.ndarray:
        vectors = self.model.encode(
            list(texts),
            batch_size=self.batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=show_progress,
        )
        return np.asarray(vectors, dtype=np.float32)


class HashingEmbedder:
    """Bag of words hashed into a fixed-size vector. For tests only.

    Texts sharing words get similar vectors, which is enough to test the search plumbing
    without a 2 GB model. It understands nothing about meaning.
    """

    def __init__(self, dim: int = 256):
        self.dim = dim
        self.name = f"hashing-{dim}"

    def embed(self, texts: Sequence[str], show_progress: bool = False) -> np.ndarray:
        vectors = np.zeros((len(texts), self.dim), dtype=np.float32)
        for row, text in enumerate(texts):
            for word in tokenize(text):
                vectors[row, zlib.crc32(word.encode()) % self.dim] += 1.0
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        return vectors / np.where(norms == 0, 1, norms)
