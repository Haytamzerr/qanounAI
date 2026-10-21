"""Legal calculators: every figure comes from an article, every step is shown (decision 83).

A language model is bad at arithmetic and may "remember" a rate that changed. Here the rates are
read once from the official articles and written as constants next to the article that sets
them; the arithmetic is plain Python, tested, and returned step by step so the person (and the
interface) can see how the number was reached. The interface formats the steps in its language.

    dismissal_indemnity     Labour Code arts. 52, 53, 55, 58, 184
    abusive_dismissal       Labour Code art. 41 (damages, capped at 36 months)
    annual_leave            Labour Code arts. 231, 232
    rent_increase           Law 67.12 arts. 32–34
"""

from dataclasses import dataclass, field

LABOUR = "loi-65-99-ar-art-"
RENT = "loi-67-12-ar-art-"

# Labour Code art. 184: normal working time, used to turn a monthly wage into an hourly one
HOURS_PER_YEAR = {"non_agricultural": 2288, "agricultural": 2496}
# Labour Code art. 53: hours of wage per year of service, by band of seniority (years from, to)
INDEMNITY_BANDS = [(0, 5, 96), (5, 10, 144), (10, 15, 192), (15, None, 240)]
MIN_MONTHS_FOR_INDEMNITY = 6  # art. 52
REPRESENTATIVE_RAISE = 1.0  # art. 58: +100 % for staff and union representatives
DAMAGES_MONTHS_PER_YEAR = 1.5  # art. 41
DAMAGES_CAP_MONTHS = 36  # art. 41
LEAVE_DAYS_PER_MONTH = 1.5  # art. 231
LEAVE_DAYS_PER_MONTH_UNDER_18 = 2.0  # art. 231
LEAVE_BONUS_PER_5_YEARS = 1.5  # art. 232
LEAVE_CAP_DAYS = 30  # art. 232
MIN_MONTHS_FOR_LEAVE = 6  # art. 231
RENT_MAX_INCREASE = {"housing": 0.08, "professional": 0.10}  # Law 67.12 art. 34
RENT_YEARS_BETWEEN_INCREASES = 3  # Law 67.12 arts. 32, 33


class CalculationError(ValueError):
    """An input that makes no sense (negative wage, 200 years of service…)."""


@dataclass
class Step:
    key: str  # what the interface writes, in its language ("band", "hourly_wage"…)
    value: float
    detail: dict = field(default_factory=dict)  # numbers the sentence needs (years, rate…)


@dataclass
class Result:
    tool: str
    value: float  # the headline figure
    unit: str  # "MAD", "days", "months"…
    steps: list[Step]
    articles: list[str]  # ids of the articles the figures come from
    notes: list[str] = field(default_factory=list)  # keys of caveats the interface explains
    eligible: bool = True


def _check(**values: float) -> None:
    for name, value in values.items():
        if value is None or value < 0 or value != value:  # negative or NaN
            raise CalculationError(f"{name} must be a positive number")
    if values.get("years", 0) > 60:
        raise CalculationError("years of service must be at most 60")


def dismissal_indemnity(
    years: float,
    monthly_wage: float,
    *,
    agricultural: bool = False,
    representative: bool = False,
) -> Result:
    """Indemnity for dismissal (indefinite contract): hours of wage per year, by seniority band.

    The part of a year left over is counted in proportion ("each year or part of a year",
    art. 53); a court may count it differently, which a note says.
    """
    _check(years=years, monthly_wage=monthly_wage)
    sector = "agricultural" if agricultural else "non_agricultural"
    hourly = monthly_wage * 12 / HOURS_PER_YEAR[sector]
    steps = [
        Step("hourly_wage", round(hourly, 2), {"hours_per_year": HOURS_PER_YEAR[sector]}),
    ]
    articles = [f"{LABOUR}52", f"{LABOUR}53", f"{LABOUR}55", f"{LABOUR}184"]
    if years * 12 < MIN_MONTHS_FOR_INDEMNITY:
        return Result(
            "dismissal_indemnity", 0, "MAD", steps, articles, ["under_six_months"], eligible=False
        )
    hours = 0.0
    for start, end, per_year in INDEMNITY_BANDS:
        in_band = max(0.0, min(years, end if end is not None else years) - start)
        if in_band:
            hours += in_band * per_year
            steps.append(
                Step("band", round(in_band * per_year * hourly, 2),
                     {"from": start, "to": end, "years": round(in_band, 2), "hours": per_year})
            )  # fmt: skip
    total = hours * hourly
    if representative:
        steps.append(Step("representative", round(total * REPRESENTATIVE_RAISE, 2)))
        total *= 1 + REPRESENTATIVE_RAISE
        articles.append(f"{LABOUR}58")
    notes = ["average_52_weeks", "part_year", "minimum_wage"]
    return Result("dismissal_indemnity", round(total, 2), "MAD", steps, articles, notes)


