"""Embedding providers.

The same provider and model must be used for ingestion and for queries,
otherwise the vectors are not comparable.
"""

import hashlib
import math
from typing import Protocol

import httpx

from shared.config import Settings


class Embedder(Protocol):
    dim: int

    def embed(self, texts: list[str]) -> list[list[float]]: ...


def _normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


class FakeEmbedder:
    """Deterministic, offline embedder for development and CI.

    Hashes character bigrams and trigrams into buckets. It only captures
    surface overlap (no real meaning), which is enough to exercise the
    pipeline end to end without an API key.
    """

    def __init__(self, dim: int = 256):
        self.dim = dim

    def _vector(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        s = text.lower()
        for n in (2, 3):
            for i in range(len(s) - n + 1):
                gram = s[i : i + n]
                if gram.strip():
                    h = int(hashlib.md5(gram.encode("utf-8")).hexdigest(), 16)
                    vec[h % self.dim] += 1.0
        return _normalize(vec)

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(t) for t in texts]


class OpenAICompatibleEmbedder:
    """Any provider exposing an OpenAI-style POST /embeddings endpoint."""

    def __init__(self, base_url: str, api_key: str, model: str, dim: int, batch_size: int = 64):
        if not (base_url and api_key and model):
            raise ValueError(
                "EMBEDDING_BASE_URL, EMBEDDING_API_KEY and EMBEDDING_MODEL must be set"
            )
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.dim = dim
        self.batch_size = batch_size

    def embed(self, texts: list[str]) -> list[list[float]]:
        out: list[list[float]] = []
        with httpx.Client(timeout=60) as client:
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i : i + self.batch_size]
                resp = client.post(
                    f"{self.base_url}/embeddings",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"model": self.model, "input": batch},
                )
                resp.raise_for_status()
                data = sorted(resp.json()["data"], key=lambda d: d["index"])
                for item in data:
                    vec = item["embedding"]
                    if len(vec) != self.dim:
                        raise ValueError(
                            f"Model returned dim {len(vec)}, but EMBEDDING_DIM={self.dim}"
                        )
                    out.append(_normalize(vec))
        return out


def build_embedder(settings: Settings) -> Embedder:
    if settings.embedding_provider == "fake":
        return FakeEmbedder(settings.embedding_dim)
    if settings.embedding_provider == "openai_compatible":
        return OpenAICompatibleEmbedder(
            settings.embedding_base_url,
            settings.embedding_api_key,
            settings.embedding_model,
            settings.embedding_dim,
        )
    raise ValueError(f"Unknown EMBEDDING_PROVIDER: {settings.embedding_provider}")
