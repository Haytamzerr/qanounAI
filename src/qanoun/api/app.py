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
from typing import Annotated, Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from qanoun.generation.answer import Answer, Answerer, Turn
from qanoun.generation.llm import LLMError
from qanoun.ingestion.models import Article

STATIC = Path(__file__).parent / "static"


class TurnIn(BaseModel):
    """An earlier exchange of the same conversation, sent back by the interface."""

    question: str = Field(max_length=1000)
    answer: str = Field(max_length=4000)
    sources: list[str] = Field(default_factory=list, max_length=12)  # cited article ids


class AskRequest(BaseModel):
    question: str = Field(min_length=2, max_length=1000)
    mode: Literal["quick", "analysis"] = "quick"
    history: list[TurnIn] = Field(default_factory=list, max_length=8)
    # chosen in the situation builder: theme, role, when, goal (decision 81)
    facts: list[Annotated[str, Field(max_length=200)]] = Field(default_factory=list, max_length=6)

    def run(self, answerer: Answerer, on_step=None) -> Answer:
        turns = [Turn(t.question, t.answer, tuple(t.sources)) for t in self.history]
        return answerer.answer(
            self.question, on_step, mode=self.mode, history=turns, facts=self.facts
        )


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
    mode: str  # "quick" or "analysis"
    text: str
    sections: dict[str, str] | None  # analysis: situation, law, application, steps, missing
    plan: list[str]  # analysis: the searches that were run
    leads: list[str]  # analysis: articles the plan suggested, found in the official text
    deadlines: list[dict]  # analysis: time limits verified against their article (decision 82)
    standalone: str | None  # a follow-up as rewritten with the conversation
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
            question=a.question, language=a.language, status=a.status, mode=a.mode, text=a.text,
            sections=a.sections, plan=a.plan, leads=a.leads, standalone=a.standalone,
            deadlines=[d.as_dict() for d in a.deadlines],
            citations=[Citation.of(n, a.sources[n - 1]) for n in a.cited],
            verified=a.verified, problems=a.problems, sources=[s.id for s in a.sources],
            model=a.model, attempts=a.attempts, seconds=a.seconds,
        )  # fmt: skip


class CalculateRequest(BaseModel):
    tool: str = Field(max_length=40)
    inputs: dict[str, float | bool | str] = Field(default_factory=dict, max_length=8)


class LetterRequest(BaseModel):
    kind: Literal["notice", "complaint", "request"] = "notice"
    language: Literal["ar", "fr"] = "ar"
    story: str = Field(min_length=2, max_length=2000)
    facts: list[Annotated[str, Field(max_length=200)]] = Field(default_factory=list, max_length=6)
    analysis: dict[str, Annotated[str, Field(max_length=4000)]] = Field(default_factory=dict)
    sources: list[str] = Field(min_length=1, max_length=14)  # ids of the articles cited


class DocxRequest(BaseModel):
    subject: str = Field(max_length=500)
    recipient: str = Field(default="", max_length=500)
    body: str = Field(max_length=12000)
    language: Literal["ar", "fr"] = "ar"


class DocumentRequest(BaseModel):
    mime: str = Field(max_length=80)
    data: str = Field(max_length=11_500_000)  # base64 of at most 8 MB
    language: Literal["ar", "fr", "darija"] = "ar"


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

    @app.middleware("http")
    async def always_fresh_interface(request, call_next):
        """The page and its files are small: make the browser re-check them on every load, so
        an update (`git pull` + restart) shows at once instead of an old cached copy."""
        response = await call_next(request)
        if request.url.path == "/" or request.url.path.startswith("/static/"):
            response.headers["Cache-Control"] = "no-cache"
        return response

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
            answer = await run_in_threadpool(lambda: request.run(get_answerer()))
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
                answer = request.run(get_answerer(), on_step=push)
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

    # ---------- tools for the situation page (decisions 82–86) ----------

    @app.post("/calculate")
    def calculate(request: CalculateRequest) -> dict:
        """Run one legal calculator; the figures come from the articles listed in the result."""
        from dataclasses import asdict

        from qanoun.tools.calculators import CalculationError
        from qanoun.tools.calculators import calculate as run

        try:
            return asdict(run(request.tool, dict(request.inputs)))
        except CalculationError as error:
            raise HTTPException(422, str(error)) from error

    @app.post("/letter")
    async def letter(request: LetterRequest) -> dict:
        """Draft a notice, complaint or request from the situation and the articles cited."""
        from qanoun.generation.letters import write_letter

        found = get_articles()
        sources = [found[i] for i in request.sources if i in found][:8]
        if not sources:
            raise HTTPException(422, "none of the cited articles is known")
        try:
            written = await run_in_threadpool(
                lambda: write_letter(
                    get_answerer().llm, request.kind, request.language, request.story, sources,
                    request.facts, request.analysis,
                )
            )  # fmt: skip
        except LLMError as error:
            raise HTTPException(503, f"The language model is unavailable: {error}") from error
        return {**written.__dict__, "verified": written.verified}

    @app.post("/letter.docx")
    def letter_docx(request: DocxRequest) -> Response:
        from qanoun.generation.letter_docx import letter_docx as build

        content = build(request.subject, request.recipient, request.body, request.language)
        return Response(
            content,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": 'attachment; filename="qanoun-letter.docx"'},
        )

    @app.post("/read-document")
    async def read_document(request: DocumentRequest) -> dict:
        """Turn a contract, letter or judgment (PDF, photo) into the person's file."""
        import base64
        import binascii

        from qanoun.generation.documents import DocumentError
        from qanoun.generation.documents import read_document as read

        try:
            data = base64.b64decode(request.data, validate=True)
            reading = await run_in_threadpool(
                lambda: read(get_answerer().llm, request.mime, data, request.language)
            )
        except (DocumentError, binascii.Error) as error:
            raise HTTPException(422, str(error)) from error
        except LLMError as error:
            raise HTTPException(503, f"The language model is unavailable: {error}") from error
        return reading.as_dict()

    return app


def default_answerer() -> Answerer:
    """The real assistant: dense search (settings), Gemini, Arabizi rewrite."""
    from qanoun.generation.ask import RETRIEVERS, _articles, reference_resolver
    from qanoun.generation.llm import STATE_PATH, GeminiLLM
    from qanoun.understanding.llm_rewrite import LLMRewriter

    llm = GeminiLLM(state_path=STATE_PATH)
    return Answerer(
        RETRIEVERS["dense"](),
        llm,
        rewriter=LLMRewriter(llm),
        references=reference_resolver(),
        lookup=_articles().get,
    )
