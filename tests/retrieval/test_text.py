"""Normalisation must make the same word look the same, without inventing matches."""

import pytest

from qanoun.retrieval.text import normalize, strip_prefix, tokenize


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("الْمَادَّةُ", "الماده"),  # vowel marks removed, ة -> ه
        ("الـمادة", "الماده"),  # tatweel removed
        ("أجير إجازة آجال", "اجير اجازه اجال"),  # alef variants unified
        ("الأولى", "الاولي"),  # ى -> ي
        ("Période d'ESSAI", "periode d'essai"),  # French accents and case
    ],
)
def test_normalize(raw, expected):
    assert normalize(raw) == expected


@pytest.mark.parametrize(
    ("token", "expected"),
    [("والاجير", "اجير"), ("للمستهلك", "مستهلك"), ("بالعقد", "عقد"), ("ال", "ال"), ("الي", "الي")],
)
def test_strip_prefix_keeps_a_real_stem(token, expected):
    assert strip_prefix(token) == expected


def test_tokenize_arabic_question():
    assert tokenize("ما هو سن الرشد القانوني؟") == ["سن", "رشد", "قانوني"]


def test_tokenize_french_question_keeps_numbers():
    assert tokenize("Quel est l'âge légal du mariage, 18 ans ?") == [
        "age",
        "legal",
        "mariage",
        "18",
        "ans",
    ]
