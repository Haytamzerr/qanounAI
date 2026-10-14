"""Talk to a large language model (LLM).

The rest of the code only knows the small `LLM` interface: give a system prompt and a user
message, get text back. Today it is Google Gemini; another provider means one new class.

Gemini is called through its REST API with httpx rather than Google's SDK: one fewer dependency,
and every request is visible in the code. The API key comes from `.env` (QANOUN_LLM_API_KEY) and
is sent in a header, never in the URL, so it doesn't end up in logs.

Usage:
    uv run python -m qanoun.generation.llm --list-models   # models your key can use
"""

import argparse
import json
import re
import time
from collections.abc import Callable
from typing import Protocol

import httpx

from qanoun.config import settings

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta"


RETRYABLE = {429, 500, 502, 503, 504}  # busy or temporarily failing: worth trying again


class LLMError(RuntimeError):
    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status

    @property
    def retryable(self) -> bool:
        return self.status in RETRYABLE


class LLM(Protocol):
    name: str

    def generate(self, system: str, user: str, *, json_schema: dict | None = None) -> str:
        """The model's reply. With `json_schema`, the reply is JSON following that schema."""
        ...


class GeminiLLM:
    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        temperature: float = 0.1,  # low: we want faithful answers, not creative ones
        max_output_tokens: int = 1024,
        client: httpx.Client | None = None,
        attempts: int = 3,
        sleep: Callable[[float], None] = time.sleep,
    ):
        key = api_key or (settings.llm_api_key and settings.llm_api_key.get_secret_value())
        if not key:
            raise LLMError("No API key: put QANOUN_LLM_API_KEY=... in the .env file.")
        self.client = client or httpx.Client(timeout=60)
        self.headers = {"x-goog-api-key": key}
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.attempts = attempts
        self.sleep = sleep
        self.name = model or settings.llm_fast_model or pick_model(self.list_models())
        self._fallbacks: list[str] | None = None  # listed only if the first model stays busy

    def list_models(self) -> list[str]:
        """Models this key can use to generate text, e.g. "gemini-2.5-flash"."""
        response = self._request("GET", f"{GEMINI_URL}/models", params={"pageSize": 1000})
        return [
            m["name"].removeprefix("models/")
            for m in response.get("models", [])
            if "generateContent" in m.get("supportedGenerationMethods", [])
        ]

    def generate(self, system: str, user: str, *, json_schema: dict | None = None) -> str:
        config: dict = {
            "temperature": self.temperature,
            "maxOutputTokens": self.max_output_tokens,
        }
        if json_schema is not None:
            config |= {"responseMimeType": "application/json", "responseSchema": json_schema}
        body = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": config,
        }
        response = self._generate_with_fallbacks(body)
        try:
            candidate = response["candidates"][0]
            return "".join(part.get("text", "") for part in candidate["content"]["parts"])
        except (KeyError, IndexError) as error:
            reason = (
                response.get("promptFeedback", {}).get("blockReason") or json.dumps(response)[:300]
            )
            raise LLMError(f"Gemini returned no answer: {reason}") from error

    def _generate_with_fallbacks(self, body: dict) -> dict:
        """Try the chosen model, waiting longer between attempts while it is busy (2 s, 4 s…);
        if it stays busy, move on to the next model. Other errors (bad key…) stop at once."""
        model, tried = self.name, []
        while True:
            tried.append(model)
            url = f"{GEMINI_URL}/models/{model}:generateContent"
            for attempt in range(self.attempts):
                try:
                    response = self._request("POST", url, json=body)
                    self.name = model  # keep using the model that answered
                    return response
                except LLMError as error:
                    if not error.retryable:
                        raise
                    last = error
                    if attempt < self.attempts - 1:
                        self.sleep(2 ** (attempt + 1))
            if self._fallbacks is None:
                self._fallbacks = rank_models(self.list_models())
            remaining = [m for m in self._fallbacks if m not in tried]
            if not remaining:
                raise LLMError(f"All Gemini models are busy, try again later ({last})", 503)
            model = remaining[0]

    def _request(self, method: str, url: str, **kwargs) -> dict:
        try:
            response = self.client.request(method, url, headers=self.headers, **kwargs)
        except httpx.HTTPError as error:
            raise LLMError(f"Can't reach Gemini: {error}", status=503) from error
        if response.status_code != 200:
            try:
                message = response.json()["error"]["message"]
            except (ValueError, KeyError):
                message = response.text[:300]
            raise LLMError(f"Gemini error {response.status_code}: {message}", response.status_code)
        return response.json()


def rank_models(available: list[str]) -> list[str]:
    """Stable "flash" models, newest first, then stable "flash-lite" ones as a last resort.

    Google renames models often, so we choose from what the key can use rather than hard-coding
    a name. Previews and special-purpose variants (audio, image, TTS…) are skipped.
    """

    def version(model: str) -> float:
        return float(re.search(r"\d+(?:\.\d+)?", model).group())

    flash = [m for m in available if re.fullmatch(r"gemini-\d+(?:\.\d+)?-flash", m)]
    lite = [m for m in available if re.fullmatch(r"gemini-\d+(?:\.\d+)?-flash-lite", m)]
    return sorted(flash, key=version, reverse=True) + sorted(lite, key=version, reverse=True)


def pick_model(available: list[str]) -> str:
    """The newest stable "flash" model: fast and cheap, good enough to write from sources."""
    ranked = rank_models(available)
    if not ranked:
        raise LLMError(
            "No stable Gemini flash model found; set QANOUN_LLM_FAST_MODEL in .env to one of: "
            + ", ".join(available[:20])
        )
    return ranked[0]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check the LLM connection.")
    parser.add_argument("--list-models", action="store_true")
    args = parser.parse_args(argv)
    llm = GeminiLLM()
    if args.list_models:
        print("\n".join(sorted(llm.list_models())))
        print("\norder of preference:", ", ".join(rank_models(llm.list_models())))
    print(f"\nmodel chosen: {llm.name}")
    reply = llm.generate("Reply in one short sentence.", "Say hello in Darija.")
    print(f"test reply from {llm.name}:", reply)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
