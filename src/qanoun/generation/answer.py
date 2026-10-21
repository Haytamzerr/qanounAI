"""From a question to a checked answer.

    question → understand (language, Darija lexicon) → retrieve k articles
             → the model writes from them → citations checked → (one retry if needed) → answer

Two modes (decision 75):
- "quick": one search, a short answer;
- "analysis": the model first plans the research (the facts that matter, 2–4 searches in the
  law's own words, the facts that are missing), each search is run, and the answer is written
  in sections: situation · what the law says · what it means for you · what you can do · what
  is missing. Every section is checked like a quick answer. The plan may also name articles the
  model believes apply ("Penal Code art. 124"): they are looked up in the official text and given
  as sources, never trusted as such; an article that does not exist is dropped (decision 78).

When the Darija lexicon recognises several legal ideas in one question ("I hit him / he started /
will I go to prison?" → assault, self-defence, prison), each idea also gets a small search of its
own and its best articles join the sources: one vector for the whole question averages the ideas
and the minority one is lost (decision 79).

A follow-up ("and if I have children?") is first rewritten into a standalone question using the
conversation, which is also shown to the model; the articles cited in the previous answer stay
available (decision 76).

If the check fails, the model gets one second chance: its previous answer and the problems are
shown, so it corrects rather than rewrites. If the second answer still fails, or refuses although
the first one answered, the best answer is returned marked as unverified, so the interface warns
instead of hiding the problem. Each attempt is logged ("qanoun.answer") for error analysis.
"""

import json
import logging
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from qanoun.generation.citations import ARTICLE_MENTION, check, style_problems
from qanoun.generation.deadlines import Deadline, verify
from qanoun.generation.llm import LLM
from qanoun.generation.prompts import (
    ANALYSIS_SCHEMA,
    ANSWER_SCHEMA,
    CONDENSE_SYSTEM,
    PLAN_SCHEMA,
    SECTIONS,
    analysis_system,
    conversation_block,
    plan_system,
    system_prompt,
    user_prompt,
)
from qanoun.ingestion.models import Article
from qanoun.understanding.language import detect_language
from qanoun.understanding.references import Reference, note
from qanoun.understanding.rewrite import understand

log = logging.getLogger("qanoun.answer")

Retriever = Callable[[str, int], list[Article]]  # (search query, k) -> articles, best first
Resolver = Callable[[str, str], list[Reference]]  # (question, language) -> articles it names
StepCallback = Callable[[str, dict], None]  # (step name, details)
Lookup = Callable[[str], Article | None]  # article id -> article


@dataclass(frozen=True)
class Turn:
    """One earlier exchange of the conversation, as the interface sends it back."""

    question: str
    answer: str
    sources: tuple[str, ...] = ()  # ids of the articles that answer cited


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
    status: str  # "answered", "not_covered" or "clarify" (a question back to the user)
    text: str
    sources: list[Article]  # what was retrieved and shown to the model
    cited: list[int] = field(default_factory=list)  # 1-based positions in `sources`
    problems: list[str] = field(default_factory=list)
    attempts: int = 1
    seconds: dict[str, float] = field(default_factory=dict)
    model: str = ""
    history: list[str] = field(default_factory=list)  # one line per attempt
    mode: str = "quick"  # "quick" or "analysis"
    sections: dict[str, str] | None = None  # analysis mode: situation, law, application…
    plan: list[str] = field(default_factory=list)  # analysis mode: the searches that were run
    leads: list[str] = field(default_factory=list)  # analysis: ids of suggested articles found
    deadlines: list[Deadline] = field(default_factory=list)  # analysis: verified time limits
    standalone: str | None = None  # a follow-up rewritten with the conversation

    @property
    def verified(self) -> bool:
        return not self.problems

    @property
    def cited_articles(self) -> list[Article]:
        return [self.sources[n - 1] for n in self.cited]


STATUSES = {"answered", "not_covered", "clarify"}


