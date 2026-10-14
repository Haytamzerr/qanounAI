"""Convert Arabizi (Darija in Latin letters) into Arabic script.

"3ndi l7e9" → "عندي الحق". Arabizi uses digits for sounds Latin letters lack: 3 = ع, 7 = ح,
9 = ق, 2 = ء, 5 = خ, 8 = ه. The conversion is approximate: Latin spelling doesn't show emphatic
letters (t can be ت or ط), and short vowels are dropped as in written Darija. The search model
tolerates these errors; the lexicon adds the exact legal terms.

French words (any accented letter, or "d'", "l'") are left as they are: the model reads French.
"""

import re

DIGRAPHS = {"ch": "ش", "sh": "ش", "kh": "خ", "gh": "غ", "dj": "ج", "th": "ث", "ou": "و"}
LETTERS = {
    "2": "ء", "3": "ع", "5": "خ", "7": "ح", "8": "ه", "9": "ق",
    "a": "ا", "b": "ب", "c": "ك", "d": "د", "f": "ف", "g": "ك", "h": "ه", "i": "ي", "j": "ج",
    "k": "ك", "l": "ل", "m": "م", "n": "ن", "o": "و", "p": "ب", "q": "ق", "r": "ر", "s": "س",
    "t": "ت", "u": "و", "v": "ف", "w": "و", "x": "كس", "y": "ي", "z": "ز",
}  # fmt: skip
# Very common words have a settled spelling in Arabic letters: use it rather than the rules.
COMMON = {
    "chhal": "شحال", "ch7al": "شحال", "wach": "واش", "wash": "واش", "chno": "شنو", "chnou": "شنو",
    "achno": "اشنو", "dyal": "ديال", "dyali": "ديالي", "dyalk": "ديالك", "dyalo": "ديالو",
    "dyalha": "ديالها", "bla": "بلا", "mn": "من", "men": "من", "f": "ف", "fi": "في", "l": "ل",
    "li": "لي", "liya": "ليا", "lia": "ليا", "lik": "ليك", "lih": "ليه", "liha": "ليها",
    "3la": "على", "3lih": "عليه", "m3a": "مع", "ma3a": "مع", "ba3d": "بعد", "9bel": "قبل",
    "chkoun": "شكون", "chkon": "شكون", "kifach": "كيفاش", "3lach": "علاش", "fin": "فين",
    "haja": "حاجة", "7aja": "حاجة", "chi": "شي", "ila": "إلى", "ana": "أنا", "nta": "نتا",
    "hiya": "هي", "howa": "هو", "daba": "دابا", "bzaf": "بزاف", "ghir": "غير", "ma": "ما",
    "la": "لا", "wla": "ولا", "rah": "راه", "bach": "باش", "kayn": "كاين", "makaynch": "ماكاينش",
    "ndir": "ندير", "mra": "مرا", "rajel": "راجل", "rajl": "راجل", "3am": "عام", "l3am": "العام",
}  # fmt: skip
TOKEN = re.compile(r"[A-Za-zÀ-ÿ0-9']+|[^A-Za-zÀ-ÿ0-9'\s]+")
FRENCH = re.compile(r"[à-ÿ]|^(?:d|l|qu|j|n|s|c)'", re.IGNORECASE)
CONSONANT_START = re.compile(r"^l(?:[^aeiouy']|y[^aeiou])")


def transliterate_word(word: str) -> str:
    word = word.lower()
    if word in COMMON:
        return COMMON[word]
    if FRENCH.search(word) or word.isdigit():
        return word
    word = re.sub(r"(.)\1+", r"\1", word)  # "chhal" and "chhaal" are spelled alike
    prefix = ""
    if CONSONANT_START.match(word) and len(word) > 2:  # "lkhedma" → "ال" + "khedma"
        prefix, word = "ال", word[1:]
    elif word.startswith("el") and len(word) > 3:
        prefix, word = "ال", word[2:]
    out, i = [], 0
    while i < len(word):
        pair = word[i : i + 2]
        if pair in DIGRAPHS:
            out.append(DIGRAPHS[pair])
            i += 2
            continue
        char = word[i]
        last = i == len(word) - 1
        if i == 0 and char in "aeiou":
            out.append("ا" + {"o": "و", "u": "و"}.get(char, ""))  # "internet" → "انترنت"
        elif char == "e":
            pass  # short vowel: not written
        elif char == "a" and last and len(word) > 3 and word[-2] not in "hy":
            out.append("ة")  # "khedma" → "خدمة", but "nraj3ha" → "نراجعها"
        else:
            out.append(LETTERS.get(char, ""))
        i += 1
    return prefix + "".join(out)


def transliterate(text: str) -> str:
    return " ".join(
        transliterate_word(token) if token[0].isalnum() else token for token in TOKEN.findall(text)
    )
