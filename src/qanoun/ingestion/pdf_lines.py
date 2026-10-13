"""Turn a PDF into visual lines that keep their font information.

Why not just `page.get_text()`? Because plain text loses what tells us the structure of a law:
the font size and weight. In the Adala PDFs, chapters, article headings, body text and
footnotes each use a different font size. We keep that information on every line.

Three cleaning steps happen here:
- Arabic ligatures that the PDF stores with their letters swapped are put back in order
  (see `fix_ligatures`);
- spans smaller than the body text are dropped: footnotes, and the footnote markers glued to
  words (e.g. "traitement³" read as "traitement3");
- pieces of text sitting on the same baseline are merged into one line, right to left for
  Arabic, with a space where there is a visible gap (justified text is often split into one
  piece per word).
"""

import re
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


ARABIC_LETTER = re.compile(r"[\u0600-\u06FF]")
LATIN_LETTER = re.compile(r"[A-Za-zÀ-ÿ]")


def is_rtl(text: str) -> bool:
    """A line is read right to left when it has more Arabic than Latin letters."""
    return len(ARABIC_LETTER.findall(text)) > len(LATIN_LETTER.findall(text))


ALEFS = set("اأإآ")
ZERO_WIDTH = 0.05  # points: a glyph narrower than this is drawn inside its neighbour


def fix_ligatures(chars: list[tuple[str, float]]) -> str:
    """Rebuild a span's text from (character, glyph width) pairs, repairing Arabic ligatures.

    Word draws lam-alef (لا لأ لإ لآ) and Allah (ﷲ) as one glyph. When the PDF is read back,
    that glyph's letters come out in reverse order: "الأولى" is read as "األولى", "لله" as "هلل".
    The tell-tale sign is that every letter of the ligature except the last has zero width.
    So: a zero-width alef followed by lam, or a zero-width run starting with ه, is reversed
    with the letter that follows it. A real alef (e.g. the article "ال") has a normal width and
    is never touched, and a zero-width alef that already follows its lam is left as it is.
    """
    out: list[str] = []
    i = 0
    while i < len(chars):
        char, width = chars[i]
        is_zero = width < ZERO_WIDTH and char.strip()
        if is_zero and char in ALEFS and i + 1 < len(chars) and chars[i + 1][0] == "ل":
            out += ["ل", char]
            i += 2
            continue
        if is_zero and char == "ه":
            j = i
            while j < len(chars) and chars[j][1] < ZERO_WIDTH:
                j += 1
            run = [c for c, _ in chars[i : min(j + 1, len(chars))]]
            out += reversed(run)
            i = j + 1
            continue
        out.append(char)
        i += 1
    return "".join(out)


LTR_CHAR = re.compile(r"[0-9A-Za-zÀ-ÿ]")
NUMBER_JOINER = set(".,/-:")  # kept inside a left-to-right run when between two LTR chars


def reading_order(chars: list[tuple[str, float, float]]) -> list[tuple[str, float]]:
    """Put an Arabic span's characters in reading order using their positions.

    `chars` holds (character, x0, x1) in the order the PDF gives them. For Arabic letters that
    order is usually right, but spaces, punctuation and quotes are often misplaced: ".الخاصة"
    instead of "الخاصة.". Their *positions* are always right, so we read the span from right to
    left by position, then flip runs of digits and Latin letters (e.g. "09.08", "CNDP") back to
    left to right. Ties keep the PDF order, which the ligature repair relies on.
    """
    ordered = sorted(range(len(chars)), key=lambda i: (-chars[i][2], i))
    out = [(chars[i][0], chars[i][2] - chars[i][1]) for i in ordered]

    def is_ltr(k: int) -> bool:
        c = out[k][0]
        if LTR_CHAR.match(c):
            return True
        inside = 0 < k < len(out) - 1
        return (
            c in NUMBER_JOINER
            and inside
            and bool(LTR_CHAR.match(out[k - 1][0]) and LTR_CHAR.match(out[k + 1][0]))
        )

    k = 0
    while k < len(out):
        if is_ltr(k):
            end = k
            while end + 1 < len(out) and is_ltr(end + 1):
                end += 1
            out[k : end + 1] = reversed(out[k : end + 1])
            k = end + 1
        else:
            k += 1
    return out


def read_spans(pdf_path: Path) -> list[Span]:
    """Read every non-empty text span of the PDF, with its position and font."""
    spans: list[Span] = []
    with pymupdf.open(pdf_path) as doc:
        for page in doc:
            for block in page.get_text("rawdict")["blocks"]:
                for line in block.get("lines", []):
                    for s in line["spans"]:
                        raw = [(c["c"], c["bbox"][0], c["bbox"][2]) for c in s["chars"]]
                        if ARABIC_LETTER.search("".join(c for c, _, _ in raw)):
                            chars = reading_order(raw)
                        else:
                            chars = [(c, x1 - x0) for c, x0, x1 in raw]
                        text = fix_ligatures(chars)
                        if not text.strip():
                            continue
                        spans.append(
                            Span(
                                page=page.number + 1,
                                x0=s["bbox"][0],
                                x1=s["bbox"][2],
                                baseline=s["origin"][1],
                                size=round(s["size"], 1),
                                bold=bool(s["flags"] & 16),
                                text=text,
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
        rtl = is_rtl("".join(s.text for s in group))
        group.sort(key=lambda s: -s.x1 if rtl else s.x0)  # reading order
        text = group[0].text
        for prev, cur in zip(group, group[1:], strict=False):
            gap = prev.x0 - cur.x1 if rtl else cur.x0 - prev.x1
            needs_space = gap > WORD_GAP
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
