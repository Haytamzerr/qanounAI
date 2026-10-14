"""The Gemini client against a simulated API: no key, no network."""

import json

import httpx
import pytest

from qanoun.generation.llm import GeminiLLM, LLMError, pick_model

MODELS = {
    "models": [
        {"name": "models/gemini-2.5-flash", "supportedGenerationMethods": ["generateContent"]},
        {"name": "models/gemini-3.0-flash", "supportedGenerationMethods": ["generateContent"]},
        {"name": "models/gemini-3.5-flash-lite", "supportedGenerationMethods": ["generateContent"]},
        {
            "name": "models/gemini-4.0-flash-preview",
            "supportedGenerationMethods": ["generateContent"],
        },
        {"name": "models/text-embedding-004", "supportedGenerationMethods": ["embedContent"]},
    ]
}


def fake_gemini(requests: list[httpx.Request], reply: dict, status: int = 200):
    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path.endswith("/models"):
            return httpx.Response(200, json=MODELS)
        return httpx.Response(status, json=reply)

    return httpx.Client(transport=httpx.MockTransport(handler))


def reply(text: str) -> dict:
    return {"candidates": [{"content": {"parts": [{"text": text}]}}]}


def test_picks_newest_stable_flash_model():
    requests: list[httpx.Request] = []
    llm = GeminiLLM(api_key="secret", client=fake_gemini(requests, reply("")))
    assert llm.name == "gemini-3.0-flash"  # not the lite, preview or embedding models
    assert "text-embedding-004" not in llm.list_models()


def test_pick_model_explains_when_nothing_fits():
    with pytest.raises(LLMError, match="QANOUN_LLM_FAST_MODEL"):
        pick_model(["gemini-9-pro"])


def test_generate_sends_key_in_header_and_json_schema():
    requests: list[httpx.Request] = []
    llm = GeminiLLM("gemini-x", api_key="secret", client=fake_gemini(requests, reply('{"a": 1}')))
    assert llm.generate("system", "user", json_schema={"type": "OBJECT"}) == '{"a": 1}'
    sent = requests[-1]
    assert sent.headers["x-goog-api-key"] == "secret"
    assert "secret" not in str(sent.url)  # never in URLs, which end up in logs
    body = json.loads(sent.content)
    assert body["systemInstruction"]["parts"][0]["text"] == "system"
    assert body["generationConfig"]["responseMimeType"] == "application/json"


def test_api_errors_are_readable():
    error = {"error": {"message": "API key not valid"}}
    llm = GeminiLLM("gemini-x", api_key="bad", client=fake_gemini([], error, status=400))
    with pytest.raises(LLMError, match="400: API key not valid"):
        llm.generate("s", "u")


def test_blocked_prompt_is_reported():
    blocked = {"promptFeedback": {"blockReason": "SAFETY"}}
    llm = GeminiLLM("gemini-x", api_key="k", client=fake_gemini([], blocked))
    with pytest.raises(LLMError, match="SAFETY"):
        llm.generate("s", "u")


def test_missing_key_is_explained(monkeypatch):
    from qanoun.config import settings

    monkeypatch.setattr(settings, "llm_api_key", None)
    with pytest.raises(LLMError, match=r"\.env"):
        GeminiLLM("gemini-x")


def flaky_gemini(
    failures: dict[str, int], calls: list[str], status: int = 503, retired: tuple[str, ...] = ()
):
    """Each model fails `failures[model]` times with `status`, then answers; `retired` models
    always answer 404, like a model listed but no longer open to new users."""

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/models"):
            return httpx.Response(200, json=MODELS)
        model = request.url.path.split("/models/")[1].split(":")[0]
        calls.append(model)
        if model in retired:
            return httpx.Response(404, json={"error": {"message": "no longer available"}})
        if failures.get(model, 0) > 0:
            failures[model] -= 1
            return httpx.Response(status, json={"error": {"message": "high demand"}})
        return httpx.Response(200, json=reply(f"hello from {model}"))

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_busy_model_hands_over_to_the_next_without_waiting():
    calls, waits = [], []
    client = flaky_gemini({"gemini-3.0-flash": 99}, calls)
    llm = GeminiLLM(api_key="k", client=client, sleep=waits.append)
    assert llm.generate("s", "u") == "hello from gemini-2.5-flash"
    assert calls == ["gemini-3.0-flash", "gemini-2.5-flash"]
    assert waits == []
    assert llm.name == "gemini-2.5-flash"  # later questions go straight to the one that works
    llm.generate("s", "u")
    assert calls[-1] == "gemini-2.5-flash"


def test_waits_only_when_every_model_is_busy():
    calls, waits = [], []
    busy_once = {"gemini-3.0-flash": 1, "gemini-2.5-flash": 1, "gemini-3.5-flash-lite": 1}
    llm = GeminiLLM(api_key="k", client=flaky_gemini(busy_once, calls), sleep=waits.append)
    assert llm.generate("s", "u") == "hello from gemini-3.0-flash"
    assert len(calls) == 4 and waits == [2]  # one full round, one wait, then success


