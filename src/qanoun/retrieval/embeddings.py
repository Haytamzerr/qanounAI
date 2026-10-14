"""Turn text into vectors that capture meaning.

Two texts with the same meaning get nearby vectors even when they share no word: "licencié",
"الفصل من الشغل" and "tjrrat mn lkhedma" can land close together. BM25 can't do that, because it
only matches words. Every vector has length 1, so the similarity of two texts is their dot product
(the cosine of the angle between them).

- `BGEM3Embedder` is the real model: BGE-M3, multilingual (100+ languages including Arabic and
  French), run locally through sentence-transformers (2.3 GB, needs torch).
- `OnnxEmbedder` is the same model converted to ONNX with its weights stored as 8-bit integers
  (568 MB, runs with onnxruntime alone): it fits on an 8 GB laptop.
- `HashingEmbedder` is a tiny stand-in for tests: it needs no download and runs in microseconds.
"""

import logging
import os
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


class OnnxEmbedder:
    """BGE-M3 as an 8-bit ONNX model (Xenova/bge-m3, onnx/model_int8.onnx).

    Quantization stores each weight as an 8-bit integer plus a scale instead of a 32-bit float:
    4 times smaller, faster on a CPU, slightly less precise (measured in decision 55). BGE-M3's
    dense vector is the hidden state of the first token ([CLS]), normalised to length 1; the
    sentence-transformers version does the same, so the two produce comparable vectors.
    `session` and `tokenizer` can be passed in for tests.
    """

    def __init__(
        self,
        repo: str | None = None,
        file: str | None = None,
        max_tokens: int | None = None,
        batch_size: int | None = None,
        session=None,
        tokenizer=None,
    ):
        repo = repo or settings.onnx_repo
        file = file or settings.onnx_file
        self.max_tokens = max_tokens or settings.embedding_max_tokens
        self.batch_size = batch_size or settings.embedding_batch_size
        if session is None or tokenizer is None:
            # Harmless on Windows: no symlinks in the download cache (files are copied instead),
            # and no Hugging Face account needed for this public model.
            os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
            logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
            import onnxruntime
            from huggingface_hub import hf_hub_download
            from tokenizers import Tokenizer

            tokenizer = Tokenizer.from_file(hf_hub_download(repo, "tokenizer.json"))
            session = onnxruntime.InferenceSession(
                hf_hub_download(repo, file), providers=["CPUExecutionProvider"]
            )
        tokenizer.enable_truncation(max_length=self.max_tokens)
        tokenizer.enable_padding(pad_id=1, pad_token="<pad>")  # XLM-RoBERTa's padding token
        self.tokenizer = tokenizer
        self.session = session
        self.inputs = {i.name for i in session.get_inputs()}
        self.name = f"{repo}/{file}@{self.max_tokens}"
        self.dim = int(self.embed(["test"]).shape[1])

    def embed(self, texts: Sequence[str], show_progress: bool = False) -> np.ndarray:
        texts = list(texts)
        # Similar lengths in one batch waste less padding; results go back in the input order.
        order = sorted(range(len(texts)), key=lambda i: len(texts[i]))
        vectors: list[np.ndarray] = [np.empty(0)] * len(texts)
        batches = range(0, len(order), self.batch_size)
        if show_progress:
            from tqdm import tqdm

            batches = tqdm(batches, desc="embedding", unit="batch")
        for start in batches:
            chunk = order[start : start + self.batch_size]
            encoded = self.tokenizer.encode_batch([texts[i] for i in chunk])
            feeds = {
                "input_ids": np.array([e.ids for e in encoded], dtype=np.int64),
                "attention_mask": np.array([e.attention_mask for e in encoded], dtype=np.int64),
            }
            if "token_type_ids" in self.inputs:
                feeds["token_type_ids"] = np.zeros_like(feeds["input_ids"])
            hidden = self.session.run(None, feeds)[0]  # (batch, tokens, 1024)
            cls = hidden[:, 0].astype(np.float32)
            cls /= np.maximum(np.linalg.norm(cls, axis=1, keepdims=True), 1e-12)
            for i, vector in zip(chunk, cls, strict=True):
                vectors[i] = vector
        return np.stack(vectors) if vectors else np.zeros((0, 0), dtype=np.float32)


def embedder_name(backend: str | None = None) -> str:
    """The name the chosen backend's embedder will have, known without loading the model:
    enough to find its cached vectors."""
    backend = backend or settings.embedding_backend
    if backend == "onnx":
        return f"{settings.onnx_repo}/{settings.onnx_file}@{settings.embedding_max_tokens}"
    return f"{settings.embedding_model}@{settings.embedding_max_tokens}"


def make_embedder(backend: str | None = None) -> Embedder:
    """The embedding model chosen in the settings (QANOUN_EMBEDDING_BACKEND)."""
    backend = backend or settings.embedding_backend
    if backend == "onnx":
        return OnnxEmbedder()
    if backend == "sentence-transformers":
        return BGEM3Embedder()
    raise ValueError(
        f"unknown embedding backend {backend!r}: use 'onnx' or 'sentence-transformers'"
    )


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
