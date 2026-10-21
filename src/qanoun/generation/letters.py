"""Letters from an analysis: a notice, a complaint or a request, ready to fill in (decision 84).

The analysis often ends with "send a written notice to the landlord" or "file a complaint". Most
people do not know how such a letter is written. From the person's file (what happened, their
role, what they want), the analysis and the articles it cited, the model drafts the letter in
formal Arabic or French:

- it may only rely on the articles given, named in full ("المادة 10 من القانون رقم 67.12"); the
  citation checker verifies every article number it writes, with one retry, as for answers;
- it never invents a fact: names, addresses, dates, amounts it was not told are left as
  placeholders in square brackets ("[الاسم الكامل]") for the person to fill in;
- the person reads and signs it: it is a draft, and the interface says so.
"""

import json
import logging
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date

from qanoun.generation.citations import ARTICLE_MENTION, check
from qanoun.generation.llm import LLM
from qanoun.ingestion.models import Article

log = logging.getLogger("qanoun.letters")

KINDS = {
    "notice": "a formal notice to the other party (landlord, employer, debtor, seller…), asking "
    "them to do what the law requires within the legal time limit, sent by registered mail or "
    "through a commissaire judiciaire",
    "complaint": "a complaint to the competent authority (the public prosecutor, the labour "
    "inspector, the consumer protection service…), stating the facts and asking it to act",
    "request": "a request to the competent court, office or administration, asking for what the "
    "law allows in this situation",
}
LANGUAGES = {"ar": "formal Modern Standard Arabic", "fr": "formal French"}

LETTER_SYSTEM = """You draft letters for people in Morocco, from their situation and the Moroccan
legal articles given.

Rules:
1. Rely ONLY on the numbered articles given. Name each article you rely on in full in the
   body ("المادة 10 من القانون رقم 67.12" / "l'article 10 de la loi n° 67.12"), and list its
   number in "used_sources". Never cite an article from memory.
2. Never invent a fact. Every name, address, date, amount or reference you were not told is a
   placeholder in square brackets, e.g. [الاسم الكامل], [العنوان], [التاريخ], [Nom et prénom].
3. The letter follows the usual Moroccan layout: sender with placeholders, recipient, city and
   date placeholder, subject line, a respectful opening, the facts in neutral sentences, the
   legal basis, a precise request with the legal time limit when an article sets one, a
   closing formula, "signature".
4. Calm, firm, courteous; no threats beyond the legal consequences the articles state.
5. Write in {language}, whatever language the situation is written in.

The letter is: {kind}."""

LETTER_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "subject": {"type": "STRING"},
        "recipient": {"type": "STRING"},
        "body": {"type": "STRING"},
        "used_sources": {"type": "ARRAY", "items": {"type": "INTEGER"}},
    },
    "required": ["subject", "recipient", "body", "used_sources"],
}


@dataclass
class Letter:
    kind: str
    language: str
    subject: str
    recipient: str
    body: str
    cited: list[str] = field(default_factory=list)  # ids of the articles it relies on
    problems: list[str] = field(default_factory=list)
    attempts: int = 1

    @property
    def verified(self) -> bool:
        return not self.problems


def _prompt(story: str, facts: Sequence[str], analysis: dict, sources: Sequence[Article]) -> str:
    from qanoun.generation.prompts import describe

    blocks = [f"[{n}] {describe(a)}" for n, a in enumerate(sources, start=1)]
    parts = [
        "ARTICLES\n\n" + "\n\n".join(blocks),
        f"THE PERSON'S SITUATION, IN THEIR WORDS\n{story}",
    ]
    if facts:
        parts.append("WHAT THEY SELECTED\n" + "\n".join(f"- {f}" for f in facts))
    if analysis:
        text = "\n".join(f"{k}: {v}" for k, v in analysis.items() if v and k != "missing")
        parts.append(f"THE ANALYSIS ALREADY GIVEN TO THEM\n{text}")
    parts.append(f"TODAY\n{date.today().isoformat()}")
    return "\n\n".join(parts)


def write_letter(
    llm: LLM,
    kind: str,
    language: str,
    story: str,
    sources: Sequence[Article],
    facts: Sequence[str] = (),
    analysis: dict | None = None,
    retries: int = 1,
) -> Letter:
    if kind not in KINDS or language not in LANGUAGES:
        raise ValueError("unknown kind or language")
    system = LETTER_SYSTEM.format(language=LANGUAGES[language], kind=KINDS[kind])
    base = _prompt(story, facts, analysis or {}, sources)
    own = set(ARTICLE_MENTION.findall(story))
    prompt, best = base, None
    for attempt in range(1, retries + 2):
        try:
            data = json.loads(llm.generate(system, prompt, json_schema=LETTER_SCHEMA))
            used = [int(n) for n in data.get("used_sources", []) if str(n).isdigit()]
            subject, recipient = str(data.get("subject", "")), str(data.get("recipient", ""))
            body = str(data.get("body", "")).strip()
        except (json.JSONDecodeError, AttributeError, TypeError, ValueError):
            used, subject, recipient, body = [], "", "", ""
        checked = check(body, sources, used, answered=bool(body), allowed=own)
        problems = checked.problems + ([] if body else ["the letter is empty"])
        letter = Letter(
            kind, language, subject.strip(), recipient.strip(), checked.text,
            [sources[n - 1].id for n in checked.cited], problems, attempt,
        )  # fmt: skip
        if best is None or not problems:
            best = letter
        if not problems:
            break
        log.info("letter attempt %d rejected: %s", attempt, "; ".join(problems))
        prompt = (
            base + "\n\nYOUR PREVIOUS DRAFT:\n" + body + "\n\nIT BROKE THE RULES:\n- "
            + "\n- ".join(problems) + "\nCorrect only these problems."
        )  # fmt: skip
    return best
