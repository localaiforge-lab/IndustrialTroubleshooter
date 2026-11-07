"""LUMEEI AI Mind – RAG + web search + local Qwen GGUF (English in/out).

Flutter phone: Hu↔En on device. Web tester / Firebase: optional POST /v1/translate.
"""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .config import settings
from .embedder import Embedder
from .gt_translate import translate_text
from .llm import LocalLlm
from .plant_store import PlantStore
from .rag_store import RagStore
from . import web_search as ws

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("api")

rag: RagStore | None = None
llm: LocalLlm | None = None
plant: PlantStore | None = None
started_at = 0.0
_PLANT_UI = Path(__file__).resolve().parents[1] / "plant_console"


@asynccontextmanager
async def lifespan(_: FastAPI):
    global rag, llm, plant, started_at
    started_at = time.time()
    embedder = None
    try:
        log.info("Loading embedder from %s", settings.embedding_onnx)
        embedder = Embedder(settings.embedding_onnx, settings.embedding_vocab)
        log.info("Loading RAG materials from %s", settings.materials_dir)
        rag = RagStore(settings.materials_dir, embedder)
        log.info("Catalog: %s", rag.catalog)
    except Exception:
        log.exception("Curriculum RAG did not load; the plant library still starts")
        rag = None
    plant = PlantStore(settings.plant_dir, embedder)
    plant.load()
    llm = LocalLlm(
        settings.llm_model_path,
        n_ctx=settings.llm_n_ctx,
        n_threads=settings.llm_n_threads,
        max_tokens=settings.llm_max_tokens,
        temperature=settings.llm_temperature,
    )
    llm.load()
    yield


app = FastAPI(title="LUMEEI AI Mind", version="2.1.0", lifespan=lifespan)
origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    """Client sends English [question]; optional Hungarian for lexical boost."""

    question: str = Field(..., min_length=1, max_length=2000)
    hungarian_question: str | None = Field(default=None, alias="hungarianQuestion")
    document_id: str | None = Field(default=None, alias="documentId")

    model_config = {"populate_by_name": True}


class ChatDebug(BaseModel):
    english_question: str
    context: str
    search_terms: list[str]
    hits: list[dict[str, Any]]
    llm_ready: bool = False
    web_used: bool = False


class ChatResponse(BaseModel):
    """English answer – Flutter translates to Hungarian."""

    answer: str
    document_id: str | None = Field(default=None, alias="documentId")
    debug: ChatDebug | None = None

    model_config = {"populate_by_name": True}


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "uptimeSec": int(time.time() - started_at) if started_at else 0,
        "ragReady": rag is not None and bool(rag.catalog),
        "llmReady": bool(llm and llm.ready),
        "books": rag.catalog if rag else [],
        "plantReady": plant is not None,
        "plantDocuments": plant.summary()["documents"] if plant else 0,
    }


@app.get("/v1/books")
def books() -> dict[str, Any]:
    if rag is None:
        raise HTTPException(503, "RAG not ready")
    return {"books": rag.catalog}


class TranslateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)
    source: Literal["hu", "en", "auto"] = "auto"
    target: Literal["hu", "en"] = "en"


class TranslateResponse(BaseModel):
    text: str
    source: str
    target: str


@app.post("/v1/translate", response_model=TranslateResponse)
def translate(req: TranslateRequest) -> TranslateResponse:
    """Hu↔En for the Firebase / browser web tester (CORS-safe)."""
    raw = req.text.strip()
    if not raw:
        raise HTTPException(400, "Empty text")

    source = req.source
    target = req.target
    if source == "auto":
        # Heuristic: Hungarian diacritics / common words → hu, else en.
        hu_markers = set("áéíóöőúüűÁÉÍÓÖŐÚÜŰ")
        source = "hu" if any(c in hu_markers for c in raw) else "en"
    if source == target:
        return TranslateResponse(text=raw, source=source, target=target)

    out = translate_text(raw, source=source, target=target)
    return TranslateResponse(text=out, source=source, target=target)