def _parse(raw: str) -> tuple[str, str, list[int]]:
    """(status, answer, used sources) from the model's JSON, tolerating plain text."""
    try:
        data = json.loads(raw)
        status = data.get("status", "answered")
        return (
            status if status in STATUSES else "answered",
            str(data.get("answer", "")),
            [int(n) for n in data.get("used_sources", []) if str(n).isdigit()],
        )
    except (json.JSONDecodeError, AttributeError, TypeError):
        return "answered", raw, []


class Answerer:
    def __init__(
        self,
        retriever: Retriever,
        llm: LLM,
        k: int = 6,
        retries: int = 1,
        rewriter: Callable[[str], str | None] | None = None,
        references: Resolver | None = None,
        lookup: Lookup | None = None,
        per_search: int = 4,
        max_sources: int = 14,
        per_idea: int = 2,
        max_ideas: int = 3,
    ):
        self.retriever = retriever
        self.llm = llm
        self.rewriter = rewriter
        self.references = references
        self.lookup = lookup
        self.k = k
        self.retries = retries
        self.per_search = per_search
        self.max_sources = max_sources
        self.per_idea = per_idea
        self.max_ideas = max_ideas

    # ---------- entry point ----------

    def answer(
        self,
        question: str,
        on_step: StepCallback | None = None,
        *,
        mode: str = "quick",
        history: Sequence[Turn] = (),
        facts: Sequence[str] = (),
        document: Sequence[str] = (),
    ) -> Answer:
        """`on_step(name, details)` is called as the work progresses, so an interface can show
        "searching…", "writing…" while the user waits (see the API's streaming endpoint)."""
        step = on_step or (lambda name, details: None)
        clock = time.perf_counter()
        history = list(history)[-4:]
        language = detect_language(question)
        standalone = self._standalone(question, history) if history else None
        if standalone:
            step("condensed", {"question": standalone})
        understood = understand(standalone or question, rewriter=self.rewriter)
        step("understood", {"language": language, "rewritten": understood.rewritten})

        # Articles named in the question come first (decision 71), then the articles the
        # previous answer cited (a follow-up is often about them), then what the search finds
        refs = self.references(standalone or question, language) if self.references else []
        named = [r.article for r in refs if r.article is not None]
        notes = [n for r in refs if (n := note(r))]
        facts = [f.strip() for f in facts if f.strip()][:6]  # chosen in the situation builder
        if facts:
            notes.append("What the person selected about the situation: " + "; ".join(facts))
        clauses = [c.strip() for c in document if c.strip()][:8]  # from "read my document" (86)
        if clauses:
            notes.append(
                "Clauses quoted from the person's document; check each one against the sources:"
                + "".join(f"\n  «{c}»" for c in clauses)
            )
        carried = self._carried(history)
        talk = [(t.question, t.answer) for t in history]

        if mode == "analysis":
            planned = self._plan(standalone or question, language, talk, facts, clauses)
            if planned is not None:
                situation, searches, missing, suggested = planned
                leads = self._leads(suggested, language)
                step("planned", {"situation": situation, "searches": searches,
                                 "articles": [a.id for a in leads]})  # fmt: skip
                found = self._by_idea(understood)  # few, and kept within the 14 sources
                found += [a for q in searches for a in self._search(q, self.per_search)]
                found += self._search(understood.query, self.per_search, done=True)
                limit = self.max_sources + (4 if clauses else 0)  # a contract raises more questions
                sources = _unique([*named, *leads, *found, *carried])[:limit]
                seconds = {"retrieval": time.perf_counter() - clock}
                step("sources", {"articles": [a.id for a in sources]})
                answer = self._write_analysis(
                    question, language, sources, notes, talk, missing, step, seconds
                )
                answer.plan, answer.standalone = searches, standalone
                answer.leads = [a.id for a in leads if a in sources]
                return answer
            log.info("planning failed: quick answer instead")

        found = [*self.retriever(understood.query, self.k), *self._by_idea(understood)]
        sources = _unique([*named, *found, *carried])
        seconds = {"retrieval": time.perf_counter() - clock}
        step("sources", {"articles": [a.id for a in sources]})
        answer = self._write_quick(question, language, sources, notes, talk, step, seconds)
        answer.standalone = standalone
        return answer

    # ---------- steps ----------

    def _standalone(self, question: str, talk: Sequence[Turn]) -> str | None:
        """ "w ila 3ndi drari?" + the conversation → a question search can use on its own."""
        prompt = (
            f"CONVERSATION\n{conversation_block([(t.question, t.answer) for t in talk])}"
            f"\n\nLAST MESSAGE\n{question}"
        )
        try:
            rewritten = self.llm.generate(CONDENSE_SYSTEM, prompt).strip().strip('"«»')
        except Exception as error:  # the follow-up is still answered, with the conversation
            log.info("follow-up rewrite failed: %s", error)
            return None
        return rewritten if 2 <= len(rewritten) <= 600 else None

    def _carried(self, talk: Sequence[Turn]) -> list[Article]:
        if not talk or self.lookup is None:
            return []
        return [a for i in talk[-1].sources[:3] if (a := self.lookup(i)) is not None]

    def _plan(
        self, question, language, talk, facts=(), clauses=()
    ) -> tuple[str, list[str], list[str], list[str]] | None:
        prompt = (f"CONVERSATION SO FAR\n{conversation_block(talk)}\n\n" if talk else "") + (
            f"SITUATION\n{question}"
        )
        if facts:
            prompt += "\n\nWHAT THE PERSON SELECTED\n" + "\n".join(f"- {f}" for f in facts)
        if clauses:
            prompt += "\n\nCLAUSES OF THE PERSON'S DOCUMENT\n" + "\n".join(
                f"- {c}" for c in clauses
            )
        try:
            data = json.loads(
                self.llm.generate(plan_system(language), prompt, json_schema=PLAN_SCHEMA)
            )
            most = 6 if clauses else 4  # one search per clause that may conflict with the law
            searches = [str(q).strip() for q in data.get("searches", []) if str(q).strip()][:most]
            missing = [str(m).strip() for m in data.get("missing", []) if str(m).strip()][:3]
            suggested = [str(m).strip() for m in data.get("articles", []) if str(m).strip()][:4]
            return str(data.get("situation", "")), searches, missing, suggested
        except Exception as error:  # a broken plan must not cost the person an answer
            log.info("plan rejected: %s", error)
            return None

    def _leads(self, suggested: Sequence[str], language: str) -> list[Article]:
        """The suggested articles that exist in the official text (the others are dropped)."""
        if self.references is None:
            return []
        found = [r.article for s in suggested for r in self.references(s, language)]
        leads = _unique([a for a in found if a is not None])[:4]
        if len(leads) < len(suggested):
            log.info("plan leads: %d of %d found", len(leads), len(suggested))
        return leads

    def _by_idea(self, understood) -> list[Article]:
        """The best articles for each legal idea, when the question raises several."""
        ideas = list(dict.fromkeys(" ".join(e.legal_ar) for e in understood.terms))
        ideas = [i for i in ideas if len(i.split()) > 1]  # "المكري" names a party, not an issue
        if len(ideas) < 2:
            return []  # one idea: the question's own search already targets it
        return [a for idea in ideas[: self.max_ideas] for a in self.retriever(idea, self.per_idea)]

    def _search(self, query: str, k: int, done: bool = False) -> list[Article]:
        """One search of the plan; plan queries go through the Darija lexicon too."""
        return self.retriever(query if done else understand(query).query, k)

    # ---------- writing and checking ----------

    def _attempts(self, question, language, sources, system, schema, prompt_of, parse, step):
        """Write, check, and retry once with the problems shown (shared by both modes).

        Citation problems make an answer unverified; writing problems (Arabic letters in an
        Arabizi answer…) only earn a retry, they do not make the law wrong (decision 80)."""
        own = set(ARTICLE_MENTION.findall(question))  # numbers the person wrote may come back
        prompt = prompt_of()
        lines, best = [], None
        for attempt in range(1, self.retries + 2):
            step("writing", {"attempt": attempt})
            status, text, used, extra = parse(self.llm.generate(system, prompt, json_schema=schema))
            answered = status == "answered"
            checked = check(text, sources, used, answered=answered, allowed=own)
            style = style_problems(text, language) if answered else []
            problems = [*checked.problems, *style]
            line = f"attempt {attempt}: {status}" + (
                f" — rejected: {'; '.join(problems)}" if problems else ""
            )
            lines.append(line)
            log.info(line)
            better = best is None or (answered and not best[0])
            better = better or (answered and checked.ok and (not best[1].ok or not style))
            if better:
                best = (answered, checked, status, extra)  # a refusal never replaces an answer
            if not problems or attempt > self.retries:
                break
            prompt = (
                prompt_of()
                + "\n\nYOUR PREVIOUS ANSWER:\n"
                + text
                + "\n\nIT BROKE THE RULES:\n- "
                + "\n- ".join(problems)
                + "\nCorrect only these problems and keep what was right. Cite only the numbered "
                "sources; if the sources answer the question, do not refuse."
            )
        return best, attempt, lines

    def _write_quick(self, question, language, sources, notes, talk, step, seconds) -> Answer:
        if not sources and not notes:
            return Answer(
                question, language, "not_covered", NOT_COVERED[language], [], seconds=seconds
            )
        log.info("sources: %s", ", ".join(a.id for a in sources))
        clock = time.perf_counter()

        def parse(raw):
            status, text, used = _parse(raw)
            return status, text, used, None

        (answered, checked, status, _), attempt, lines = self._attempts(
            question,
            language,
            sources,
            system_prompt(language),
            ANSWER_SCHEMA,
            lambda: user_prompt(question, sources, notes, talk),
            parse,
            step,
        )
        seconds["generation"] = time.perf_counter() - clock
        return Answer(
            question,
            language,
            status,
            checked.text if answered else (checked.text or NOT_COVERED[language]),
            list(sources),
            checked.cited if answered else [],
            checked.problems,
            attempt,
            seconds,
            self.llm.name,
            lines,
        )

    def _write_analysis(
        self, question, language, sources, notes, talk, missing, step, seconds
    ) -> Answer:
        log.info("sources: %s", ", ".join(a.id for a in sources))
        clock = time.perf_counter()
        hints = notes + (
            [f"Facts not given (ask about them in 'missing'): {'; '.join(missing)}"]
            if missing
            else []
        )

        found_deadlines: list[list[dict]] = []  # per attempt, kept for the attempt chosen

        def parse(raw):
            try:
                data = json.loads(raw)
                found_deadlines.append(list(data.get("deadlines") or []))
                sections = {name: str(data.get(name, "")).strip() for name in SECTIONS}
                used = [int(n) for n in data.get("used_sources", []) if str(n).isdigit()]
                status = data.get("status", "answered")
            except (json.JSONDecodeError, AttributeError, TypeError):
                found_deadlines.append([])
                sections, used, status = (
                    {"situation": raw, **dict.fromkeys(SECTIONS[1:], "")},
                    [],
                    "answered",
                )
            text = "\n\n".join(v for v in sections.values() if v)
            extra = {"sections": sections, "deadlines": found_deadlines[-1]}
            return (status if status in STATUSES else "answered"), text, used, extra

        (answered, checked, status, extra), attempt, lines = self._attempts(
            question,
            language,
            sources,
            analysis_system(language),
            ANALYSIS_SCHEMA,
            lambda: user_prompt(question, sources, hints, talk),
            parse,
            step,
        )
        seconds["generation"] = time.perf_counter() - clock
        sections = extra["sections"] if extra else None
        deadlines = verify(extra["deadlines"], sources) if extra and answered else []
        if sections is not None:  # unknown [n] markers removed in every section, as in the text
            sections = {
                name: check(value, sources, answered=False).text for name, value in sections.items()
            }
        return Answer(
            question,
            language,
            status,
            checked.text if answered else (checked.text or NOT_COVERED[language]),
            list(sources),
            checked.cited if answered else [],
            checked.problems,
            attempt,
            seconds,
            self.llm.name,
            lines,
            mode="analysis",
            sections=sections if answered else None,
            deadlines=deadlines,
        )


def _unique(articles: Sequence[Article]) -> list[Article]:
    return list({a.id: a for a in articles}.values())
