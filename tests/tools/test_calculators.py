"""Worked examples, checked by hand against the articles."""

import pytest

from qanoun.tools.calculators import CalculationError, calculate


def test_dismissal_indemnity_after_seven_years():
    # 5,000 MAD a month → 5000 × 12 / 2288 = 26.22 MAD an hour (art. 184)
    # 5 years × 96 h + 2 years × 144 h = 768 h (art. 53) → 768 × 26.22 = 20,139.86 MAD
    r = calculate("dismissal_indemnity", {"years": 7, "monthly_wage": 5000})
    assert r.value == pytest.approx(20139.86, abs=0.01) and r.eligible
    assert [s.detail.get("hours") for s in r.steps if s.key == "band"] == [96, 144]
    assert "loi-65-99-ar-art-53" in r.articles


def test_every_band_and_the_representative_raise():
    r = calculate("dismissal_indemnity", {"years": 20, "monthly_wage": 2288 / 12})  # 1 MAD/hour
    assert r.value == pytest.approx(5 * 96 + 5 * 144 + 5 * 192 + 5 * 240)
    doubled = calculate(
        "dismissal_indemnity", {"years": 20, "monthly_wage": 2288 / 12, "representative": True}
    )
    assert doubled.value == pytest.approx(2 * r.value) and "loi-65-99-ar-art-58" in doubled.articles


def test_no_indemnity_before_six_months():
    r = calculate("dismissal_indemnity", {"years": 0.4, "monthly_wage": 4000})
    assert not r.eligible and r.value == 0 and "under_six_months" in r.notes


def test_abusive_dismissal_damages_and_cap():
    assert calculate("abusive_dismissal", {"years": 7, "monthly_wage": 5000}).value == 52500
    capped = calculate("abusive_dismissal", {"years": 30, "monthly_wage": 5000})
    assert capped.value == 36 * 5000 and "capped" in capped.notes


@pytest.mark.parametrize(
    ("months", "years", "under_18", "days"),
    [
        (12, 1, False, 18),
        (12, 1, True, 24),
        (12, 11, False, 21),
        (12, 40, False, 30),
        (12, 50, False, 30),
    ],
)
def test_annual_leave(months, years, under_18, days):
    r = calculate(
        "annual_leave", {"months_worked": months, "years_of_service": years, "under_18": under_18}
    )
    assert r.value == days


def test_rent_increase():
    assert (
        calculate("rent_increase", {"monthly_rent": 2000, "years_since_last_revision": 3}).value
        == 2160
    )
    shop = calculate(
        "rent_increase",
        {"monthly_rent": 2000, "years_since_last_revision": 4, "use": "professional"},
    )
    assert shop.value == 2200
    early = calculate("rent_increase", {"monthly_rent": 2000, "years_since_last_revision": 2})
    assert not early.eligible and early.value == 2000 and "too_early" in early.notes


@pytest.mark.parametrize(
    ("tool", "inputs"),
    [
        ("nope", {}),
        ("abusive_dismissal", {"years": -1, "monthly_wage": 10}),
        ("abusive_dismissal", {"years": 200, "monthly_wage": 10}),
        ("abusive_dismissal", {"years": 2}),
        ("rent_increase", {"monthly_rent": 10, "years_since_last_revision": 4, "use": "boat"}),
    ],
)
def test_bad_inputs_are_refused(tool, inputs):
    with pytest.raises(CalculationError):
        calculate(tool, inputs)
