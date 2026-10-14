"""Tell the four kinds of question apart: "ar", "darija-ar", "fr", "darija-latn".

Rules, not a model: they are instant, explainable, and testable on every labelled question.
- Arabic letters: Darija if it uses a word formal Arabic doesn't ("شنو", "واش", "ديال"…).
- Latin letters: Arabizi if a digit stands for a letter ("3ndi", "l7e9") or a Darija word appears
  ("wach", "chhal", "dyal"…); otherwise French.
"""

import re

from qanoun.retrieval.text import normalize

ARABIC_LETTER = re.compile(r"[ء-ي]")
LATIN_LETTER = re.compile(r"[A-Za-zÀ-ÿ]")
WORD = re.compile(r"[\w']+")

# Normalised the same way as the text (ة→ه, ى→ي, alef forms), so spelling variants match.
DARIJA_AR_WORDS = {
    normalize(w)
    for w in [
        "شنو",
        "شنوة",
        "اشنو",
        "شحال",
        "واش",
        "ديال",
        "ديالي",
        "ديالك",
        "ديالو",
        "ديالها",
        "ديالهم",
        "باش",
        "خاصني",
        "خاصك",
        "خاصو",
        "دابا",
        "بغيت",
        "بغا",
        "بغات",
        "بغينا",
        "فين",
        "علاش",
        "كيفاش",
        "فاش",
        "بزاف",
        "ماشي",
        "هادشي",
        "هاد",
        "هادي",
        "داك",
        "ديك",
        "شي",
        "كاين",
        "كاينة",
        "كاينين",
        "مكاينش",
        "والو",
        "غادي",
        "حيت",
        "ملي",
        "السيمانة",
        "الدراري",
        "طردوني",
        "طردوك",
        "كيخدم",
        "كنخدم",
        "نخدم",
        "فالسيمانة",
        "فالخدمة",
        "خدام",
        "خدامة",
        "الباطرون",
        "كونجي",
        "الكونجي",
    ]
}
# Words that exist in Darija but never alone in a French sentence ("fin" and "la" are excluded:
# they are French words too).
DARIJA_LATN_WORDS = set(
    [
        "wach",
        "wash",
        "chhal",
        "chhel",
        "ch7al",
        "chno",
        "chnou",
        "achno",
        "achnou",
        "chnu",
        "dyal",
        "dyali",
        "dyalk",
        "dyalo",
        "dyalha",
        "dyalhom",
        "bghit",
        "bgha",
        "bghat",
        "bghina",
        "bghit",
        "kifach",
        "kifash",
        "3lach",
        "3lash",
        "fach",
        "ila",
        "mn",
        "bla",
        "kayn",
        "kayna",
        "kayen",
        "makaynch",
        "3ndi",
        "3andi",
        "3ndek",
        "ndir",
        "n9der",
        "y9der",
        "t9der",
        "khdma",
        "khedma",
        "lkhedma",
        "lkhdma",
        "daba",
        "bzaf",
        "machi",
        "hadchi",
        "wla",
        "rah",
        "ghadi",
        "chkoun",
        "chkon",
        "wakha",
        "m3a",
        "hna",
        "ana",
        "nta",
        "nti",
        "howa",
        "hiya",
        "homa",
        "ma3ndich",
        "tredouni",
        "jrawni",
        "chi",
        "lih",
        "liha",
        "liya",
        "fl",
        "bach",
    ]
)
DIGIT_AS_LETTER = re.compile(r"[a-z]*[235789][a-z]|[a-z][235789]", re.IGNORECASE)


def detect_language(text: str) -> str:
    arabic = len(ARABIC_LETTER.findall(text))
    latin = len(LATIN_LETTER.findall(text))
    words = WORD.findall(text)
    if arabic >= latin:
        normalized = {normalize(w) for w in words}
        return "darija-ar" if normalized & DARIJA_AR_WORDS else "ar"
    lowered = [w.lower() for w in words]
    if any(DIGIT_AS_LETTER.search(w) and not w.isdigit() for w in lowered):
        return "darija-latn"
    return "darija-latn" if set(lowered) & DARIJA_LATN_WORDS else "fr"


def is_darija(language: str) -> bool:
    return language.startswith("darija")
