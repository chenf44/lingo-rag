"""Vector stores: an in-memory one for dev/CI and a Postgres + pgvector one."""

import math
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Sentence:
    id: int
    lang: str
    text: str
    translation: str | None = None

    def embedding_text(self) -> str:
        """Text that gets embedded: the sentence plus its translation.

        Including the translation lets a Chinese query match an English
        sentence through its Chinese translation, even with the fake embedder.
        """
        return f"{self.text} | {self.translation}" if self.translation else self.text


class VectorStore(Protocol):
    def add(self, sentences: list[Sentence], vectors: list[list[float]]) -> None: ...

    def search(self, vector: list[float], k: int) -> list[tuple[Sentence, float]]: ...

    def count(self) -> int: ...


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


class MemoryStore:
    def __init__(self) -> None:
        self._rows: list[tuple[Sentence, list[float]]] = []

    def add(self, sentences: list[Sentence], vectors: list[list[float]]) -> None:
        self._rows.extend(zip(sentences, vectors, strict=True))

    def search(self, vector: list[float], k: int) -> list[tuple[Sentence, float]]:
        scored = [(s, _cosine(vector, v)) for s, v in self._rows]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]

    def count(self) -> int:
        return len(self._rows)


def _vec_literal(vec: list[float]) -> str:
    return "[" + ",".join(f"{v:.6f}" for v in vec) + "]"


class PostgresStore:
    """Postgres + pgvector. Works with local Docker and with Neon."""

    def __init__(self, database_url: str, dim: int):
        if not database_url:
            raise ValueError("DATABASE_URL must be set when STORE=postgres")
        import psycopg  # imported lazily so memory mode needs no DB driver

        self._psycopg = psycopg
        self.database_url = database_url
        self.dim = dim

    def _connect(self):
        return self._psycopg.connect(self.database_url)

    def init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS sentences (
                    id           BIGINT PRIMARY KEY,
                    lang         TEXT NOT NULL,
                    text         TEXT NOT NULL,
                    translation  TEXT,
                    embedding    vector({self.dim}) NOT NULL
                )
                """
            )

    def add(self, sentences: list[Sentence], vectors: list[list[float]]) -> None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO sentences (id, lang, text, translation, embedding)
                VALUES (%s, %s, %s, %s, %s::vector)
                ON CONFLICT (id) DO UPDATE SET
                    lang = EXCLUDED.lang, text = EXCLUDED.text,
                    translation = EXCLUDED.translation, embedding = EXCLUDED.embedding
                """,
                [
                    (s.id, s.lang, s.text, s.translation, _vec_literal(v))
                    for s, v in zip(sentences, vectors, strict=True)
                ],
            )

    def search(self, vector: list[float], k: int) -> list[tuple[Sentence, float]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, lang, text, translation, 1 - (embedding <=> %s::vector) AS score
                FROM sentences
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (_vec_literal(vector), _vec_literal(vector), k),
            ).fetchall()
        return [(Sentence(r[0], r[1], r[2], r[3]), float(r[4])) for r in rows]

    def count(self) -> int:
        with self._connect() as conn:
            return conn.execute("SELECT count(*) FROM sentences").fetchone()[0]
