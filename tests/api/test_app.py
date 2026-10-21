"""The web service with a fake assistant: no model, no key, no network."""

import json

from fastapi.testclient import TestClient

from qanoun.api.app import create_app
from qanoun.generation.answer import Answerer
from qanoun.generation.llm import LLMError

from ..generation.test_answer import ScriptedLLM, ok
from ..retrieval.test_search import ARTICLES

ARTICLE_MAP = {a.id: a for a in ARTICLES}


def client_with(*replies) -> TestClient:
    llm = ScriptedLLM(*replies)
    answerer = Answerer(lambda query, k: ARTICLES[:k], llm, k=3)
    return TestClient(create_app(lambda: answerer, ARTICLE_MAP))


def test_health_and_articles():
    client = client_with()
    health = client.get("/health").json()
    assert (health["status"], health["articles"]) == ("ok", 4)
    assert health["laws"] >= 1
    article = client.get("/articles/loi-65-99-ar-art-231").json()
    assert article["article_number"] == "231"
    assert client.get("/articles/nope").status_code == 404


def test_ask_returns_the_cited_articles_in_full():
    client = client_with(ok("Tu as droit à 1,5 jour par mois [2].", used=[2]))
    body = client.post("/ask", json={"question": "Combien de jours de congé ?"}).json()
    assert body["status"] == "answered" and body["verified"]
    assert body["language"] == "fr"
    [citation] = body["citations"]
    assert citation["number"] == 2 and citation["article_number"] == "231"
    assert citation["text"].startswith("العطلة") and citation["official"]
    assert len(body["sources"]) == 3


def test_question_is_validated():
    client = client_with()
    assert client.post("/ask", json={"question": ""}).status_code == 422
    assert client.post("/ask", json={"question": "x" * 1001}).status_code == 422


def test_model_down_is_a_503_with_a_reason():
    class Down(ScriptedLLM):
        def generate(self, system, user, *, json_schema=None):
            raise LLMError("All Gemini models are busy", 503)

    answerer = Answerer(lambda q, k: ARTICLES[:k], Down())
    client = TestClient(create_app(lambda: answerer, ARTICLE_MAP))
    response = client.post("/ask", json={"question": "Question ?"})
    assert response.status_code == 503 and "busy" in response.json()["detail"]


def parse_sse(text: str) -> list[tuple[str, object]]:
    events = []
    for block in text.strip().split("\n\n"):
        lines = dict(line.split(": ", 1) for line in block.splitlines())
        events.append((lines["event"], json.loads(lines["data"])))
    return events


def test_stream_sends_steps_then_the_checked_answer():
    client = client_with(ok("Réponse [1].", used=[1]))
    with client.stream("POST", "/ask/stream", json={"question": "Période d'essai ?"}) as r:
        assert r.headers["content-type"].startswith("text/event-stream")
        events = parse_sse(r.read().decode())
    names = [name for name, _ in events]
    assert names == ["started", "understood", "sources", "writing", "answer"]
    assert events[-1][1]["citations"][0]["article_number"] == "13"


def test_stream_reports_errors_instead_of_breaking():
    class Boom(ScriptedLLM):
        def generate(self, system, user, *, json_schema=None):
            raise RuntimeError("boom")

    answerer = Answerer(lambda q, k: ARTICLES[:k], Boom())
    client = TestClient(create_app(lambda: answerer, ARTICLE_MAP))
    with client.stream("POST", "/ask/stream", json={"question": "Question ?"}) as r:
        events = parse_sse(r.read().decode())
    assert events[-1] == ("error", {"message": "RuntimeError: boom"})


def test_the_assistant_is_built_once():
    built = []

    def factory():
        built.append(1)
        return Answerer(lambda q, k: ARTICLES[:k], ScriptedLLM(ok("A [1]."), ok("B [1].")))

    client = TestClient(create_app(factory, ARTICLE_MAP))
    client.post("/ask", json={"question": "Un ?"})
    client.post("/ask", json={"question": "Deux ?"})
    assert built == [1]


def test_the_interface_is_served():
    client = client_with()
    page = client.get("/")
    assert page.status_code == 200 and "Qanoun AI" in page.text
    assert client.get("/static/app.js").status_code == 200
    assert client.get("/static/app.css").status_code == 200


def test_citations_carry_the_word_and_the_version_of_the_text():
    from qanoun.api.app import Citation

    article = ARTICLES[0].model_copy(
        update={
            "article_word": "الفصل",
            "source_url": "https://adala.justice.gov.ma/api/uploads/2026/07/28/x.pdf",
        }
    )
    citation = Citation.of(1, article)
    assert (citation.label, citation.updated) == ("الفصل", "2026-07-28")


