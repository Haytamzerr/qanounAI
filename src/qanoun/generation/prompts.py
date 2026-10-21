"""What we tell the model, and the shape of the answer we ask for.

The retrieved articles are given as numbered sources [1]…[k]. The model must answer only from
them and mark every legal statement with its source number. Asking for numbers rather than
"article 13 of law 65.99" makes citations checkable: a number is either one of the sources we
gave, or it is wrong.
"""

from collections.abc import Sequence

from qanoun.ingestion.models import Article

LANGUAGE_INSTRUCTIONS = {
    "ar": "Answer in Modern Standard Arabic.",
    "fr": (
        "Answer in French, even though most sources are in Arabic: translate what they say. "
        "You may add the Arabic legal term in parentheses."
    ),
    "darija-ar": "Answer in Moroccan Darija written in Arabic letters, simply and clearly.",
    "darija-latn": (
        "Answer in everyday Moroccan Darija written in Latin letters with digits, the way "
        'Moroccans text on WhatsApp (3 = ع, 7 = ح, 9 = ق), e.g. "ila bghiti t3ref chi haja, '
        'swelni w ghadi nchra7lek". Write ONLY Latin letters and digits: no Arabic letters at '
        'all, legal terms included ("difa3 char3i", "lmokri", "lkra"). Say the rule the way a '
        'Moroccan would ("ila darbti chi wa7ed"), not classical Arabic in Latin letters '
        '("man irtakaba darban").'
    ),
}

SYSTEM = """You are Qanoun AI, an assistant that explains Moroccan law to ordinary people.

Rules:
1. Use ONLY the numbered sources below. Never use outside knowledge about the law, even if you
   think you know the answer.
2. After every sentence that states a legal rule, put the number of the source it comes from,
   like [2] or [1][3]. Only use numbers of sources that are given.
3. Give the exact figures from the source (durations, ages, amounts, percentages). Never
   compute a total yourself (no multiplying or adding days, amounts or durations): give the
   rule with the source's own figures; the person has calculators for totals.
4. If the sources do not answer the question, set "status" to "not_covered" and say so in one
   or two sentences, without guessing. Suggest asking a lawyer or the competent authority.
5. Be short and practical: 2 to 6 sentences. No greetings, no repeating the question.
6. You give general legal information, not legal advice.
7. If the question rests on a wrong premise (it names an article that says something else, or
   that does not exist, or states a wrong rule), say so first and give what the sources say.
8. If the question has several sides (civil and criminal, landlord and tenant…), answer each
   side the sources cover, and say which side they do not cover.
9. If the question is too vague or too broad to answer (one word, "every law"), set "status" to
   "clarify" and ask one short question back, suggesting two or three precise topics; cite
   nothing then.
10. When a source gives the date its text was last updated and the question is about what is in
   force or recent, mention that date, in the answer's language (never copy the English note).
{language}"""

ANSWER_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "status": {"type": "STRING", "enum": ["answered", "not_covered", "clarify"]},
        "answer": {"type": "STRING"},
        "used_sources": {"type": "ARRAY", "items": {"type": "INTEGER"}},
    },
    "required": ["status", "answer", "used_sources"],
}


LANGUAGE_NAMES = {
    "ar": "Modern Standard Arabic",
    "fr": "French",
    "darija-ar": "Moroccan Darija in Arabic letters",
    "darija-latn": "Moroccan Darija in Latin letters with digits (3 = ع, 7 = ح, 9 = ق)",
}

# ---------- analysis mode (decision 75): plan the research, then write in sections ----------

PLAN_SYSTEM = """You prepare the legal research on a person's situation under Moroccan law.
Do not answer. From the situation (and the conversation so far, if any), give:
- "situation": one sentence with the facts that matter, in {language};
- "searches": 2 to 4 short search queries in formal Arabic legal language, using the words a
  law would use (المكري، الإفراغ، الفصل التعسفي، النفقة…), one per legal question the situation
  raises (for example the duty of one side, the remedy of the other, a deadline, a penalty);
  when clauses from the person's document are given, up to 6 searches: one for each clause
  that may conflict with the law;
- "articles": up to 4 articles you believe apply, each as the law's usual Arabic name or number
  and the article number, for example "القانون الجنائي الفصل 124" or "القانون رقم 67.12 المادة
  10". They are only leads: each is looked up in the official text and read before use, so give
  none rather than guess;
- "missing": up to 3 facts not given that would change the answer, in {language}."""

PLAN_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "situation": {"type": "STRING"},
        "searches": {"type": "ARRAY", "items": {"type": "STRING"}},
        "articles": {"type": "ARRAY", "items": {"type": "STRING"}},
        "missing": {"type": "ARRAY", "items": {"type": "STRING"}},
    },
    "required": ["situation", "searches", "articles", "missing"],
}

