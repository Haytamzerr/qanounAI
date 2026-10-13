"""Deep heading hierarchies, mis-formatted headings, and line-level repairs.

Each case reproduces something measured in the real Labour Code PDF (Law 65.99).
"""

from qanoun.ingestion.models import Source
from qanoun.ingestion.parse_law import LAYOUTS, parse_lines, rescue_misformatted_headings
from qanoun.ingestion.pdf_lines import Line, Span, _ShadowFilter, drop_fake_spaces, group_into_lines

CODE = LAYOUTS["adala-code-ar"]
SOURCE = Source(
    file="code.pdf",
    law_number="65-99",
    law_title="مدونة الشغل",
    language="ar",
    layout="adala-code-ar",
    source_url="https://example.org/code.pdf",
    downloaded_on="2026-10-13",
    is_official_version=True,
)
BODY = "نص المادة الذي يكفي طوله لاجتياز اختبار الطول الأدنى بسهولة تامة."


def line(text: str, size: float, bold: bool = False, page: int = 1, y: float = 100.0) -> Line:
    return Line(page=page, y=y, size=size, bold=bold, text=text)


def test_five_heading_levels_build_the_hierarchy_and_reset_lower_levels():
    lines = [
        line("ديباجة", 21.8, True, y=50),  # preamble heading at book size: skipped
        line("الكتاب الأول: الاتفاقيات", 21.8, True, y=60),
        line("القسم الأول: عقد الشغل", 21.0, True, y=80),
        line("الباب الخامس: توقف عقد الشغل", 20.3, True, y=100),
        line("الفرع الرابع: التعويض عن الفصل", 18.8, True, y=120),
        line("القسم الفرعي الأول: اللوائح", 18.0, True, y=140),
        line("المادة 53", 15.8, True, y=160),
        line(BODY, 15.8, y=180),
        line("الباب السادس: الوكيل المتجول", 20.3, True, page=2, y=60),  # a new chapter
        line("المادة 79", 15.8, True, page=2, y=80),
        line(BODY, 15.8, page=2, y=100),
    ]
    first, second = parse_lines(lines, SOURCE, CODE)
    assert first.hierarchy == [
        "الكتاب الأول: الاتفاقيات",
        "القسم الأول: عقد الشغل",
        "الباب الخامس: توقف عقد الشغل",
        "الفرع الرابع: التعويض عن الفصل",
        "القسم الفرعي الأول: اللوائح",
    ]
    assert second.hierarchy == [
        "الكتاب الأول: الاتفاقيات",
        "القسم الأول: عقد الشغل",
        "الباب السادس: الوكيل المتجول",
    ], "a new chapter closes the section and sub-section above it"


def test_wrapped_heading_is_joined():
    lines = [
        line("الكتاب الأول: الاتفاقيات", 21.8, True, y=60),
        line("الباب السابع: المجلس الأعلى لإنعاش التشغيل والمجالس الجهوية", 20.3, True, y=80),
        line("والإقليمية لإنعاش التشغيل", 20.3, True, y=100),
        line("المادة 522", 15.8, True, y=120),
        line(BODY, 15.8, y=140),
    ]
    [article] = parse_lines(lines, SOURCE, CODE)
    assert article.hierarchy[-1].endswith("والمجالس الجهوية والإقليمية لإنعاش التشغيل")


def test_heading_printed_in_footnote_font_is_rescued():
    all_lines = [
        line("المادة 517", 12.8, y=575),  # the source PDF's formatting error
        line("يجب أن يكون عقد الشغل الخاص بالأجانب، مطابقا للنموذج", 15.8, y=599),
    ]
    [rescued] = rescue_misformatted_headings(all_lines, CODE, "ar")
    assert rescued.bold and rescued.size == CODE.article_size


def test_footnotes_quoting_other_articles_are_not_rescued():
    all_lines = [
        line("المادة 34:", 12.8, True, y=700),  # quoted article, ends with a colon
        line("نص المرسوم", 12.8, y=715),
        line("المادة 35", 12.8, True, y=730),  # no colon, but followed only by the page number
        line("- 140 -", 15.8, y=799),
    ]
    assert rescue_misformatted_headings(all_lines, CODE, "ar") == []


def test_shadow_copy_is_dropped_but_ligature_alef_is_kept():
    shadows = _ShadowFilter()
    font = (20.3, True)
    assert not shadows.check_and_keep("ب", 365.7, 371.2, 364.8, font, span=1)
    assert shadows.check_and_keep("ب", 366.4, 371.9, 365.6, font, span=2), "copy 0.8 pt away"
    assert not shadows.check_and_keep("ب", 366.4, 371.9, 365.6, font, span=1), "same span"
    assert not shadows.check_and_keep("ا", 293.6, 297.1, 300.0, font, span=3)
    assert not shadows.check_and_keep("ا", 293.6, 293.6, 300.0, font, span=4), (
        "a zero-width ligature alef is not the shadow of a full alef at the same spot"
    )


def test_fake_spaces_on_top_of_letters_are_removed():
    # From "المادة 8": two spaces start inside "د" and "م"; the real one sits between words
    chars = [
        ("د", 295.9, 301.3),
        (" ", 295.9, 311.4),
        ("م", 304.9, 311.4),
        (" ", 304.9, 318.8),
        (" ", 286.9, 290.8),
        ("8", 278.6, 286.5),
    ]
    assert drop_fake_spaces(chars) == [("د", 295.9, 301.3), ("م", 304.9, 311.4), *chars[4:]]


def _arabic_line(chars) -> str:
    span = Span(1, 0, 1000, 100.0, 16.0, False, "".join(c for c, *_ in chars), tuple(chars))
    [result] = group_into_lines([span], min_size=15.7)
    return result.text


def test_no_space_inside_a_correctly_ordered_lam_alef():
    # "لا؛": the zero-width alef already follows its lam and must not create a gap
    assert _arabic_line([("ل", 100, 106), ("ا", 100, 100), ("؛", 96.5, 99.5)]) == "لا؛"


def test_space_kept_before_a_word_starting_with_a_swapped_ligature():
    # "أ) لاحترام": the swapped zero-width alef belongs with the lam after it
    chars = [("أ", 200, 204), (")", 196, 199.5), ("ا", 190, 190), ("ل", 182, 190), ("ح", 176, 182)]
    assert _arabic_line(chars) == "أ) لاح"


FAMILY = LAYOUTS["adala-family-ar"]


def test_chapter_and_section_sharing_a_font_are_told_apart_by_their_word():
    lines = [
        line("باب تمهيدي: أحكام عامة", 18.0, True, y=40),  # preliminary chapter, without "ال"
        line("المادة 1", 16.0, True, y=60),
        line(BODY, 16.0, y=90),
        line("الكتاب الأول: الزواج", 22.0, True, y=120),
        line("الباب الأول: الزواج الصحيح وآثاره", 18.0, True, y=150),
        line("الفرع الأول: الزوجان", 18.0, True, y=180),  # same font as the chapter
        line("المادة 51", 16.0, True, y=210),
        line(BODY, 16.0, y=240),
    ]
    first, second = parse_lines(lines, SOURCE, FAMILY)
    assert first.hierarchy == ["باب تمهيدي: أحكام عامة"]
    assert second.hierarchy == [
        "الكتاب الأول: الزواج",
        "الباب الأول: الزواج الصحيح وآثاره",
        "الفرع الأول: الزوجان",
    ]