def test_ask_accepts_a_mode_and_the_conversation():
    plan = {"situation": "s", "searches": ["الأجير"], "missing": []}
    sections = {
        "status": "answered", "situation": "s", "law": "Règle [1].", "application": "a",
        "steps": "e", "missing": "", "used_sources": [1],
    }  # fmt: skip
    client = client_with("Question complète ?", plan, sections)
    body = {
        "question": "Et si ?",
        "mode": "analysis",
        "history": [{"question": "Q1 ?", "answer": "R1 [1].", "sources": [ARTICLES[0].id]}],
    }
    out = client.post("/ask", json=body).json()
    assert out["mode"] == "analysis" and out["sections"]["law"] == "Règle [1]."
    assert out["plan"] == ["الأجير"] and out["standalone"] == "Question complète ?"


def test_stream_reports_the_plan():
    plan = {"situation": "s", "searches": ["الأجير", "العطلة"], "missing": []}
    sections = {
        "status": "answered", "situation": "s", "law": "Règle [1].", "application": "a",
        "steps": "e", "missing": "", "used_sources": [1],
    }  # fmt: skip
    client = client_with(plan, sections)
    text = client.post("/ask/stream", json={"question": "Ma situation ?", "mode": "analysis"}).text
    assert "event: planned" in text and "العطلة" in text


def test_the_interface_is_never_served_stale():
    client = client_with()
    assert client.get("/").headers["cache-control"] == "no-cache"
    assert client.get("/static/app.js").headers["cache-control"] == "no-cache"


def test_ask_accepts_what_the_person_selected_and_limits_it():
    plan = {"situation": "s", "searches": ["الأجير"], "missing": []}
    sections = {
        "status": "answered", "situation": "s", "law": "Règle [1].", "application": "a",
        "steps": "1) Écrire. 2) Attendre.", "missing": "", "used_sources": [1],
    }  # fmt: skip
    client = client_with(plan, sections)
    body = {"question": "On m'a licencié.", "mode": "analysis", "facts": ["Sujet: Travail"]}
    assert client.post("/ask", json=body).status_code == 200
    too_many = dict(body, facts=["x"] * 7)
    assert client.post("/ask", json=too_many).status_code == 422
    too_long = dict(body, facts=["x" * 201])
    assert client.post("/ask", json=too_long).status_code == 422


def test_the_interface_has_the_situation_page():
    page = client_with().get("/").text
    assert 'href="#situation"' in page and 'id="builder"' in page and 'id="dossier"' in page


def test_calculate_endpoint():
    client = client_with()
    out = client.post(
        "/calculate",
        json={"tool": "abusive_dismissal", "inputs": {"years": 7, "monthly_wage": 5000}},
    ).json()
    assert out["value"] == 52500 and "loi-65-99-ar-art-41" in out["articles"]
    assert client.post("/calculate", json={"tool": "nope", "inputs": {}}).status_code == 422


def test_letter_endpoints():
    reply = {
        "subject": "طلب",
        "recipient": "[المشغل]",
        "body": "طبقا للمادة 231 من مدونة الشغل.",
        "used_sources": [1],
    }
    client = client_with(reply)
    body = {
        "kind": "request",
        "language": "ar",
        "story": "بغيت الكونجي",
        "sources": ["loi-65-99-ar-art-231"],
    }
    out = client.post("/letter", json=body).json()
    assert out["verified"] and out["cited"] == ["loi-65-99-ar-art-231"]
    assert client.post("/letter", json=dict(body, sources=["nope"])).status_code == 422
    docx = client.post("/letter.docx", json={"subject": "s", "body": "b", "language": "fr"})
    assert docx.status_code == 200 and docx.content[:2] == b"PK"


def test_read_document_endpoint():
    import base64

    reading = {
        "kind": "receipt",
        "summary": "s",
        "story": "خلصت الكرا",
        "theme": "home",
        "dates": [],
        "amounts": [],
        "clauses": [],
    }
    client = client_with(reading)
    data = base64.b64encode(b"\x89PNG photo").decode()
    out = client.post("/read-document", json={"mime": "image/png", "data": data}).json()
    assert out["kind"] == "receipt" and out["read_as"] == "image"
    assert (
        client.post("/read-document", json={"mime": "image/png", "data": "@@@"}).status_code == 422
    )


def test_the_interface_has_the_situation_tools():
    client = client_with()
    page, script = client.get("/").text, client.get("/static/app.js").text
    assert 'id="doc-input"' in page and 'id="tools"' in page and 'id="listen"' in page
    for name in ("SCENARIOS", "deadlinesTool", "calculatorsTool", "letterTool", "downloadIcs"):
        assert name in script


def test_ask_accepts_document_clauses_within_limits():
    plan = {"situation": "s", "searches": ["الأجير"], "missing": []}
    sections = {
        "status": "answered", "situation": "s", "law": "Règle [1].", "application": "a",
        "steps": "e", "missing": "", "used_sources": [1],
    }  # fmt: skip
    client = client_with(plan, sections)
    body = {"question": "Mon contrat.", "mode": "analysis", "document": ["Clause 1.", "Clause 2."]}
    assert client.post("/ask", json=body).status_code == 200
    assert client.post("/ask", json=dict(body, document=["c"] * 9)).status_code == 422
    assert client.post("/ask", json=dict(body, document=["c" * 401])).status_code == 422
