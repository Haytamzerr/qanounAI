from qanoun.generation.llm import LLMError
from qanoun.understanding.llm_rewrite import LLMRewriter
from qanoun.understanding.rewrite import understand


class FakeLLM:
    name = "fake"

    def __init__(self, reply="هل يجوز للمشغل فصل الأجير دون مبرر؟\n", fail=False):
        self.reply, self.fail, self.calls = reply, fail, 0

    def generate(self, system, user, *, json_schema=None):
        self.calls += 1
        if self.fail:
            raise LLMError("busy", 503)
        return self.reply


def test_darija_question_gets_the_formal_restatement():
    rewriter = LLMRewriter(FakeLLM())
    result = understand("wach y9d lmoudir yjri 3liya bla sabab?", rewriter=rewriter)
    assert result.rewritten == "هل يجوز للمشغل فصل الأجير دون مبرر؟"
    assert result.query.startswith("wach y9d")  # the original is kept
    assert result.query.endswith(result.rewritten)


def test_formal_questions_are_not_sent_to_the_model():
    llm = FakeLLM()
    for question in ("ما هي مدة فترة الاختبار؟", "Quelle est la durée du préavis ?"):
        assert understand(question, rewriter=LLMRewriter(llm)).query == question
    assert llm.calls == 0  # no cost, no delay


def test_same_question_is_rewritten_once():
    llm = FakeLLM()
    rewriter = LLMRewriter(llm)
    rewriter("chhal dyal lconji?")
    rewriter("chhal dyal lconji?")
    assert llm.calls == 1


def test_a_busy_model_does_not_block_the_search():
    llm = FakeLLM(fail=True)
    result = understand("tredouni mn lkhedma", rewriter=LLMRewriter(llm))
    assert result.rewritten is None
    assert "الفصل من الشغل" in result.query  # the lexicon still works


def test_only_the_first_line_is_kept():
    rewriter = LLMRewriter(FakeLLM(reply="سؤال رسمي؟\nشرح إضافي لا نريده"))
    assert rewriter("wach?") == "سؤال رسمي؟"
