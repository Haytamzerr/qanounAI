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
import base64
import json
import logging
import re
import time
from collections.abc import Callable, Iterator, Sequence
from pathlib import Path
from typing import Protocol

import httpx

from qanoun.config import settings

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta"
MAX_OUTPUT_TOKENS = 8192  # the most a cut-off reply is retried with
log = logging.getLogger("qanoun.llm")


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
        """The model's reply. With `json_schema`, the reply is JSON following that schema.
        GeminiLLM also takes `attachments`: (mime type, bytes) pairs such as a photo."""
        ...


class GeminiLLM:
    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        temperature: float = 0.1,  # low: we want faithful answers, not creative ones
        max_output_tokens: int = 4096,  # Arabic analyses and documents need room (decision 90)
        client: httpx.Client | None = None,
        attempts: int = 3,
        sleep: Callable[[float], None] = time.sleep,
        timeout: float = 25,
        state_path: Path | None = None,
    ):
        key = api_key or (settings.llm_api_key and settings.llm_api_key.get_secret_value())
        if not key:
            raise LLMError("No API key: put QANOUN_LLM_API_KEY=... in the .env file.")
        # An overloaded model can hang for a minute before answering "busy"; a real answer takes
        # a few seconds. Giving up after `timeout` seconds moves on to a free model sooner.
        self.client = client or httpx.Client(timeout=httpx.Timeout(timeout, connect=10))
        self.headers = {"x-goog-api-key": key}
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.attempts = attempts
        self.sleep = sleep
        # Remembered between runs: the model that last answered, and the models refused with 404.
        self.state_path = state_path
        state = self._load_state()
        self._retired: set[str] = set(state.get("retired", []))  # listed but refused: never retried
        self._busy: set[str] = set()  # busy during this session: tried last
        self._fallbacks: list[str] | None = None  # listed only if the first model stays busy
        self.name = (
            model
            or settings.llm_fast_model
            or state.get("model")
            or pick_model([m for m in self.list_models() if m not in self._retired])
        )

    def list_models(self) -> list[str]:
        """Models this key can use to generate text, e.g. "gemini-2.5-flash"."""
        response = self._request("GET", f"{GEMINI_URL}/models", params={"pageSize": 1000})
        return [
            m["name"].removeprefix("models/")
            for m in response.get("models", [])
            if "generateContent" in m.get("supportedGenerationMethods", [])
        ]

    def generate(
        self,
        system: str,
        user: str,
        *,
        json_schema: dict | None = None,
        attachments: Sequence[tuple[str, bytes]] = (),
    ) -> str:
        """`attachments`: files the model reads with the text, e.g. ("image/jpeg", photo)."""
        config: dict = {
            "temperature": self.temperature,
            "maxOutputTokens": self.max_output_tokens,
        }
        if json_schema is not None:
            config |= {"responseMimeType": "application/json", "responseSchema": json_schema}
        body = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        *(
                            {
                                "inline_data": {
                                    "mime_type": mime,
                                    "data": base64.b64encode(data).decode(),
                                }
                            }
                            for mime, data in attachments
                        ),
                        {"text": user},
                    ],
                }
            ],  # fmt: skip
            "generationConfig": config,
        }
        response = self._generate_with_fallbacks(body)
        # A reply cut at the length limit is half a JSON object: ask again once with twice the
        # room (an Arabic contract with 8 clauses went past 2,048 tokens, decision 90).
        while (
            response.get("candidates", [{}])[0].get("finishReason") == "MAX_TOKENS"
            and config["maxOutputTokens"] < MAX_OUTPUT_TOKENS
        ):
            config["maxOutputTokens"] = min(config["maxOutputTokens"] * 2, MAX_OUTPUT_TOKENS)
            log.info(
                "reply cut at the length limit: asking again with %d", config["maxOutputTokens"]
            )
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
        """Try each model once, best first; only when all are busy, wait (2 s, then 4 s) and go
        round again. Waiting on one busy model while others are free wasted up to a minute.
        A model refused with 404 (listed, but "no longer available to new users") is skipped
        for good. Other errors (bad key…) stop at once."""
        last: LLMError | None = None
        for round_ in range(self.attempts):
            if round_:
                if not list(self._candidates()):
                    break  # every model was retired: waiting won't help
                self.sleep(2**round_)
            for model in self._candidates():
                url = f"{GEMINI_URL}/models/{model}:generateContent"
                start = time.perf_counter()
                try:
                    response = self._request("POST", url, json=body)
                except LLMError as error:
                    log.info("%s → %s (%.1f s)", model, error.status, time.perf_counter() - start)
                    if error.status == 404:
                        self._retired.add(model)
                        self._save_state()
                        continue
                    if not error.retryable:
                        raise
                    self._busy.add(model)
                    last = error
                    continue
                log.info("%s → ok (%.1f s)", model, time.perf_counter() - start)
                self._busy.discard(model)
                self.name = model  # keep using the model that answered
                self._save_state()
                return response
        if last is None:  # every model refused with 404
            raise LLMError("None of the listed Gemini models accepted the request (404).", 404)
        raise LLMError(f"All Gemini models are busy, try again later ({last})", 503)

    def _candidates(self) -> Iterator[str]:
        """Models to try, in order: the current one, then the others best first, and those that
        were busy earlier in this session last. Refused (404) models are left out. Lazy: the
        model list is fetched only when the current model fails."""
        seen: set[str] = set()

        def fresh(models):
            for m in models:
                if m not in seen and m not in self._retired:
                    seen.add(m)
                    yield m

        if self.name not in self._busy:
            yield from fresh([self.name])
        if self._fallbacks is None:
            self._fallbacks = rank_models(self.list_models())
        yield from fresh(m for m in self._fallbacks if m not in self._busy)
        yield from fresh([self.name, *self._fallbacks])  # the busy ones, last

    def _load_state(self) -> dict:
        if not self.state_path or not self.state_path.exists():
            return {}
        try:
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}  # a damaged cache is just ignored

    def _save_state(self) -> None:
        if not self.state_path:
            return
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        state = {"model": self.name, "retired": sorted(self._retired)}
        self.state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")

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


STATE_PATH = settings.data_dir / "cache" / "llm.json"  # git-ignored


def configure_logging() -> None:
    """Print one line per model attempt; hide httpx's own request lines."""
    logging.basicConfig(level=logging.INFO, format="  %(name)s: %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)


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
    configure_logging()
    llm = GeminiLLM(state_path=STATE_PATH)
    if args.list_models:
        print("\n".join(sorted(llm.list_models())))
        print("\norder of preference:", ", ".join(rank_models(llm.list_models())))
    print(f"\nmodel chosen: {llm.name}")
    reply = llm.generate("Reply in one short sentence.", "Say hello in Darija.")
    print(f"test reply from {llm.name}:", reply)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
