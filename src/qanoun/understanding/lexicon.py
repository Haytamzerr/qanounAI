"""An open Darija → legal-Arabic lexicon (data/lexicon/darija_legal.csv).

People say "tredouni mn lkhedma" ("they kicked me out of work"); the law says "الفصل من الشغل".
Each row maps everyday Darija, in Latin and Arabic letters, to the legal terms the law uses:

- `arabizi`: a regular expression over the lowercased Latin text. A word may start with a glued
  article or preposition (l, el, f, fl, b, w) and continue with any ending, so "khe?d[ea]?m"
  catches khedma, lkhedma, flkhdma and khdemt;
- `darija_ar`: Arabic-script spellings, separated by ";", found inside words after normalisation
  (so "طرد" catches طردوني and طردوك);
- `legal_ar`: the formal terms added to the search;
- `legal_fr`: the French equivalent, for display and for French questions later.
"""

import csv
import re
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from qanoun.config import PROJECT_ROOT
from qanoun.retrieval.text import normalize

LEXICON_PATH = PROJECT_ROOT / "data" / "lexicon" / "darija_legal.csv"
GLUED = r"(?<![a-z0-9])(?:el|l|fl|f|bl|b|wl|w)?"  # a word may start with these


@dataclass(frozen=True)
class Entry:
    domain: str
    arabizi: re.Pattern
    darija_ar: tuple[str, ...]  # normalised
    legal_ar: tuple[str, ...]
    legal_fr: str


@cache
def load_lexicon(path: Path = LEXICON_PATH) -> tuple[Entry, ...]:
    with path.open(encoding="utf-8") as f:
        return tuple(
            Entry(
                domain=row["domain"],
                arabizi=re.compile(GLUED + f"(?:{row['arabizi']})", re.IGNORECASE),
                darija_ar=tuple(normalize(w) for w in row["darija_ar"].split(";") if w),
                legal_ar=tuple(row["legal_ar"].split(";")),
                legal_fr=row["legal_fr"],
            )
            for row in csv.DictReader(f)
        )


GLUED_AR = ("وال", "فال", "بال", "ال", "كي", "كن", "تي", "و", "ف", "ب", "ل")


def _stems(word: str) -> set[str]:
    """The word, and the word without a glued article, preposition or verb prefix."""
    return {word} | {
        word[len(p) :] for p in GLUED_AR if word.startswith(p) and len(word) > len(p) + 1
    }


def _found_in_arabic(form: str, text: str, words: list[str]) -> bool:
    if " " in form:
        return form in text
    if len(form) <= 3:  # short forms must start a word: "طرد" in "طردوني", not in "مطرد"
        return any(stem.startswith(form) for w in words for stem in _stems(w))
    return any(form in w for w in words)


def find_terms(text: str, lexicon: tuple[Entry, ...] | None = None) -> list[Entry]:
    """Lexicon entries whose Darija words appear in `text`, in lexicon order."""
    lexicon = lexicon or load_lexicon()
    normalized = normalize(text)
    words = normalized.split()
    return [
        entry
        for entry in lexicon
        if entry.arabizi.search(text)
        or any(_found_in_arabic(form, normalized, words) for form in entry.darija_ar)
    ]