@app.post("/v1/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    if rag is None or llm is None:
        raise HTTPException(503, "Service not ready")
    if not llm.ready:
        raise HTTPException(
            503,
            "LLM not loaded. Set LLM_MODEL_PATH to a Qwen2.5 GGUF "
            "(e.g. qwen2.5-1.5b-instruct-q4_k_m.gguf) and restart.",
        )

    english_q = req.question.strip()
    if not english_q:
        raise HTTPException(400, "Empty question")
    hungarian_q = (req.hungarian_question or "").strip()

    hits, context, terms = rag.retrieve(
        english_query=english_q,
        hungarian_query=hungarian_q or english_q,
        document_id=req.document_id,
    )

    web_used = False
    hits_extra = None
    # Same idea as the old mobile path: deepen with curriculum web search
    # when textbook RAG is thin.
    if len(hits) < 2 or not context.strip():
        web = ws.search_curriculum(english_q, hungarian_q)
        if web is not None:
            context = (
                f"[Internet (Hungarian curriculum)]\n{web.snippet.strip()}\n\n"
                f"{context}"
            ).strip()
            web_used = True
            hits_extra = {
                "id": "web::curriculum",
                "title": f"Internet: {web.title}",
                "score": round(web.score, 4),
                "text": web.snippet[:280],
            }

    english_answer = llm.generate(english_question=english_q, context=context)

    hit_payload = [
        {
            "id": h.chunk.id,
            "title": h.chunk.document_title,
            "score": round(h.score, 4),
            "text": h.chunk.text[:280],
        }
        for h in hits[:5]
    ]
    if hits_extra is not None:
        hit_payload.insert(0, hits_extra)

    return ChatResponse(
        answer=english_answer,
        documentId=req.document_id,
        debug=ChatDebug(
            english_question=english_q,
            context=context,
            search_terms=terms,
            hits=hit_payload,
            llm_ready=True,
            web_used=web_used,
        ),
    )


class PlantAsk(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)


def _plant() -> PlantStore:
    if plant is None:
        raise HTTPException(503, "A tudástár nem elérhető")
    return plant


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/plant/", status_code=302)


@app.get("/v1/plant/status")
def plant_status() -> dict[str, Any]:
    library = _plant().summary()
    library["answerMode"] = "model" if llm and llm.ready else "documents"
    return library


@app.get("/v1/plant/documents")
def plant_documents() -> dict[str, Any]:
    return {"documents": _plant().list_documents()}


@app.post("/v1/plant/documents")
async def plant_upload(
    files: list[UploadFile] = File(...),
    area: str = Form(""),
) -> dict[str, Any]:
    if not files:
        raise HTTPException(400, "Válasszon legalább egy fájlt.")
    payload: list[tuple[str, bytes]] = []
    for item in files:
        payload.append((item.filename or "dokumentum", await item.read()))
    try:
        results = _plant().ingest_many(payload, area=area)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"results": results, "library": _plant().summary()}


@app.delete("/v1/plant/documents/{document_id}")
def plant_delete(document_id: str) -> dict[str, Any]:
    if not _plant().delete(document_id):
        raise HTTPException(404, "Nincs ilyen dokumentum a tudástárban.")
    return {"ok": True, "library": _plant().summary()}


@app.post("/v1/plant/ask")
def plant_ask(req: PlantAsk) -> dict[str, Any]:
    question = req.question.strip()
    if not question:
        raise HTTPException(400, "Írja le a hibát vagy a kérdést.")
    model = None
    if llm is not None and llm.ready:
        model = llm.generate_plant
    return _plant().ask(question, answer_with_model=model)


if _PLANT_UI.is_dir():
    app.mount(
        "/plant",
        StaticFiles(directory=str(_PLANT_UI), html=True),
        name="plant-ui",
    )
