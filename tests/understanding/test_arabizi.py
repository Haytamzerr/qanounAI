import pytest

from qanoun.understanding.arabizi import transliterate, transliterate_word


@pytest.mark.parametrize(
    ("word", "arabic"),
    [
        ("3ndi", "عندي"),  # 3 = ع
        ("l7e9", "الحق"),  # glued article, 7 = ح, 9 = ق, short e dropped
        ("lkhedma", "الخدمة"),  # kh = خ, final a = ة
        ("nraj3ha", "نراجعها"),  # "-ha" (her) stays ها
        ("chhal", "شحال"),  # common word: settled spelling
        ("internet", "انترنت"),  # initial vowel
        ("préavis", "préavis"),  # French word: kept
        ("d'essai", "d'essai"),
        ("2026", "2026"),
    ],
)
def test_words(word, arabic):
    assert transliterate_word(word) == arabic


def test_sentence_keeps_punctuation():
    assert transliterate("wach 3ndi l7e9?") == "واش عندي الحق ?"
