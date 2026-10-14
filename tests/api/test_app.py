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
    assert client.get("/health").json() == {"status": "ok", "articles": 4}
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
