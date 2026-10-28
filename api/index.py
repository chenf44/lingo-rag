"""Core API. Every terminal (web, Telegram bot, mobile app) calls POST /api/ask.

Run locally:  uvicorn api.index:app --reload --port 8000
"""

import sys
from pathlib import Path

# Make the repo-root packages (shared, retrieval, generation) importable
# both locally and on Vercel, where this file is the function entry point.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from generation.answer import generate_answer, get_llm  # noqa: E402
from retrieval.search import get_retriever  # noqa: E402
from shared.config import get_settings  # noqa: E402
from shared.schemas import AskRequest, AskResponse  # noqa: E402

settings = get_settings()

app = FastAPI(title="LingoRAG API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "store": settings.store,
        "embedding_provider": settings.embedding_provider,
        "llm_provider": settings.llm_provider,
        "min_relevance_score": settings.min_relevance_score,
    }


@app.post("/api/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    retrieved = get_retriever().search(
        req.query, k=req.top_k, min_score=settings.min_relevance_score
    )
    answer = generate_answer(req.query, retrieved, get_llm())
    return AskResponse(answer=answer, retrieved=retrieved)
