"""Legal deadlines in an analysis, verified against the article before they are shown (82).

A deadline the person misses can cost them their right ("90 days to take a dismissal to court",
art. 65 of the Labour Code). The analysis model lists the deadlines it reads in the sources, with
the exact words of the article. Nothing is trusted:

1. the source number must be one of the sources given;
2. the quote must appear, word for word (after the usual normalisation), in that article;
3. the duration must be in the quote: its number in digits or in words ("تسعين", "quinze"),
   or a unit alone meaning one ("أجل شهر"), or an Arabic dual meaning two ("شهرين");
4. the unit must be one of days, months, years, hours;
5. no "and a half" in the quote: "شهر ونصف" was shown as "1 month" (owner's contract test).

A deadline that fails any check is dropped (and logged); the interface then turns the duration
into a date from the day the person gives, and a calendar reminder.
"""

import logging
import re
from collections.abc import Sequence
from dataclasses import asdict, dataclass

from qanoun.ingestion.models import Article
from qanoun.retrieval.text import normalize

log = logging.getLogger("qanoun.deadlines")

UNITS = {
    "days": ("يوم", "ايام", "أيام", "يوما", "jour", "jours"),
    "months": ("شهر", "اشهر", "أشهر", "شهور", "mois"),
    "years": ("سنة", "سنوات", "سنين", "عام", "اعوام", "an", "ans", "annee", "annees"),
    "hours": ("ساعة", "ساعات", "heure", "heures"),
}
DUALS = {"days": ("يومين", "يومان"), "months": ("شهرين", "شهران"), "years": ("سنتين", "سنتان"),
         "hours": ("ساعتين", "ساعتان")}  # fmt: skip
NUMBER_WORDS = {
    1: ("واحد", "واحدة", "un", "une"),
    2: ("اثنين", "اثنان", "deux"),
    3: ("ثلاثة", "ثلاث", "trois"),
    4: ("اربعة", "أربعة", "اربع", "أربع", "quatre"),
    5: ("خمسة", "خمس", "cinq"),
    6: ("ستة", "ست", "six"),
    7: ("سبعة", "سبع", "sept"),
    8: ("ثمانية", "ثماني", "ثمان", "huit"),
    9: ("تسعة", "تسع", "neuf"),
    10: ("عشرة", "عشر", "dix"),
    12: ("اثني عشر", "اثنا عشر", "douze"),
    15: ("خمسة عشر", "خمس عشرة", "quinze"),
    20: ("عشرين", "عشرون", "vingt"),
    30: ("ثلاثين", "ثلاثون", "trente"),
    45: ("خمسة واربعين", "خمسة وأربعين", "quarante-cinq"),
    60: ("ستين", "ستون", "soixante"),
    90: ("تسعين", "تسعون", "quatre-vingt-dix"),
}


@dataclass
class Deadline:
    what: str  # what must be done, in the answer's language
    amount: int
    unit: str  # "days", "months", "years" or "hours"
    from_event: str  # from when it runs ("the notice", "receiving the dismissal letter")
    quote: str  # the article's own words
    source: int  # 1-based number among the sources
    article_id: str

    def as_dict(self) -> dict:
        return asdict(self)


def _words(text: str) -> list[str]:
    return re.findall(r"[\w-]+", normalize(text))


def _has_unit(words: list[str], unit: str) -> bool:
    forms = {normalize(f) for f in UNITS[unit]}
    # Arabic glues prefixes: "بالأيام", "لمدة", "اشهر" — accept a unit form at the end of a word
    return any(w in forms or any(w.endswith(f) and len(f) > 2 for f in forms) for w in words)


HALF = re.compile(r"نصف|demi|moitie|half")  # "شهر ونصف" is 1.5 months: not a whole amount


def _has_amount(quote: str, amount: int, unit: str) -> bool:
    text = normalize(quote)
    if HALF.search(text):
        return False  # a duration "and a half" cannot be shown exactly as whole days or months
    if re.search(rf"(?<!\d){amount}(?!\d)", text):
        return True
    if any(normalize(w) in text for w in NUMBER_WORDS.get(amount, ())):
        return True
    if amount == 2 and any(normalize(d) in text for d in DUALS[unit]):
        return True
    return amount == 1  # "أجل شهر", "un mois": the unit alone means one


def verify(raw: Sequence[dict], sources: Sequence[Article]) -> list[Deadline]:
    """The deadlines the article really states; the others are dropped."""
    kept = []
    for item in raw[:6]:
        try:
            source, amount = int(item.get("source", 0)), int(item.get("amount", 0))
            unit = str(item.get("unit", "")).strip().lower()
            quote, what = str(item.get("quote", "")).strip(), str(item.get("what", "")).strip()
        except (TypeError, ValueError, AttributeError):
            continue
        reason = None
        if not 1 <= source <= len(sources):
            reason = f"source {source} is not among the {len(sources)} sources"
        elif unit not in UNITS or not 0 < amount <= 3650:
            reason = f"unusable duration {amount} {unit}"
        elif len(quote) < 6 or " ".join(_words(quote)) not in " ".join(
            _words(sources[source - 1].text)
        ):
            reason = "the quote is not in the article"
        elif not _has_unit(_words(quote), unit) or not _has_amount(quote, amount, unit):
            reason = f"{amount} {unit} is not what the quote says"
        if reason:
            log.info("deadline dropped (%s): %s", reason, what)
            continue
        kept.append(
            Deadline(what, amount, unit, str(item.get("from_event", "")).strip(), quote, source,
                     sources[source - 1].id)
        )  # fmt: skip
    return kept