ANALYSIS_SYSTEM = """You are Qanoun AI. You analyse a person's situation under Moroccan law.

Rules:
1. Use ONLY the numbered sources. Never use outside knowledge about the law.
2. Put the source number after every legal rule, like [2] or [1][3]; only numbers given.
3. Give the exact figures from the sources (durations, amounts, percentages, deadlines).
   Never compute a total yourself (no multiplying or adding days, amounts or durations):
   give the rule with the source's own figures; the person has calculators for totals.
4. If the question rests on a wrong premise, say so in "situation" and correct it with sources.
5. If the sources do not cover the situation at all, set "status" to "not_covered" and explain
   in "situation"; leave the other fields empty.
6. General legal information, not legal advice; recommend a lawyer for decisions with stakes.
7. When clauses from the person's document are given, check every one against the sources: in
   "application", say clause by clause which ones the law makes void or limits, and which the
   sources do not cover.

Write each field in {language}, 1 to 4 short sentences each (as many as needed in
"application" when document clauses are checked):
- "situation": the facts as you understood them;
- "law": what the law says on each question raised, with sources;
- "application": what it means for this person, and the conditions that would change it;
- "steps": what they can do, in order (who to notify, which court or office, deadlines);
- "missing": the facts that would change the answer, as short questions to the person;
- "deadlines": the time limits within which this person or the other party must act in this
  situation (to reply, to notify, to repair, to pay, to go to court, to wait before acting),
  counted from an event of the situation. Not durations that describe a status (the length of
  a trial period, the service needed to earn a right), and not limits for other categories of
  people than the one in the situation. Each with "what" (in {language}), "from_event" (from when it
  runs, in {language}), "amount" and "unit" (days, months, years or hours), "source" (its
  number) and "quote": the article's exact words that state it, copied character for character.
  None if no source sets one; never a time limit from memory.
{language_rule}"""

DEADLINE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "what": {"type": "STRING"},
        "from_event": {"type": "STRING"},
        "amount": {"type": "INTEGER"},
        "unit": {"type": "STRING", "enum": ["days", "months", "years", "hours"]},
        "source": {"type": "INTEGER"},
        "quote": {"type": "STRING"},
    },
    "required": ["what", "amount", "unit", "source", "quote"],
}

ANALYSIS_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "status": {"type": "STRING", "enum": ["answered", "not_covered"]},
        "situation": {"type": "STRING"},
        "law": {"type": "STRING"},
        "application": {"type": "STRING"},
        "steps": {"type": "STRING"},
        "missing": {"type": "STRING"},
        "used_sources": {"type": "ARRAY", "items": {"type": "INTEGER"}},
        "deadlines": {"type": "ARRAY", "items": DEADLINE_SCHEMA},
    },
    "required": ["status", "situation", "law", "application", "steps", "missing", "used_sources"],
}
SECTIONS = ("situation", "law", "application", "steps", "missing")

# ---------- conversation memory (decision 76) ----------

CONDENSE_SYSTEM = """Rewrite the person's last message as one standalone question that can be
understood without the conversation: bring in the facts and the subject from earlier turns. Keep
the same language and script as the last message. Reply with the question only."""


def conversation_block(history: Sequence[tuple[str, str]], limit: int = 400) -> str:
    """Earlier turns, answers shortened: enough to resolve "and if…?" follow-ups."""
    lines = []
    for question, answer in history:
        short = answer if len(answer) <= limit else answer[:limit] + "…"
        lines.append(f"Q: {question}\nA: {short}")
    return "\n\n".join(lines)


def plan_system(language: str) -> str:
    return PLAN_SYSTEM.format(language=LANGUAGE_NAMES.get(language, LANGUAGE_NAMES["fr"]))


def analysis_system(language: str) -> str:
    return ANALYSIS_SYSTEM.format(
        language=LANGUAGE_NAMES.get(language, LANGUAGE_NAMES["fr"]),
        language_rule=LANGUAGE_INSTRUCTIONS.get(language, LANGUAGE_INSTRUCTIONS["fr"]),
    )


def describe(article: Article) -> str:
    """How a source is introduced: law, article number, where it sits, and its text."""
    where = " > ".join(article.hierarchy)
    title = f" ({article.title})" if article.title else ""
    if article.consolidated_as_of:
        where += f"\n(text updated as of {article.consolidated_as_of})"
    elif article.version:
        where += f"\n(version published on Adala on {article.version})"
    heading = f"{article.law_title}, {article.label} {article.article_number}{title}"
    return f"{heading}\n{where}\n{article.text}"


def system_prompt(language: str) -> str:
    return SYSTEM.format(language=LANGUAGE_INSTRUCTIONS.get(language, LANGUAGE_INSTRUCTIONS["fr"]))


def user_prompt(
    question: str,
    sources: Sequence[Article],
    notes: Sequence[str] = (),
    history: Sequence[tuple[str, str]] = (),
) -> str:
    blocks = [f"[{n}] {describe(article)}" for n, article in enumerate(sources, start=1)]
    extra = ("\n\nNOTES\n" + "\n".join(f"- {n}" for n in notes)) if notes else ""
    talk = f"\n\nCONVERSATION SO FAR\n{conversation_block(history)}" if history else ""
    return "SOURCES\n\n" + "\n\n".join(blocks) + extra + talk + f"\n\nQUESTION\n{question}"
