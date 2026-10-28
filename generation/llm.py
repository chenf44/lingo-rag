"""LLM providers. Each returns the raw text of the model's reply."""

import json
from typing import Protocol

import httpx

from shared.config import Settings


class LLM(Protocol):
    def complete(self, system: str, user: str) -> str: ...


class FakeLLM:
    """Offline stand-in: cites the first three examples it was given.

    Lets the frontend and the API be developed and tested with no API key.
    """

    def complete(self, system: str, user: str) -> str:
        marker = "Example sentences (JSON):\n"
        examples = json.loads(user.split(marker, 1)[1]) if marker in user else []
        ids = [e["sentence_id"] for e in examples[:3]]
        lines = [f"- {e['text']}（{e.get('translation') or ''}）" for e in examples[:3]]
        return json.dumps(
            {
                "summary": f"离线模式：找到 {len(examples)} 条相关例句（未调用大模型）。",
                "explanation": "以下是检索到的前几条例句：\n" + "\n".join(lines),
                "examples": ids,
            },
            ensure_ascii=False,
        )


class AnthropicLLM:
    """Claude via the Anthropic Messages API."""

    def __init__(self, api_key: str, model: str, base_url: str = ""):
        if not (api_key and model):
            raise ValueError("LLM_API_KEY and LLM_MODEL must be set for LLM_PROVIDER=anthropic")
        self.api_key = api_key
        self.model = model
        self.base_url = (base_url or "https://api.anthropic.com").rstrip("/")

    def complete(self, system: str, user: str) -> str:
        resp = httpx.post(
            f"{self.base_url}/v1/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": self.model,
                "max_tokens": 1024,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            },
            timeout=60,
        )
        resp.raise_for_status()
        return "".join(b.get("text", "") for b in resp.json()["content"])


class OpenAICompatibleLLM:
    """Any provider exposing an OpenAI-style POST /chat/completions endpoint."""

    def __init__(self, base_url: str, api_key: str, model: str):
        if not (base_url and api_key and model):
            raise ValueError(
                "LLM_BASE_URL, LLM_API_KEY and LLM_MODEL must be set "
                "for LLM_PROVIDER=openai_compatible"
            )
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    def complete(self, system: str, user: str) -> str:
        resp = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


def build_llm(settings: Settings) -> LLM:
    if settings.llm_provider == "fake":
        return FakeLLM()
    if settings.llm_provider == "anthropic":
        return AnthropicLLM(settings.llm_api_key, settings.llm_model, settings.llm_base_url)
    if settings.llm_provider == "openai_compatible":
        return OpenAICompatibleLLM(settings.llm_base_url, settings.llm_api_key, settings.llm_model)
    raise ValueError(f"Unknown LLM_PROVIDER: {settings.llm_provider}")
