"""Retrieval entry point: query text in, RetrievedItem list out.

Week 1 is vector search only. BM25, SQL collocation lookup and rerank are
added here later without changing the interface.
"""

import csv
from functools import lru_cache
from pathlib import Path

from retrieval.embedding import Embedder, build_embedder
from retrieval.store import MemoryStore, PostgresStore, Sentence, VectorStore
from shared.config import Settings, get_settings
from shared.schemas import RetrievedItem


def read_pairs(path: Path) -> list[Sentence]:
    """Read a TSV of: id, lang, text, translation (header row required)."""
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return [
            Sentence(
                id=int(row["id"]),
                lang=row["lang"],
                text=row["text"],
                translation=row.get("translation") or None,
            )
            for row in reader
        ]


class Retriever:
    def __init__(self, embedder: Embedder, store: VectorStore):
        self.embedder = embedder
        self.store = store

    def index(self, sentences: list[Sentence]) -> None:
        vectors = self.embedder.embed([s.embedding_text() for s in sentences])
        self.store.add(sentences, vectors)

    def search(self, query: str, k: int = 5) -> list[RetrievedItem]:
        [qvec] = self.embedder.embed([query])
        return [
            RetrievedItem(
                sentence_id=s.id,
                lang=s.lang,
                text=s.text,
                translation=s.translation,
                score=round(score, 4),
            )
            for s, score in self.store.search(qvec, k)
        ]


def build_retriever(settings: Settings) -> Retriever:
    embedder = build_embedder(settings)
    if settings.store == "memory":
        retriever = Retriever(embedder, MemoryStore())
        retriever.index(read_pairs(settings.sample_path))
        return retriever
    if settings.store == "postgres":
        return Retriever(embedder, PostgresStore(settings.database_url, settings.embedding_dim))
    raise ValueError(f"Unknown STORE: {settings.store}")


@lru_cache
def get_retriever() -> Retriever:
    return build_retriever(get_settings())
