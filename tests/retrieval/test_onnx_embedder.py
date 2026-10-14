"""The 8-bit ONNX embedder's own logic, with a fake tokenizer and a fake model."""

from types import SimpleNamespace

import numpy as np
import pytest

from qanoun.retrieval.embeddings import OnnxEmbedder, make_embedder


class FakeTokenizer:
    def enable_truncation(self, max_length):
        self.max_length = max_length

    def enable_padding(self, pad_id, pad_token):
        self.pad_id = pad_id

    def encode_batch(self, texts):
        width = max(len(t) for t in texts)
        return [
            SimpleNamespace(
                ids=[len(t)] + [self.pad_id] * (width - 1),  # first token encodes the length
                attention_mask=[1] * len(t) + [0] * (width - len(t)),
            )
            for t in texts
        ]


class FakeSession:
    """Hidden state of token 0 = [length, 1, 0, …]: easy to check after normalisation."""

    def __init__(self, with_token_types=False):
        names = ["input_ids", "attention_mask"] + (["token_type_ids"] if with_token_types else [])
        self.inputs = [SimpleNamespace(name=n) for n in names]
        self.feeds = []

    def get_inputs(self):
        return self.inputs

    def run(self, _outputs, feeds):
        self.feeds.append(feeds)
        ids = feeds["input_ids"]
        hidden = np.zeros((ids.shape[0], ids.shape[1], 4), dtype=np.float32)
        hidden[:, 0, 0] = ids[:, 0]
        hidden[:, 0, 1] = 1.0
        hidden[:, 1:, 2] = 99.0  # other tokens must be ignored
        return [hidden]


def make(**kwargs):
    return OnnxEmbedder(session=kwargs.pop("session", FakeSession()), tokenizer=FakeTokenizer(),
                        batch_size=2, **kwargs)  # fmt: skip


def test_first_token_normalised_in_input_order():
    embedder = make()
    texts = ["aaaa", "a", "aaa", "aa", "aaaaa"]  # batched by length, returned in this order
    vectors = embedder.embed(texts)
    assert vectors.shape == (5, 4) and embedder.dim == 4
    assert np.allclose(np.linalg.norm(vectors, axis=1), 1)
    expected = np.array([[len(t), 1, 0, 0] for t in texts], dtype=np.float32)
    expected /= np.linalg.norm(expected, axis=1, keepdims=True)
    assert np.allclose(vectors, expected)


def test_token_type_ids_only_when_the_model_wants_them():
    plain, typed = FakeSession(), FakeSession(with_token_types=True)
    make(session=plain).embed(["abc"])
    make(session=typed).embed(["abc"])
    assert "token_type_ids" not in plain.feeds[-1]
    assert not typed.feeds[-1]["token_type_ids"].any()


def test_name_identifies_the_model_for_the_vector_cache():
    embedder = make(repo="Xenova/bge-m3", file="onnx/model_int8.onnx", max_tokens=512)
    assert embedder.name == "Xenova/bge-m3/onnx/model_int8.onnx@512"
    assert embedder.tokenizer.max_length == 512


def test_unknown_backend_is_explained():
    with pytest.raises(ValueError, match="onnx"):
        make_embedder("tensorflow")