def abusive_dismissal(years: float, monthly_wage: float) -> Result:
    """Damages a court may award for abusive dismissal: 1.5 month per year, at most 36 months.

    This is what the law caps, not what a court will grant: the court decides (art. 41).
    """
    _check(years=years, monthly_wage=monthly_wage)
    months = min(years * DAMAGES_MONTHS_PER_YEAR, DAMAGES_CAP_MONTHS)
    steps = [
        Step("months", round(months, 2), {"years": years, "per_year": DAMAGES_MONTHS_PER_YEAR})
    ]
    notes = ["court_decides", "part_year"]
    if years * DAMAGES_MONTHS_PER_YEAR > DAMAGES_CAP_MONTHS:
        steps.append(Step("cap", DAMAGES_CAP_MONTHS))
        notes.append("capped")
    total = months * monthly_wage
    return Result(
        "abusive_dismissal", round(total, 2), "MAD", steps, [f"{LABOUR}41", f"{LABOUR}59"], notes
    )


def annual_leave(
    months_worked: float, years_of_service: float, *, under_18: bool = False
) -> Result:
    """Paid annual leave earned: 1.5 day per month (2 under 18), + 1.5 per 5 full years, max 30."""
    _check(months_worked=months_worked, years=years_of_service)
    articles = [f"{LABOUR}231", f"{LABOUR}232"]
    if months_worked < MIN_MONTHS_FOR_LEAVE and years_of_service * 12 < MIN_MONTHS_FOR_LEAVE:
        return Result("annual_leave", 0, "days", [], articles, ["under_six_months"], eligible=False)
    per_month = LEAVE_DAYS_PER_MONTH_UNDER_18 if under_18 else LEAVE_DAYS_PER_MONTH
    base = min(months_worked, 12) * per_month
    bonus = int(years_of_service // 5) * LEAVE_BONUS_PER_5_YEARS
    steps = [Step("per_month", base, {"months": min(months_worked, 12), "per_month": per_month})]
    if bonus:
        steps.append(Step("seniority", bonus, {"periods": int(years_of_service // 5)}))
    total = base + bonus
    notes = ["working_days", "better_contract"]
    if total > LEAVE_CAP_DAYS:
        steps.append(Step("cap", LEAVE_CAP_DAYS))
        total = LEAVE_CAP_DAYS
        notes.append("capped")
    return Result("annual_leave", total, "days", steps, articles, notes)


def rent_increase(
    monthly_rent: float, years_since_last_revision: float, use: str = "housing"
) -> Result:
    """The highest rent after a revision: +8 % for housing, +10 % for professional premises,
    and only once three years have passed since the contract or the last revision."""
    _check(monthly_rent=monthly_rent, years=years_since_last_revision)
    if use not in RENT_MAX_INCREASE:
        raise CalculationError("use must be 'housing' or 'professional'")
    rate = RENT_MAX_INCREASE[use]
    articles = [f"{RENT}32", f"{RENT}33", f"{RENT}34"]
    if years_since_last_revision < RENT_YEARS_BETWEEN_INCREASES:
        wait = RENT_YEARS_BETWEEN_INCREASES - years_since_last_revision
        steps = [Step("too_early", round(wait, 2), {"years": RENT_YEARS_BETWEEN_INCREASES})]
        return Result("rent_increase", monthly_rent, "MAD", steps, articles, ["too_early"], False)
    increase = monthly_rent * rate
    steps = [Step("increase", round(increase, 2), {"rate": rate * 100, "use": use})]
    return Result(
        "rent_increase", round(monthly_rent + increase, 2), "MAD", steps, articles, ["agreement"]
    )


TOOLS = {
    "dismissal_indemnity": dismissal_indemnity,
    "abusive_dismissal": abusive_dismissal,
    "annual_leave": annual_leave,
    "rent_increase": rent_increase,
}


def calculate(tool: str, inputs: dict) -> Result:
    """Run one calculator by name with the inputs the interface sent."""
    if tool not in TOOLS:
        raise CalculationError(f"unknown calculator: {tool}")
    try:
        return TOOLS[tool](**inputs)
    except TypeError as error:  # a missing or unknown input
        raise CalculationError(str(error)) from error