def test_all_busy_gives_a_clear_message():
    all_busy = {m: 99 for m in ("gemini-3.0-flash", "gemini-2.5-flash", "gemini-3.5-flash-lite")}
    waits = []
    llm = GeminiLLM(api_key="k", client=flaky_gemini(all_busy, []), sleep=waits.append)
    with pytest.raises(LLMError, match="All Gemini models are busy"):
        llm.generate("s", "u")
    assert waits == [2, 4]


def test_bad_key_is_not_retried():
    calls = []
    client = flaky_gemini({"gemini-x": 99}, calls, status=400)
    llm = GeminiLLM("gemini-x", api_key="bad", client=client, sleep=lambda s: None)
    with pytest.raises(LLMError, match="400"):
        llm.generate("s", "u")
    assert calls == ["gemini-x"]


def test_lite_models_are_the_last_resort():
    from qanoun.generation.llm import rank_models

    ranked = rank_models([m["name"].removeprefix("models/") for m in MODELS["models"]])
    assert ranked == ["gemini-3.0-flash", "gemini-2.5-flash", "gemini-3.5-flash-lite"]


def test_retired_model_is_skipped_for_good():
    calls = []
    client = flaky_gemini({"gemini-3.0-flash": 1}, calls, retired=("gemini-2.5-flash",))
    llm = GeminiLLM(api_key="k", client=client, sleep=lambda s: None)
    # 3.0 busy → 2.5 retired (404) → lite answers; no crash
    assert llm.generate("s", "u") == "hello from gemini-3.5-flash-lite"
    calls.clear()
    llm.name = "gemini-3.0-flash"
    llm.generate("s", "u")
    assert "gemini-2.5-flash" not in calls


def test_every_model_retired_is_explained():
    all_models = ("gemini-3.0-flash", "gemini-2.5-flash", "gemini-3.5-flash-lite")
    llm = GeminiLLM(api_key="k", client=flaky_gemini({}, [], retired=all_models))
    with pytest.raises(LLMError, match="404"):
        llm.generate("s", "u")


def test_replay_of_the_slow_answer_busy_models_are_not_retried_first():
    """2026-10-14: the first try fell back past two hanging models, then the retry of the same
    answer started again with those two models, adding 2 minutes."""
    calls = []
    client = flaky_gemini({"gemini-3.0-flash": 99}, calls)
    llm = GeminiLLM(api_key="k", client=client, sleep=lambda s: None)
    llm.generate("s", "first try")
    calls.clear()
    llm.generate("s", "retry")
    assert calls == ["gemini-2.5-flash"]  # straight to the model that worked


def test_busy_models_are_tried_after_the_free_ones():
    calls = []
    failures = {"gemini-3.0-flash": 99, "gemini-2.5-flash": 0}
    llm = GeminiLLM(api_key="k", client=flaky_gemini(failures, calls), sleep=lambda s: None)
    llm.generate("s", "u")  # 3.0 busy → 2.5
    failures["gemini-2.5-flash"] = 1
    calls.clear()
    llm.generate("s", "u")  # 2.5 busy now → the free lite model, not the busy 3.0
    assert calls == ["gemini-2.5-flash", "gemini-3.5-flash-lite"]


def test_a_hanging_model_counts_as_busy():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/models"):
            return httpx.Response(200, json=MODELS)
        model = request.url.path.split("/models/")[1].split(":")[0]
        calls.append(model)
        if model == "gemini-3.0-flash":
            raise httpx.ReadTimeout("no answer", request=request)
        return httpx.Response(200, json=reply("ok"))

    client = httpx.Client(transport=httpx.MockTransport(handler))
    llm = GeminiLLM(api_key="k", client=client, sleep=lambda s: None)
    assert llm.generate("s", "u") == "ok"
    assert calls == ["gemini-3.0-flash", "gemini-2.5-flash"]


def test_the_working_model_and_refused_ones_are_remembered(tmp_path):
    state = tmp_path / "llm.json"
    client = flaky_gemini({"gemini-3.0-flash": 99}, [], retired=("gemini-2.5-flash",))
    GeminiLLM(api_key="k", client=client, sleep=lambda s: None, state_path=state).generate("s", "u")
    saved = json.loads(state.read_text())
    assert saved == {"model": "gemini-3.5-flash-lite", "retired": ["gemini-2.5-flash"]}

    requests: list[httpx.Request] = []
    again = GeminiLLM(api_key="k", client=fake_gemini(requests, reply("hi")), state_path=state)
    assert again.name == "gemini-3.5-flash-lite"
    assert requests == []  # no need to list the models again


def test_a_damaged_state_file_is_ignored(tmp_path):
    state = tmp_path / "llm.json"
    state.write_text("not json")
    llm = GeminiLLM(api_key="k", client=fake_gemini([], reply("")), state_path=state)
    assert llm.name == "gemini-3.0-flash"
