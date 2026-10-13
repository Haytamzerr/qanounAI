"""Turn a PDF into visual lines that keep their font information.

Why not just `page.get_text()`? Because plain text loses what tells us the structure of a law:
the font size and weight. In the Adala PDFs, chapters, article headings, body text and
footnotes each use a different font size. We keep that information on every line.

Two cleaning steps happen here:
- spans smaller than the body text are dropped: footnotes, and the footnote markers glued to
  words (e.g. "traitement³" read as "traitement3");
- pieces of text sitting on the same baseline are merged into one line, with a space where
  there is a visible gap (justified text is often split into one piece per word).
"""

from dataclasses import dataclass
from pathlib import Path

import pymupdf


@dataclass(frozen=True)
class Span:
    """A piece of text as the PDF stores it."""

    page: int
    x0: float
    x1: float
    baseline: float
    size: float
    bold: bool
    text: str


@dataclass(frozen=True)
class Line:
    """A visual line on a page."""

    page: int
    y: float
    size: float
    bold: bool
    text: str


BASELINE_TOLERANCE = 2.0  # points: spans this close vertically are on the same line
WORD_GAP = 1.5  # points: a horizontal gap bigger than this means a space between spans


def read_spans(pdf_path: Path) -> list[Span]:
    """Read every non-empty text span of the PDF, with its position and font."""
    spans: list[Span] = []
    with pymupdf.open(pdf_path) as doc:
        for page in doc:
            for block in page.get_text("dict")["blocks"]:
                for line in block.get("lines", []):
                    for s in line["spans"]:
                        if not s["text"].strip():
                            continue
                        spans.append(
                            Span(
                                page=page.number + 1,
                                x0=s["bbox"][0],
                                x1=s["bbox"][2],
                                baseline=s["origin"][1],
                                size=round(s["size"], 1),
                                bold=bool(s["flags"] & 16),
                                text=s["text"],
                            )
                        )
    return spans


ORDINAL_SUFFIXES = {"e", "er", "re", "ère", "ème", "eme"}
SUPERSCRIPT_RISE = 6.0  # points: how far above the baseline a superscript can sit


def _attach_ordinals(small: list[Span], body: list[Span]) -> list[Span]:
    """Keep superscript ordinals ("2e alinéa", "1er janvier") that small-font filtering drops.

    Small superscript *digits* are footnote markers and stay dropped. Small superscript
    *letters* glued to a number are part of the legal text, so they are moved onto the
    baseline of the number they belong to.
    """
    kept: list[Span] = []
    for s in small:
        if s.text.strip() not in ORDINAL_SUFFIXES:
            continue
        for target in body:
            glued = (
                target.page == s.page
                and abs(target.baseline - s.baseline) <= SUPERSCRIPT_RISE
                and 0 <= s.x0 - target.x1 <= WORD_GAP
                and target.text.rstrip()[-1:].isdigit()
            )
            if glued:
                kept.append(
                    Span(s.page, s.x0, s.x1, target.baseline, target.size, target.bold, s.text)
                )
                break
    return kept


def group_into_lines(spans: list[Span], min_size: float) -> list[Line]:
    """Drop spans smaller than `min_size`, then merge spans on the same baseline into lines."""
    body = [s for s in spans if s.size >= min_size]
    small = [s for s in spans if s.size < min_size]
    kept = body + _attach_ordinals(small, body)
    kept.sort(key=lambda s: (s.page, s.baseline, s.x0))

    groups: list[list[Span]] = []
    for span in kept:
        last = groups[-1][-1] if groups else None
        same_line = (
            last is not None
            and last.page == span.page
            and abs(last.baseline - span.baseline) <= BASELINE_TOLERANCE
        )
        if same_line:
            groups[-1].append(span)
        else:
            groups.append([span])

    lines: list[Line] = []
    for group in groups:
        group.sort(key=lambda s: s.x0)
        text = group[0].text
        for prev, cur in zip(group, group[1:], strict=False):
            needs_space = cur.x0 - prev.x1 > WORD_GAP
            if needs_space and not text.endswith(" ") and not cur.text.startswith(" "):
                text += " "
            text += cur.text
        first = group[0]
        lines.append(
            Line(page=first.page, y=first.baseline, size=first.size, bold=first.bold, text=text)
        )
    return lines


def read_lines(pdf_path: Path, min_size: float) -> list[Line]:
    return group_into_lines(read_spans(pdf_path), min_size=min_size)
