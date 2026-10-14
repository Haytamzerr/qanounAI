"""From a question to a checked answer.

    question → understand (language, Darija lexicon) → retrieve k articles
             → the model writes from them → citations checked → (one retry if needed) → answer

If the check fails, the model gets one second chance: its previous answer and the problems are
shown, so it corrects rather than rewrites. If the second answer still fails, or refuses although
the first one answered, the best answer is returned marked as unverified, so the interface warns
instead of hiding the problem. Each attempt is logged ("qanoun.answer") for error analysis.
"""

import json
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field

from qanoun.generation.citations import check
from qanoun.generation.llm import LLM
from qanoun.generation.prompts import ANSWER_SCHEMA, system_prompt, user_prompt
from qanoun.ingestion.models import Article
from qanoun.understanding.rewrite import understand

log = logging.getLogger("qanoun.answer")

Retriever = Callable[[str, int], list[Article]]  # (search query, k) -> articles, best first

NOT_COVERED = {
    "ar": "لم أجد في النصوص المتوفرة لدي ما يجيب عن هذا السؤال. "
    "يُستحسن استشارة محامٍ أو الجهة المختصة.",
    "darija-ar": "ما لقيتش فالنصوص اللي عندي جواب على هاد السؤال. "
    "الأحسن تسول محامي ولا الإدارة المعنية.",
    "darija-latn": "Ma l9itch f nnosous li 3ndi jwab 3la had soual. L7sen tsowel chi m7ami.",
    "fr": "Je n'ai pas trouvé de réponse dans les textes dont je dispose. "
    "Mieux vaut consulter un avocat ou l'administration compétente.",
}  # fmt: skip


@dataclass
class Answer:
    question: str
    language: str
    status: str  # "answered" or "not_covered"
    text: str
    sources: list[Article]  # what was retrieved and shown to the model
    cited: list[int] = field(default_factory=list)  # 1-based positions in `sources`
    problems: list[str] = field(default_factory=list)
    attempts: int = 1
    seconds: dict[str, float] = field(default_factory=dict)
    model: str = ""
    history: list[str] = field(default_factory=list)  # one line per attempt

    @property
    def verified(self) -> bool:
        return not self.problems

    @property
    def cited_articles(self) -> list[Article]:
        return [self.sources[n - 1] for n in self.cited]


def _parse(raw: str) -> tuple[str, str, list[int]]:
    """(status, answer, used sources) from the model's JSON, tolerating plain text."""
    try:
        data = json.loads(raw)
        return (
            data.get("status", "answered"),
            str(data.get("answer", "")),
            [int(n) for n in data.get("used_sources", []) if str(n).isdigit()],
        )
    except (json.JSONDecodeError, AttributeError, TypeError):
        return "answered", raw, []


class Answerer:
    def __init__(self, retriever: Retriever, llm: LLM, k: int = 5, retries: int = 1):
        self.retriever = retriever
        self.llm = llm
        self.k = k
        self.retries = retries

    def answer(self, question: str) -> Answer:
        clock = time.perf_counter()
        understood = understand(question)
        sources = self.retriever(understood.query, self.k)
        seconds = {"retrieval": time.perf_counter() - clock}
        language = understood.language
        if not sources:
            return Answer(
                question, language, "not_covered", NOT_COVERED[language], [], seconds=seconds
            )

        log.info("sources: %s", ", ".join(a.id for a in sources))
        system = system_prompt(language)
        prompt = user_prompt(question, sources)
        clock = time.perf_counter()
        history, best = [], None
        for attempt in range(1, self.retries + 2):
            raw = self.llm.generate(system, prompt, json_schema=ANSWER_SCHEMA)
            status, text, used = _parse(raw)
            answered = status != "not_covered"
            checked = check(text, sources, used, answered=answered)
            line = f"attempt {attempt}: {status}" + (
                f" — rejected: {'; '.join(checked.problems)}" if checked.problems else ""
            )
            history.append(line)
            log.info(line)
            if best is None or (answered and not best[0]) or (answered and checked.ok):
                best = (answered, checked)  # a refusal never replaces an answer
            if checked.ok or attempt > self.retries:
                break
            prompt = (
                user_prompt(question, sources)
                + "\n\nYOUR PREVIOUS ANSWER:\n"
                + text
                + "\n\nIT BROKE THE RULES:\n- "
                + "\n- ".join(checked.problems)
                + "\nCorrect only these problems and keep what was right. Cite only the numbered "
                "sources; if the sources answer the question, do not refuse."
            )
        answered, checked = best
        seconds["generation"] = time.perf_counter() - clock
        return Answer(
            question,
            language,
            "answered" if answered else "not_covered",
            checked.text if answered else (checked.text or NOT_COVERED[language]),
            list(sources),
            checked.cited if answered else [],
            checked.problems,
            attempt,
            seconds,
            self.llm.name,
            history,
        )
