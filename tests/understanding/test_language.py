import json

import pytest

from qanoun.retrieval.evaluate import EVAL_DIR
from qanoun.understanding.language import detect_language


@pytest.mark.parametrize(
    ("question", "language"),
    [
        ("ما هي مدة فترة الاختبار في عقد الشغل غير محدد المدة؟", "ar"),
        ("شحال من ساعة خاصني نخدم فالسيمانة؟", "darija-ar"),
        ("Quelle est la durée du préavis en cas de démission ?", "fr"),
        ("Fin du contrat de travail : quelles indemnités ?", "fr"),  # "fin" is French too
        ("3ndi l7e9 f lconji?", "darija-latn"),  # digits used as letters
        ("wach lpatron y9der yjrini?", "darija-latn"),
        ("wach khasni nkhdem nhar l7ad", "darija-latn"),
    ],
)
def test_examples(question, language):
    assert detect_language(question) == language


def test_every_labelled_question():
    with (EVAL_DIR / "retrieval_set.jsonl").open(encoding="utf-8") as f:
        questions = [json.loads(line) for line in f]
    wrong = [q["id"] for q in questions if detect_language(q["question"]) != q["language"]]
    assert wrong == []
