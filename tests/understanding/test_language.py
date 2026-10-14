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


# French questions that must stay French (reported: "2ans" made a French question Arabizi, so the
# answer came back in Darija). Numbers glued to units are ordinary French.
FRENCH = """Mon employeur peut-il me licencier sans motif ?
Combien de jours de congé par an ?
Que doit le mari à son épouse après un divorce ?
En combien de temps le vendeur doit-il me rembourser ?
Puis-je m'opposer à l'utilisation de mes données ?
J'ai un CDD de 2ans, est-ce que je peux démissionner ?
Quelle est la durée du préavis si je démissionne après 3ans ?
mon patron ne me paye pas depuis 2mois, que faire ?
Est-ce que la femme peut travailler la nuit ?
Je travaille 48h par semaine, c'est légal ?
quel est l'age minimum pour se marier au maroc ?
Ma femme veut divorcer, est-ce qu'elle garde les enfants ?
J'ai acheté un téléphone en ligne à 300dh, je peux le retourner ?
Le 2e alinéa de l'article 9 s'applique à moi ?
Je travaille depuis 5ans, combien d'indemnité si on me licencie ?
c'est quoi la periode d'essai pour un cadre ?
j'ai été licencié hier sans préavis, j'ai droit à quoi ?
Le congé de maternité dure 14 semaines ou plus ?
Mon mari veut prendre une 2ème femme, il a le droit ?""".splitlines()


@pytest.mark.parametrize("question", FRENCH)
def test_french_stays_french(question):
    assert detect_language(question) == "fr"


def test_every_held_out_arabizi_question_is_still_arabizi():
    with (EVAL_DIR / "darija_holdout.jsonl").open(encoding="utf-8") as f:
        questions = [json.loads(line)["question"] for line in f]
    assert [q for q in questions if detect_language(q) != "darija-latn"] == []
