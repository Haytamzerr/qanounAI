"""Arabic-specific repairs: ligature order, reading order, article numbering.

Each test reproduces, character by character, a case measured in the real Law 09-08 PDF.
"""

import pytest

from qanoun.ingestion.parse_law import article_number
from qanoun.ingestion.pdf_lines import Span, fix_ligatures, group_into_lines, reading_order


def chars_of(text: str, width: float = 4.0) -> list[tuple[str, float]]:
    return [(c, width) for c in text]


def test_swapped_lam_alef_hamza_is_repaired():
    # "الأولى" is read as ا + أ(zero width) + ل + ولى
    chars = [("ا", 3.5), ("أ", 0.0), ("ل", 7.7), ("و", 7.2), ("ل", 3.7), ("ى", 8.8)]
    assert fix_ligatures(chars) == "الأولى"


@pytest.mark.parametrize(
    ("read_as", "expected"),
    [
        ("أال", "ألا"),  # ألا: plain lam-alef
        ("لإلنسان", "للإنسان"),  # لإ
        ("ألجل", "لأجل"),  # لأ at the start of a word
        ("آلية", "لآية"),  # لآ (made-up word, the mechanism is what matters)
    ],
)
def test_every_lam_alef_variant(read_as, expected):
    # The first alef-variant directly before a lam is the zero-width one
    chars, marked = [], False
    for i, c in enumerate(read_as):
        is_ligature_alef = (
            not marked and c in "اأإآ" and i + 1 < len(read_as) and read_as[i + 1] == "ل"
        )
        chars.append((c, 0.0 if is_ligature_alef else 4.0))
        marked |= is_ligature_alef
    assert fix_ligatures(chars) == expected


def test_real_definite_article_is_not_touched():
    # "المعلوميات": the alef of "ال" has a normal width, so nothing moves
    assert fix_ligatures(chars_of("المعلوميات")) == "المعلوميات"


def test_correct_lam_alef_is_not_touched():
    # Sometimes the zero-width alef already follows its lam: "لا؛" must stay as it is
    assert fix_ligatures([("ل", 6.0), ("ا", 0.0), ("؛", 3.0)]) == "لا؛"


@pytest.mark.parametrize(
    ("read_as", "expected"),
    [
        ([("ه", 0.0), ("ل", 0.0), ("ل", 9.0)], "لله"),
        ([("ه", 0), ("ل", 0), ("ل", 0), ("ا", 9)], "الله"),
    ],
)
def test_allah_ligature_is_repaired(read_as, expected):
    assert fix_ligatures(read_as) == expected


def test_reading_order_moves_space_and_period_to_their_real_place():
    # ".الخاصة " was extracted with the period first, although it sits at the far left
    raw = [(".", 429.7, 433.7), ("ا", 521.3, 524.6), ("ل", 517.9, 521.2), ("ة", 486.3, 492.3)]
    assert "".join(c for c, _ in reading_order(raw)) == "الة."


def test_reading_order_keeps_numbers_left_to_right():
    # "رقم 09.08" drawn right to left: Arabic letters on the right, the number on the left
    word = [("ر", 100, 108), ("ق", 92, 100), ("م", 86, 92), (" ", 82, 86)]
    number = [(c, 40 + 7 * i, 47 + 7 * i) for i, c in enumerate("09.08")]
    text = "".join(c for c, _ in reading_order(word + number))
    assert text == "رقم 09.08"


def test_arabic_line_is_assembled_right_to_left():
    spans = [
        Span(page=1, x0=257, x1=297, baseline=267, size=16, bold=True, text="الأولى"),
        Span(page=1, x0=301, x1=330, baseline=267, size=16, bold=True, text="المادة"),
    ]
    [line] = group_into_lines(spans, min_size=15.7)
    assert line.text == "المادة الأولى"


@pytest.mark.parametrize(
    ("heading", "expected"),
    [
        ("المادة الأولى", "1"),
        ("المادة 2", "2"),
        ("المادة2", "2"),
        ("المادة 25 المكررة", "25 bis"),
        ("الحق في الولوج", None),
    ],
)
def test_arabic_article_numbers(heading, expected):
    assert article_number(heading, "ar") == expected
