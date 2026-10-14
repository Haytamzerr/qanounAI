from qanoun.understanding.lexicon import find_terms, load_lexicon
from qanoun.understanding.rewrite import understand


def test_lexicon_loads_and_every_row_is_complete():
    lexicon = load_lexicon()
    assert len(lexicon) >= 50
    assert all(entry.legal_ar and entry.darija_ar and entry.legal_fr for entry in lexicon)


def test_arabizi_and_arabic_script_find_the_same_term():
    def labels(text):
        return {e.legal_fr for e in find_terms(text)}

    assert "licenciement" in labels("tredouni mn lkhedma")
    assert "licenciement" in labels("طردوني من الخدمة")
    assert "employeur" in labels("lpatron ma bghach")


def test_glued_prepositions_and_endings():
    assert {e.legal_fr for e in find_terms("flkhdma dyali")} == {"travail"}


def test_formal_questions_are_searched_unchanged():
    for question in ("ما هي مدة فترة الاختبار؟", "Quelle est la durée du préavis ?"):
        result = understand(question)
        assert result.query == question
        assert result.terms == []


def test_arabizi_question_gets_script_and_legal_terms():
    result = understand("tredouni mn lkhedma bla préavis, wach 3ndi l7e9?")
    assert result.language == "darija-latn"
    assert "الخدمة" in result.arabic_script
    assert {"الفصل من الشغل", "أجل الإخطار"} <= set(result.legal_terms)
    assert result.query.startswith("tredouni")  # the original is kept


def test_parts_can_be_switched_off():
    question = "tredouni mn lkhedma"
    assert understand(question, use_lexicon=False).terms == []
    assert understand(question, use_arabizi=False).arabic_script is None
