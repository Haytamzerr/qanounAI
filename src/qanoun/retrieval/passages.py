"""Extra vectors for long articles: one per passage, so a detail deep inside a long list is found.

Article 185 of the Highway Code fines 15 different offences (speeding, priority, a phone held
while driving…) in 4,640 characters. One vector for the whole article is an average of all of
them, and a question about the phone did not find it (decision 67). Long articles are therefore
also cut into passages: one per list item, and windows of about 900 characters for the other
paragraphs, each starting with the article's opening sentence ("يعاقب بغرامة من 500 إلى 1000
درهم…"), so the passage keeps the penalty that applies to the items it lists. Search scores an
article by its best vector: the article's or a passage's. The answer still receives the whole
article.

Short articles that list cases get one passage per item too (decision 77): article 124 of the
Penal Code is only 397 characters, but its three cases (an act ordered by law, force majeure,
self-defence) are different subjects, and its single vector did not answer a question about
self-defence. Their other paragraphs are not cut into windows: the article vector covers them.

Usage (after the article vectors exist; the configured embedder, e.g. 8-bit ONNX on the PC):
    uv run python -m qanoun.retrieval.passages

The passage vectors are saved next to the article vectors ("…-passages.npz") with one hash per
passage: a later run only embeds passages that are new or changed.
"""

import argparse
import re
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from qanoun.config import settings
from qanoun.ingestion.models import Article

LONG = 1500  # characters: articles longer than this get passages
WINDOW = 900  # characters of article text per passage
LEAD = 300  # characters of the opening sentence repeated in each passage
ITEM = re.compile(r"(?=(?:^|\s)\d{1,2}\s*[.-]\s)")  # "2. عدم احترام…", "3 - …" inside a paragraph


@dataclass(frozen=True)
class Passage:
    article_id: str
    number: int
    text: str


def _units(text: str) -> list[str]:
    """Paragraphs, and the numbered items inside a long paragraph."""
    units: list[str] = []
    for paragraph in text.split("\n"):
        parts = ITEM.split(paragraph) if len(paragraph) > WINDOW else [paragraph]
        units += [p.strip() for p in parts if p.strip()]
    return units


LIST_ITEM = re.compile(r"^\s*(?:\d{1,2}|[أ-ي])\s*[.)\-–]\s|^\s*[-–•\u00ad]\s*")
INTRO = 200  # characters of the sentence that opens a list ("…إحدى المخالفات التالية:")
MIN_ITEMS = 2  # a short article gets item passages only if it lists at least this many cases


def split_passages(article: Article) -> list[Passage]:
    """The passages of an article: long ones, and short ones that list cases (else none).

    Each item of a list ("4. الاستعمال أو التحدث بالهاتف…") is a passage of its own, preceded by
    the article's opening sentence and the sentence that opens the list: a list item says what
    is forbidden, the opening sentence says the penalty. The other paragraphs are grouped into
    windows of about WINDOW characters (decision 67).
    """
    units = _units(article.text)
    short = len(article.text) <= LONG
    if short and sum(bool(LIST_ITEM.match(u)) for u in units[1:]) < MIN_ITEMS:
        return []
    lead = units[0][:LEAD]
    where = " > ".join(article.hierarchy)
    header = f"{article.law_title}\n{where}\n{article.label} {article.article_number}"
    texts: list[str] = []
    current = ""
    intro = ""

    def flush() -> None:
        nonlocal current
        if current:
            texts.append(f"{header}\n{lead}\n{current}")
            current = ""

    for unit in units[1:]:
        if LIST_ITEM.match(unit):
            flush()
            context = f"{intro}\n" if intro else ""
            texts.append(f"{header}\n{lead}\n{context}{unit[:WINDOW]}")
            continue
        intro = unit[:INTRO]  # a paragraph that is not an item may open the next list
        if short:
            continue  # the article's own vector covers the rest of a short article
        while len(unit) > WINDOW:  # a single very long paragraph: cut it
            flush()
            texts.append(f"{header}\n{lead}\n{unit[:WINDOW]}")
            unit = unit[WINDOW:]
        if current and len(current) + len(unit) + 1 > WINDOW:
            flush()
        current = f"{current}\n{unit}" if current else unit
    flush()
    return [Passage(article.id, n, text) for n, text in enumerate(texts, start=1)]


