"""A letter as a Word file, right-to-left for Arabic (decision 84).

python-docx has no switch for right-to-left text, so each paragraph gets Word's own markers
(<w:bidi/> on the paragraph, <w:rtl/> on its text): without them Word shows Arabic sentences with
the punctuation on the wrong side.
"""

from io import BytesIO

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt

LABELS = {
    "ar": {
        "to": "إلى",
        "subject": "الموضوع",
        "draft": "مسودة أعدها قانون AI: راجعها وأكمل ما بين معقوفين قبل التوقيع.",
    },
    "fr": {
        "to": "À",
        "subject": "Objet",
        "draft": "Brouillon préparé par Qanoun AI : relisez-le et complétez les crochets "
        "avant de signer.",
    },
}


def _rtl(paragraph) -> None:
    paragraph.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    paragraph._p.get_or_add_pPr().append(OxmlElement("w:bidi"))
    for run in paragraph.runs:
        run._r.get_or_add_rPr().append(OxmlElement("w:rtl"))
        fonts = run._r.get_or_add_rPr().get_or_add_rFonts()
        fonts.set(qn("w:cs"), "Arial")


def letter_docx(subject: str, recipient: str, body: str, language: str) -> bytes:
    labels = LABELS["ar" if language == "ar" else "fr"]
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name, style.font.size = "Arial", Pt(12)

    def add(text: str, bold: bool = False, size: int | None = None, italic: bool = False):
        p = doc.add_paragraph()
        run = p.add_run(text)
        run.bold, run.italic = bold, italic
        if size:
            run.font.size = Pt(size)
        if language == "ar":
            _rtl(p)
        return p

    add(labels["draft"], italic=True, size=9)
    if recipient:
        add(f"{labels['to']}: {recipient}", bold=True)
    add(f"{labels['subject']}: {subject}", bold=True)
    for block in body.split("\n"):
        add(block)
    out = BytesIO()
    doc.save(out)
    return out.getvalue()
