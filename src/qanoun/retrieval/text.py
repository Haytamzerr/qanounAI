"""Text normalisation and tokenisation for keyword search (French and Arabic).

Search compares words, so the same word must always be written the same way. Arabic text varies
a lot for the same word: optional vowel marks (tashkeel), several forms of alef (أ إ آ ا), ى or
ي at the end, ة or ه, and glued prefixes ("والأجير" = "و" + "ال" + "أجير"). French varies by
accents and case. These functions remove that variation for searching only: the text shown to
users is never changed.
"""

import re
import unicodedata

TASHKEEL = re.compile(r"[ً-ْٰ]")  # vowel marks
TATWEEL = "ـ"  # decorative stretching, e.g. "الـمادة"
ARABIC_FOLDS = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ة": "ه"})
ARABIC_LETTER = re.compile(r"[ء-ي]")
TOKEN = re.compile(r"[\w]+", re.UNICODE)

# Glued prefixes, longest first: and-the, with-the, like-the, so-the, for-the, the, and
ARABIC_PREFIXES = ("وال", "بال", "كال", "فال", "لل", "ال")
MIN_STEM = 2  # never strip a prefix if less than this would remain

FRENCH_STOPWORDS = (
    "le la les l un une des de du d et ou a au aux en dans par pour sur que qui quoi ce cet "
    "cette ces est il elle on se sa son ses y ne pas plus je j mes mon ma quel quelle quels "
    "quelles comment combien"
)
ARABIC_STOPWORDS = (
    "في من علي الي عن مع او ان هذا هذه ذلك التي الذي ما لا هل كل هي هو كم متي كيف ثم قد"
)
STOPWORDS = set(FRENCH_STOPWORDS.split()) | set(ARABIC_STOPWORDS.split())  # Arabic: normalised


def is_arabic(token: str) -> bool:
    return bool(ARABIC_LETTER.search(token))


def normalize(text: str) -> str:
    """Lowercase, remove French accents and Arabic vowel marks, unify letter variants."""
    text = unicodedata.normalize("NFKC", text).lower()
    text = TASHKEEL.sub("", text).replace(TATWEEL, "")
    text = text.translate(ARABIC_FOLDS)
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(c for c in decomposed if unicodedata.category(c) != "Mn")


def strip_prefix(token: str) -> str:
    """Remove one glued Arabic prefix: "والاجير" -> "اجير", "للمستهلك" -> "مستهلك"."""
    for prefix in ARABIC_PREFIXES:
        if token.startswith(prefix) and len(token) - len(prefix) >= MIN_STEM:
            return token[len(prefix) :]
    if token.startswith(("و", "ب", "ف", "ل")) and len(token) > 4:  # "وبالتالي", "لمدة"…
        return token[1:]
    return token


def tokenize(text: str) -> list[str]:
    """Words of `text`, normalised, without stop words, with Arabic prefixes removed."""
    tokens = []
    for token in TOKEN.findall(normalize(text)):
        if token in STOPWORDS:
            continue
        if is_arabic(token):
            token = strip_prefix(token)
        if len(token) > 1 or token.isdigit():
            tokens.append(token)
    return tokens