def all_passages(articles: Sequence[Article]) -> list[Passage]:
    return [p for a in articles for p in split_passages(a)]


def passage_hashes(embedder_name: str, passages: Sequence[Passage]) -> np.ndarray:
    import hashlib

    return np.array(
        [
            hashlib.sha256(f"{embedder_name}\0{p.article_id}\0{p.text}".encode()).hexdigest()[:32]
            for p in passages
        ]
    )


def passages_path(embedder_name: str, directory: Path | None = None) -> Path:
    from qanoun.retrieval.index import cache_path

    path = cache_path(embedder_name, directory)
    return path.with_name(path.stem + "-passages.npz")


def load_passage_vectors(
    embedder_name: str, passages: Sequence[Passage], directory: Path | None = None
) -> tuple[list[Passage], np.ndarray]:
    """The passages that have a saved vector, and those vectors (possibly none)."""
    path = passages_path(embedder_name, directory)
    if not path.exists():
        return [], np.zeros((0, 0), dtype=np.float32)
    with np.load(path) as saved:
        row = {h: i for i, h in enumerate(saved["hashes"])}
        vectors = saved["vectors"]
    hashes = passage_hashes(embedder_name, passages)
    found = [(p, row[h]) for p, h in zip(passages, hashes, strict=True) if h in row]
    if not found:
        return [], np.zeros((0, vectors.shape[1]), dtype=np.float32)
    return [p for p, _ in found], vectors[[i for _, i in found]]


def embed_passages(
    passages: Sequence[Passage],
    embedder,
    directory: Path | None = None,
    log=print,
    batch: int = 1000,
):
    """Vectors for every passage: saved ones reused, missing ones computed, all saved."""
    path = passages_path(embedder.name, directory)
    hashes = passage_hashes(embedder.name, passages)
    known: dict[str, np.ndarray] = {}
    if path.exists():
        with np.load(path) as saved:
            known = dict(zip(saved["hashes"], saved["vectors"], strict=True))
    missing = [i for i, h in enumerate(hashes) if h not in known]
    log(f"{len(passages)} passages: {len(passages) - len(missing)} saved, {len(missing)} to embed")
    path.parent.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    for first in range(0, len(missing), batch):
        part = missing[first : first + batch]
        new = embedder.embed([passages[i].text for i in part], show_progress=True)
        known.update(zip(hashes[part], new, strict=True))
        _save(path, known)  # an interrupted run resumes from here
        done = first + len(part)
        log(f"{done}/{len(missing)} embedded ({time.perf_counter() - start:.0f} s), saved")
    vectors = np.stack([known[h] for h in hashes]) if len(passages) else np.zeros((0, 0))
    np.savez(path, vectors=vectors.astype(np.float32), hashes=hashes)
    log(f"saved to {path}")
    return vectors


def _save(path: Path, known: dict[str, np.ndarray]) -> None:
    hashes = np.array(list(known))
    vectors = np.stack(list(known.values())).astype(np.float32)
    tmp = path.with_name(path.stem + ".tmp.npz")
    np.savez(tmp, vectors=vectors, hashes=hashes)
    tmp.replace(path)  # never a half-written file, even if the run is stopped while saving


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Embed the passages of long articles.")
    parser.add_argument("--backend", choices=["sentence-transformers", "onnx"], default=None)
    args = parser.parse_args(argv)

    from qanoun.retrieval.corpus import load_articles
    from qanoun.retrieval.embeddings import make_embedder

    passages = all_passages(load_articles())
    print(f"loading the embedding model ({args.backend or settings.embedding_backend})…")
    embed_passages(passages, make_embedder(args.backend))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
