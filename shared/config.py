"""Runtime settings, read from environment variables (and a local .env file).

Every provider defaults to "fake", so the whole pipeline runs with no API
keys and no database. Switch to real providers by editing .env locally or
the Vercel project's environment variables.
"""

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


@dataclass(frozen=True)
class Settings:
    # Storage: "memory" loads data/sample at startup; "postgres" uses DATABASE_URL.
    store: str
    database_url: str
    sample_path: Path

    # Embedding: "fake" (deterministic, offline) or "openai_compatible".
    embedding_provider: str
    embedding_base_url: str
    embedding_api_key: str
    embedding_model: str
    embedding_dim: int

    # LLM: "fake", "anthropic" or "openai_compatible".
    llm_provider: str
    llm_base_url: str
    llm_api_key: str
    llm_model: str

    # Comma-separated origins allowed to call the API from a browser.
    allowed_origins: list[str]


@lru_cache
def get_settings() -> Settings:
    return Settings(
        store=_env("STORE", "memory"),
        database_url=_env("DATABASE_URL"),
        sample_path=ROOT / _env("SAMPLE_PATH", "data/sample/pairs.tsv"),
        embedding_provider=_env("EMBEDDING_PROVIDER", "fake"),
        embedding_base_url=_env("EMBEDDING_BASE_URL"),
        embedding_api_key=_env("EMBEDDING_API_KEY"),
        embedding_model=_env("EMBEDDING_MODEL"),
        embedding_dim=int(_env("EMBEDDING_DIM", "256")),
        llm_provider=_env("LLM_PROVIDER", "fake"),
        llm_base_url=_env("LLM_BASE_URL"),
        llm_api_key=_env("LLM_API_KEY"),
        llm_model=_env("LLM_MODEL"),
        allowed_origins=[
            o.strip()
            for o in _env("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
            if o.strip()
        ],
    )
