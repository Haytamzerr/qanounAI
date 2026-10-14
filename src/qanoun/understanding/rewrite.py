"""Turn a question into the text we search with.

- formal Arabic and French: searched as they are (the model already gets 100% on them);
- Darija in Arabic letters: the question plus the legal terms of the Darija words it uses;
- Arabizi: the question, its Arabic-script version, plus the legal terms.

Keeping the original question means nothing is lost when the conversion or the lexicon is wrong:
the search model sees all three and weighs them.
"""

from dataclasses import dataclass, field

from qanoun.understanding.arabizi import transliterate
from qanoun.understanding.language import detect_language, is_darija
from qanoun.understanding.lexicon import Entry, find_terms


@dataclass
class Understanding:
    question: str
    language: str
    query: str  # what the search engines receive
    arabic_script: str | None = None  # Arabizi converted to Arabic letters
    terms: list[Entry] = field(default_factory=list)

    @property
    def legal_terms(self) -> list[str]:
        return list(dict.fromkeys(t for entry in self.terms for t in entry.legal_ar))


def understand(
    question: str, *, use_arabizi: bool = True, use_lexicon: bool = True
) -> Understanding:
    language = detect_language(question)
    result = Understanding(question, language, question)
    if not is_darija(language):
        return result
    parts = [question]
    if language == "darija-latn" and use_arabizi:
        result.arabic_script = transliterate(question)
        parts.append(result.arabic_script)
    if use_lexicon:
        result.terms = find_terms(question)
        parts.append(" ".join(result.legal_terms))
    result.query = "\n".join(p for p in parts if p)
    return result
