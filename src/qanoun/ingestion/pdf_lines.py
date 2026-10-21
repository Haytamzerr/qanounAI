"""Turn a PDF into visual lines that keep their font information.

Why not just `page.get_text()`? Because plain text loses what tells us the structure of a law:
the font size and weight. In the Adala PDFs, chapters, article headings, body text and
footnotes each use a different font size. We keep that information on every line.

How the PDF cuts text into pieces ("spans") is unreliable, especially in Arabic: a word can be
split across spans, and a heading drawn twice for a shadow effect produces two sets of spans
that interleave. So we work at the level of characters and their positions:

1. read every character with its position and font (`read_spans`), dropping shadow copies
   (`_ShadowFilter`);
2. drop text smaller than the body (footnotes, footnote markers), keeping ordinals ("2e");
3. gather all characters on the same baseline into one line, and order the whole line by
   position: right to left for Arabic, keeping numbers left to right (`reading_order`);
4. remove "spaces" drawn on top of letters (`drop_fake_spaces`), add a space wherever there
   is a visible gap, and repair Arabic ligatures read backwards (`fix_ligatures`).
"""

import re
from dataclasses import dataclass
from pathlib import Path

import pymupdf

Char = tuple[str, float, float]  # (character, x0, x1)


@dataclass(frozen=True)
class Span:
    """A piece of text as the PDF stores it, with the position of each character."""

    page: int
    x0: float
    x1: float
    baseline: float
    size: float
    bold: bool
    text: str
    chars: tuple[Char, ...] = ()

    def positioned_chars(self) -> list[Char]:
        """The span's characters with positions; spread evenly if the PDF gave none."""
        if self.chars:
            return list(self.chars)
        n = max(len(self.text), 1)
        step = (self.x1 - self.x0) / n
        rtl = is_rtl(self.text)
        out = []
        for i, c in enumerate(self.text):
            left = self.x1 - (i + 1) * step if rtl else self.x0 + i * step
            out.append((c, left, left + step))
        return out


@dataclass(frozen=True)
class Line:
    """A visual line on a page."""

    page: int
    y: float
    size: float
    bold: bool
    text: str


BASELINE_TOLERANCE = 2.0  # points: characters this close vertically are on the same line
WORD_GAP = 1.5  # points: a horizontal gap bigger than this is a space between words

ARABIC_LETTER = re.compile(r"[؀-ۿ]")
LATIN_LETTER = re.compile(r"[A-Za-zÀ-ÿ]")


def is_rtl(text: str) -> bool:
    """A line is read right to left when it has more Arabic than Latin letters."""
    return len(ARABIC_LETTER.findall(text)) > len(LATIN_LETTER.findall(text))


# --- Arabic ligatures --------------------------------------------------------------------

ALEFS = set("اأإآ")
ARABIC_BASE_LETTER = re.compile(r"[\u0621-\u064A]")  # letters only: no harakat, no digits
ZERO_WIDTH = 0.05  # points: a glyph narrower than this is drawn inside its neighbour


