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
        'swelni w ghadi nchra7lek". Not classical Arabic in Latin letters. You may quote the '
        "legal term in Arabic in parentheses."
    ),
}

SYSTEM = """You are Qanoun AI, an assistant that explains Moroccan law to ordinary people.

Rules:
1. Use ONLY the numbered sources below. Never use outside knowledge about the law, even if you
   think you know the answer.
2. After every sentence that states a legal rule, put the number of the source it comes from,
   like [2] or [1][3]. Only use numbers of sources that are given.
3. Give the exact figures from the source (durations, ages, amounts, percentages).
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
   force or recent, mention that date.
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


def user_prompt(question: str, sources: Sequence[Article], notes: Sequence[str] = ()) -> str:
    blocks = [f"[{n}] {describe(article)}" for n, article in enumerate(sources, start=1)]
    extra = ("\n\nNOTES\n" + "\n".join(f"- {n}" for n in notes)) if notes else ""
    return "SOURCES\n\n" + "\n\n".join(blocks) + extra + f"\n\nQUESTION\n{question}"
