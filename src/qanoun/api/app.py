"""The web service.

    uv run python -m qanoun.api          # then open http://127.0.0.1:8000/docs

- `POST /ask` → a checked answer with its cited articles in full
- `POST /ask/stream` → the same, with progress events first (Server-Sent Events)
- `GET /articles/{id}` → one article, to open a citation
- `GET /health` → is the service up, how many articles it knows
- `GET /` → the web interface (static/: plain HTML, CSS and JavaScript, no build step)

Answers are not streamed word by word on purpose: every citation is checked before anything is
shown (decision 56). The stream sends the steps instead ("understood", "sources", "writing"), so
the interface reacts within a second.
"""

import asyncio
import json
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from qanoun.generation.answer import Answer, Answerer
from qanoun.generation.llm import LLMError
from qanoun.ingestion.models import Article

STATIC = Path(__file__).parent / "static"


class AskRequest(BaseModel):
    question: str = Field(min_length=2, max_length=1000)


class Citation(BaseModel):
    number: int  # the [n] used in the answer text
    id: str
    law_number: str
    law_title: str
    article_number: str
    label: str  # "Article", "المادة" or "الفصل": how the law itself names its articles
    title: str | None
    hierarchy: list[str]
    text: str
    source_url: str
    official: bool  # the Arabic text published in the Bulletin officiel
    updated: str | None = None  # the date the text was last consolidated, when known

    @classmethod
    def of(cls, number: int, a: Article) -> "Citation":
        return cls(
            number=number, id=a.id, law_number=a.law_number, law_title=a.law_title,
            article_number=a.article_number, label=a.label, title=a.title,
            hierarchy=a.hierarchy, text=a.text,
            source_url=a.source_url, official=a.is_official_version,
            updated=a.version,
        )  # fmt: skip


class AnswerOut(BaseModel):
    question: str
    language: str
    status: str  # "answered", "not_covered" or "clarify"
    text: str
    citations: list[Citation]
    verified: bool
    problems: list[str]
    sources: list[str]  # every article given to the model
    model: str
    attempts: int
    seconds: dict[str, float]

    @classmethod
    def of(cls, a: Answer) -> "AnswerOut":
        return cls(
            question=a.question, language=a.language, status=a.status, text=a.text,
            citations=[Citation.of(n, a.sources[n - 1]) for n in a.cited],
            verified=a.verified, problems=a.problems, sources=[s.id for s in a.sources],
            model=a.model, attempts=a.attempts, seconds=a.seconds,
        )  # fmt: skip


def _sse(event: str, data: Any) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def create_app(
    answerer_factory: Callable[[], Answerer] | None = None,
    articles: dict[str, Article] | None = None,
) -> FastAPI:
    """`answerer_factory` builds the assistant on the first question (loading the model takes
    a few seconds); tests pass a fake one."""
    app = FastAPI(
        title="Qanoun AI", version="0.1.0", summary="Moroccan law, cited article by article"
    )
    state: dict[str, Any] = {"answerer": None}
    lock = threading.Lock()

    def get_articles() -> dict[str, Article]:
        if articles is not None:
            return articles
        from qanoun.generation.ask import _articles

        return _articles()

    def get_answerer() -> Answerer:
        with lock:  # two first requests at once must not load the model twice
            if state["answerer"] is None:
                state["answerer"] = (answerer_factory or default_answerer)()
            return state["answerer"]

    app.mount("/static", StaticFiles(directory=STATIC), name="static")

    @app.get("/", include_in_schema=False)
    def home() -> FileResponse:
        return FileResponse(STATIC / "index.html")

    @app.get("/health")
    def health() -> dict:
        articles = get_articles()
        laws = {a.law_number for a in articles.values()}
        return {"status": "ok", "articles": len(articles), "laws": len(laws)}

    @app.get("/articles/{article_id}")
    def article(article_id: str) -> Article:
        found = get_articles().get(article_id)
        if found is None:
            raise HTTPException(404, f"no article {article_id!r}")
        return found

    @app.post("/ask")
    async def ask(request: AskRequest) -> AnswerOut:
        try:
            answer = await run_in_threadpool(lambda: get_answerer().answer(request.question))
        except LLMError as error:
            raise HTTPException(503, f"The language model is unavailable: {error}") from error
        return AnswerOut.of(answer)

    @app.post("/ask/stream")
    async def ask_stream(request: AskRequest) -> StreamingResponse:
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue = asyncio.Queue()

        def push(event: str, data: Any) -> None:
            loop.call_soon_threadsafe(queue.put_nowait, (event, data))

        def work() -> None:
            try:
                answer = get_answerer().answer(request.question, on_step=push)
                push("answer", AnswerOut.of(answer).model_dump())
            except Exception as error:  # reported to the client instead of a broken stream
                push("error", {"message": f"{type(error).__name__}: {error}"})
            push("end", None)

        async def events():
            yield _sse("started", {"question": request.question})
            loop.run_in_executor(None, work)
            while True:
                event, data = await queue.get()
                if event == "end":
                    return
                yield _sse(event, data)

        return StreamingResponse(events(), media_type="text/event-stream")

    return app


def default_answerer() -> Answerer:
    """The real assistant: dense search (settings), Gemini, Arabizi rewrite."""
    from qanoun.generation.ask import RETRIEVERS, reference_resolver
    from qanoun.generation.llm import STATE_PATH, GeminiLLM
    from qanoun.understanding.llm_rewrite import LLMRewriter

    llm = GeminiLLM(state_path=STATE_PATH)
    return Answerer(
        RETRIEVERS["dense"](), llm, rewriter=LLMRewriter(llm), references=reference_resolver()
    )