def fix_ligatures(chars: list[tuple[str, float]]) -> str:
    """Rebuild text from (character, glyph width) pairs, repairing Arabic ligatures.

    Word draws lam-alef (لا لأ لإ لآ) and Allah (ﷲ) as one glyph. When the PDF is read back,
    that glyph's letters come out in reverse order: "الأولى" is read as "األولى", "لله" as "هلل".
    The tell-tale sign is that every letter of the ligature except the last has zero width.
    So: a zero-width alef followed by lam, or a zero-width run starting with ه, is reversed
    with the letter that follows it. A real alef (e.g. the article "ال") has a normal width and
    is never touched, and a zero-width alef that already follows its lam is left as it is.

    Other software draws other pairs as one glyph: LibreOffice writes "تر" as ر (zero width)
    then ت, so "المكتري" was read "المكرتي" in a contract the owner tested. Any other zero-width
    Arabic letter followed by a letter with a width is therefore swapped with it too (lam and
    alef excepted: they keep the rules above). Vowel marks (harakat) are never moved. Measured
    on 30,858 lines of 65 laws: the five curated laws are unchanged, two Adala lines are
    repaired ("املتعلق" → "المتعلق", "امللكي" → "الملكي"), nothing else moves.
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
        nxt = chars[i + 1] if i + 1 < len(chars) else None
        if (
            is_zero
            and ARABIC_BASE_LETTER.fullmatch(char)
            and char not in ALEFS
            and char != "ل"  # lam belongs to lam-alef and Allah, which have their own rules
            and nxt is not None
            and nxt[1] >= ZERO_WIDTH
            and ARABIC_BASE_LETTER.fullmatch(nxt[0])
        ):
            out += [nxt[0], char]
            i += 2
            continue
        out.append(char)
        i += 1
    return "".join(out)


# --- Reading order -----------------------------------------------------------------------

MAX_SPACE_WIDTH = 4.5  # points: some PDFs report spaces wider than whole words
OVERLAP_MARGIN = 1.0  # points: how deep inside a letter a space must start to be fake
LTR_CHAR = re.compile(r"[0-9A-Za-zÀ-ÿ]")
NUMBER_JOINER = set(".,/-:")  # kept inside a left-to-right run when between two LTR chars


def _right_edge(char: str, x0: float, x1: float) -> float:
    """Where a character really ends. Spaces are placed by where they start."""
    return min(x1, x0 + MAX_SPACE_WIDTH) if char.isspace() else x1


def drop_fake_spaces(chars: list[Char]) -> list[Char]:
    """Remove space characters drawn on top of letters.

    Some PDFs contain "spaces" whose box starts inside a letter, e.g. a space from x=295.9 to
    x=311.4 right over "د" and "م" in "المادة". They are layout artefacts, not word breaks:
    kept, they split words ("الم اد ة"). A real space starts where the previous letter ends.
    """
    letters = [(x0, x1) for c, x0, x1 in chars if not c.isspace()]
    return [
        (c, x0, x1)
        for c, x0, x1 in chars
        if not (c.isspace() and any(a - 0.5 <= x0 < b - OVERLAP_MARGIN for a, b in letters))
    ]


def _ltr_runs(out: list[Char]) -> list[tuple[int, int]]:
    """(start, end) of each run of digits / Latin letters, joiners included when inside."""

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

    runs, k = [], 0
    while k < len(out):
        if is_ltr(k):
            end = k
            while end + 1 < len(out) and is_ltr(end + 1):
                end += 1
            runs.append((k, end))
            k = end + 1
        else:
            k += 1
    return runs


def reading_order(chars: list[Char]) -> list[Char]:
    """Put Arabic characters in reading order using their positions.

    The order in which the PDF lists characters is unreliable for Arabic (spaces, punctuation
    and quotes come out misplaced: ".الخاصة" instead of "الخاصة."), but their *positions* are
    right. So we read from right to left by position, then flip runs of digits and Latin
    letters (e.g. "09.08", "CNDP") back to left to right. Ties keep the PDF order, which the
    ligature repair relies on.
    """
    edges = [_right_edge(c, x0, x1) for c, x0, x1 in chars]
    out = [chars[i] for i in sorted(range(len(chars)), key=lambda i: (-edges[i], i))]
    for start, end in _ltr_runs(out):
        out[start : end + 1] = reversed(out[start : end + 1])
    return out


def _line_text(chars: list[Char]) -> str:
    """Order a line's characters, add spaces at visible gaps, repair ligatures."""
    chars = drop_fake_spaces(chars)
    rtl = is_rtl("".join(c for c, _, _ in chars))
    if rtl:
        ordered = reading_order(chars)
        groups = [[i] for i in range(len(ordered))]
        for start, end in reversed(_ltr_runs(ordered)):  # a number is one unit for spacing
            groups[start : end + 1] = [list(range(start, end + 1))]
    else:
        ordered = sorted(chars, key=lambda c: c[1])
        groups = [[i] for i in range(len(ordered))]

    # A zero-width glyph (hidden part of a ligature) is measured with the letter it sits in:
    # the next one when it is a swapped alef before its lam, otherwise the previous one.
    merged: list[list[int]] = []
    carry: list[int] = []
    for k, g in enumerate(groups):
        zero = all(ordered[i][2] - ordered[i][1] < ZERO_WIDTH for i in g)
        next_is_lam = k + 1 < len(groups) and ordered[groups[k + 1][0]][0] == "ل"
        if zero and ordered[g[0]][0] in ALEFS and next_is_lam:
            carry += g
        elif zero and merged:
            merged[-1] += g
        else:
            merged.append(carry + g)
            carry = []
    if carry:
        merged.append(carry)
    groups = merged

    pieces: list[tuple[str, float]] = []
    for prev, cur in zip([None, *groups], groups, strict=False):
        if prev is not None:
            p_x0 = min(ordered[i][1] for i in prev)
            p_x1 = max(_right_edge(*ordered[i]) for i in prev)
            c_x0 = min(ordered[i][1] for i in cur)
            c_x1 = max(_right_edge(*ordered[i]) for i in cur)
            gap = max(p_x0 - c_x1, c_x0 - p_x1) if rtl else c_x0 - p_x1
            last, first = ordered[prev[-1]][0], ordered[cur[0]][0]
            if gap > WORD_GAP and not last.isspace() and not first.isspace():
                pieces.append((" ", 4.0))
        pieces += [(ordered[i][0], ordered[i][2] - ordered[i][1]) for i in cur]
    return fix_ligatures(pieces)


