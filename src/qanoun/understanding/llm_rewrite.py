"""Ask the language model to restate a Darija question in the law's own words.

The lexicon only knows the words it lists; real Arabizi has endless spellings ("yjri 3liya",
"ykhrjni", "louhni"). A language model reads them the way a Moroccan does. For Darija questions
only, it restates the question as a short formal question in Modern Standard Arabic, using the
vocabulary of Moroccan legislation, and that line is added to what we search with.

The rewrite is never shown to the user and never replaces the question: if the model is busy or
wrong, the search still has the original question and the lexicon terms.
"""

import logging

from qanoun.generation.llm import LLM, LLMError

log = logging.getLogger("qanoun.rewrite")

SYSTEM = """You restate questions about Moroccan law for a search engine over Moroccan legal
texts written in formal Arabic.

The question is written in Moroccan Darija, in Arabic letters or in Latin letters with digits
(3 = ع, 7 = ح, 9 = ق, 2 = ء, 5 = خ), possibly mixed with French.

Rewrite it as ONE short question in Modern Standard Arabic, using the vocabulary of Moroccan
legislation (for example الأجير، المشغل، عقد الشغل، الفصل، الزوج، الحضانة، المستهلك، المورد،
المعطيات ذات الطابع الشخصي) instead of everyday words.

Keep the exact meaning. Do not answer the question, do not add facts, do not cite articles.
Reply with the rewritten question only."""


class LLMRewriter:
    """Callable: Darija question → formal Arabic question, or None if the model failed."""

    def __init__(self, llm: LLM):
        self.llm = llm
        self.cache: dict[str, str | None] = {}  # the same question is rewritten once

    def __call__(self, question: str) -> str | None:
        if question not in self.cache:
            try:
                rewritten = self.llm.generate(SYSTEM, question).strip().splitlines()
                self.cache[question] = rewritten[0].strip() if rewritten else None
            except LLMError as error:
                log.info("rewrite failed, searching without it: %s", error)
                return None  # not cached: next time the model may be free
            log.info("rewrite: %s", self.cache[question])
        return self.cache[question]
