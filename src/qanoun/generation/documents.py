"""Read the person's document — a contract, a warning letter, a judgment — into their file (86).

People rarely know which facts matter; their documents hold them (dates, amounts, who signed,
the clause that is the problem). The document is turned into text, then the model extracts a
short situation in the person's words, the type of document, the key dates and amounts, and up to
five clauses worth a look, each with its exact quote.

- A PDF with a text layer is read here (PyMuPDF, already used for the laws): only text is sent,
  and every quoted clause is checked against that text; a clause not found is dropped.
- A photo or a scanned PDF has no text to check against: it is sent to the model as an image
  and its clauses are marked "read from an image" so the interface asks the person to compare.
- The situation is written without names, ID or phone numbers ("the landlord", "the employer"),
  because it becomes the question that is searched and stored in the browser history.
"""

import json
import logging
import re
from dataclasses import asdict, dataclass, field

from qanoun.generation.llm import LLM
from qanoun.retrieval.text import normalize

log = logging.getLogger("qanoun.documents")

MAX_BYTES = 8 * 1024 * 1024
MAX_TEXT = 15000  # characters of a long contract sent to the model
MIN_TEXT = 200  # fewer characters: a scanned PDF, read as an image
IMAGES = {"image/jpeg", "image/png", "image/webp", "image/heic"}
THEMES = ["work", "family", "home", "penal", "road", "consumer", "contract", "other"]
LANGUAGES = {"ar": "Modern Standard Arabic", "darija": "Moroccan Darija in Arabic letters",
             "fr": "French"}  # fmt: skip

READ_SYSTEM = """You help a person in Morocco understand a document they received or signed,
before they ask a lawyer-like assistant about it. Extract only what the document says:
- "kind": contract, warning_letter, judgment, receipt, official_notice or other;
- "summary": two sentences on what the document is and what it requires, in {language};
- "story": the person's situation as they would tell it, in the first person, in {language},
  at most 600 characters, built only from the document; refer to people by their role
  ("the landlord", "my employer") — never names, ID, phone numbers or addresses;
- "theme": the closest of {themes};
- "dates" and "amounts": the ones that matter, each with what it is;
- "clauses": up to five clauses worth checking (a deadline, a penalty, a waiver, a termination
  condition), each with its exact words in "quote", copied character for character, and what
  it means in plain {language} in "meaning".
Never add a fact that is not in the document. Never give legal advice here."""

READ_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "kind": {
            "type": "STRING",
            "enum": [
                "contract",
                "warning_letter",
                "judgment",
                "receipt",
                "official_notice",
                "other",
            ],
        },  # fmt: skip
        "summary": {"type": "STRING"},
        "story": {"type": "STRING"},
        "theme": {"type": "STRING", "enum": THEMES},
        "dates": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {"what": {"type": "STRING"}, "date": {"type": "STRING"}},
            },
        },  # fmt: skip
        "amounts": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {"what": {"type": "STRING"}, "amount": {"type": "STRING"}},
            },
        },  # fmt: skip
        "clauses": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {"quote": {"type": "STRING"}, "meaning": {"type": "STRING"}},
            },
        },  # fmt: skip
    },
    "required": ["kind", "summary", "story", "theme", "dates", "amounts", "clauses"],
}
PRIVATE = re.compile(
    r"(?:\+212|\b0)[5-7](?:[\s.-]?\d){8}\b|\b[A-Z]{1,2}\d{5,7}\b|[\w.+-]+@[\w-]+\.[\w.]+", re.I
)  # noqa: E501


class DocumentError(ValueError):
    """A file we cannot read: too big, empty, or of an unknown type."""


@dataclass
class Reading:
    kind: str
    summary: str
    story: str
    theme: str
    dates: list[dict] = field(default_factory=list)
    amounts: list[dict] = field(default_factory=list)
    clauses: list[dict] = field(default_factory=list)  # quote, meaning, checked (bool)
    read_as: str = "text"  # "text" (quotes checked) or "image" (to compare by eye)
    pages: int = 0

    def as_dict(self) -> dict:
        return asdict(self)


def pdf_text(data: bytes) -> tuple[str, int]:
    import pymupdf

    try:
        with pymupdf.open(stream=data, filetype="pdf") as pdf:
            return "\n".join(page.get_text() for page in pdf), pdf.page_count
    except Exception as error:  # a damaged or protected PDF
        raise DocumentError(f"this PDF cannot be opened ({error})") from error


def _flat(text: str) -> str:
    return " ".join(re.findall(r"[\w%-]+", normalize(text)))


def read_document(llm: LLM, mime: str, data: bytes, language: str = "ar") -> Reading:
    if not data:
        raise DocumentError("the file is empty")
    if len(data) > MAX_BYTES:
        raise DocumentError("the file is larger than 8 MB")
    text, pages, attachments = "", 0, []
    if mime == "application/pdf":
        text, pages = pdf_text(data)
        if len(text.strip()) < MIN_TEXT:  # scanned: no text layer, read the image
            text, attachments = "", [(mime, data)]
    elif mime in IMAGES:
        attachments = [(mime, data)]
    elif mime.startswith("text/"):
        text = data.decode("utf-8", errors="replace")
    else:
        raise DocumentError("send a PDF, a photo (JPEG, PNG, WebP) or a text file")
    system = READ_SYSTEM.format(
        language=LANGUAGES.get(language, LANGUAGES["ar"]), themes=", ".join(THEMES)
    )
    prompt = (
        f"DOCUMENT\n{text[:MAX_TEXT]}" if text else "DOCUMENT\n(the attached file)"
    ) + "\n\nExtract what the document says."
    kwargs = {"attachments": attachments} if attachments else {}
    raw = llm.generate(system, prompt, json_schema=READ_SCHEMA, **kwargs)
    try:
        data_out = json.loads(raw)
    except json.JSONDecodeError as error:
        raise DocumentError("the document could not be read, try a clearer photo") from error

    flat = _flat(text) if text else ""
    clauses = []
    for c in (data_out.get("clauses") or [])[:5]:
        quote, meaning = str(c.get("quote", "")).strip(), str(c.get("meaning", "")).strip()
        if not quote:
            continue
        checked = bool(text) and _flat(quote) in flat
        if text and not checked:
            log.info("clause dropped, not in the document: %s", quote[:80])
            continue
        clauses.append({"quote": quote, "meaning": meaning, "checked": checked})
    story = PRIVATE.sub("•••", str(data_out.get("story", "")).strip())[:800]
    theme = data_out.get("theme") if data_out.get("theme") in THEMES else "other"
    return Reading(
        kind=str(data_out.get("kind", "other")), summary=str(data_out.get("summary", "")).strip(),
        story=story, theme=theme, dates=list(data_out.get("dates") or [])[:8],
        amounts=list(data_out.get("amounts") or [])[:8], clauses=clauses,
        read_as="text" if text else "image", pages=pages,
    )  # fmt: skip
