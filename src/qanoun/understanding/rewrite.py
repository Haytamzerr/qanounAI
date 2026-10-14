"""Turn a question into the text we search with.

- formal Arabic and French: searched as they are (the model already gets 100% on them);
- Darija, in either script: the question plus the legal terms of the Darija words it uses.

Converting Arabizi to Arabic script is available (`use_arabizi=True`) but off by default:
measured with the real model, it lowered Arabizi scores (development 78% → 33%, held-out
50% → 42%), because its approximate spellings ("الهق" for الحق) add noise. See decision 40.

With a `rewriter` (see llm_rewrite.py), an Arabizi question is also restated in formal Arabic
by the language model, and that line is added too. Measured (decision 53): held-out Arabizi
50% → 92% hit@5; Darija in Arabic letters is already at 100% with the lexicon and lost a
question with the rewrite, so it is not rewritten.

Keeping the original question means nothing is lost when the conversion, the lexicon or the
rewrite is wrong: the search model sees all of them and weighs them.
"""

from collections.abc import Callable
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
    rewritten: str | None = None  # the language model's formal-Arabic version

    @property
    def legal_terms(self) -> list[str]:
        return list(dict.fromkeys(t for entry in self.terms for t in entry.legal_ar))


def understand(
    question: str,
    *,
    use_arabizi: bool = False,
    use_lexicon: bool = True,
    rewriter: Callable[[str], str | None] | None = None,
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
    if rewriter is not None and language == "darija-latn":
        result.rewritten = rewriter(question)
        parts.append(result.rewritten or "")
    result.query = "\n".join(p for p in parts if p)
    return result