# --- Reading the PDF ---------------------------------------------------------------------

SHADOW_OFFSET = 1.5  # points: a copy of a glyph this close is a shadow, not new text


class _ShadowFilter:
    """Remembers the glyphs already kept on a page, to drop shadow copies of them.

    Some headings are drawn twice, the second copy shifted by about 0.8 points (a Word shadow
    or outline effect). Read naively, the two copies interleave: "البابالباب الأول: لأول".
    A glyph is a shadow when the same character, in the same font and with the same width,
    was already kept less than `SHADOW_OFFSET` points away, in another span. Comparing widths
    matters: the hidden zero-width alef of a ligature must not be mistaken for a shadow of a
    real alef drawn at the same spot ("الاتفاقيات" would lose a letter).
    """

    def __init__(self) -> None:
        self._grid: dict[tuple, list[tuple[float, float, float, int]]] = {}

    def check_and_keep(self, char: str, x0: float, x1: float, y: float, font, span: int) -> bool:
        """Return True if the glyph is a shadow; otherwise remember it and return False."""
        width = x1 - x0
        for gx in (int(x0) - 1, int(x0), int(x0) + 1):
            for gy in (int(y) - 1, int(y), int(y) + 1):
                for kx, kw, ky, kspan in self._grid.get((char, font, gx, gy), []):
                    if (
                        kspan != span
                        and abs(kx - x0) <= SHADOW_OFFSET
                        and abs(ky - y) <= SHADOW_OFFSET
                        and abs(kw - width) <= 0.5
                    ):
                        return True
        self._grid.setdefault((char, font, int(x0), int(y)), []).append((x0, width, y, span))
        return False


# The default "rawdict" extraction also decodes every image of the page (each Adala page has a
# logo), which made reading 50 times slower and produced exactly the same text.
TEXT_FLAGS = pymupdf.TEXTFLAGS_RAWDICT & ~pymupdf.TEXT_PRESERVE_IMAGES


def read_spans(pdf_path: Path) -> list[Span]:
    """Read every text span of the PDF with its font and the position of each character."""
    spans: list[Span] = []
    with pymupdf.open(pdf_path) as doc:
        for page in doc:
            shadows = _ShadowFilter()
            span_id = 0
            for block in page.get_text("rawdict", flags=TEXT_FLAGS)["blocks"]:
                for line in block.get("lines", []):
                    for s in line["spans"]:
                        span_id += 1
                        size, bold, y = round(s["size"], 1), bool(s["flags"] & 16), s["origin"][1]
                        chars = tuple(
                            (c["c"], c["bbox"][0], c["bbox"][2])
                            for c in s["chars"]
                            if not shadows.check_and_keep(
                                c["c"], c["bbox"][0], c["bbox"][2], y, (size, bold), span_id
                            )
                        )
                        if not any(not c.isspace() for c, _, _ in chars):
                            continue
                        spans.append(
                            Span(
                                page=page.number + 1,
                                x0=min(x0 for _, x0, _ in chars),
                                x1=max(_right_edge(*c) for c in chars),
                                baseline=y,
                                size=size,
                                bold=bold,
                                text="".join(c for c, _, _ in chars),
                                chars=chars,
                            )
                        )
    return spans


# --- Footnotes and ordinals --------------------------------------------------------------

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


# --- Lines -------------------------------------------------------------------------------


def group_into_lines(spans: list[Span], min_size: float) -> list[Line]:
    """Drop text smaller than `min_size`, then build one line per baseline."""
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
        chars = [c for span in group for c in span.positioned_chars()]
        # The line's font is the font of most of its text (headings can hold a stray piece)
        main = max(group, key=lambda s: len(s.text.strip()))
        lines.append(
            Line(
                page=main.page,
                y=group[0].baseline,
                size=main.size,
                bold=main.bold,
                text=_line_text(chars),
            )
        )
    return lines


def read_lines(pdf_path: Path, min_size: float) -> list[Line]:
    return group_into_lines(read_spans(pdf_path), min_size=min_size)
