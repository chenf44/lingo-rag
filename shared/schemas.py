"""Interface contract shared by every module and every terminal.

Change this file only through a PR that both owners review: retrieval,
generation, the API and the frontend all depend on these shapes.
"""

from typing import Literal

from pydantic import BaseModel, Field

Lang = Literal["en", "zh", "th"]
Channel = Literal["web", "telegram", "app"]


class RetrievedItem(BaseModel):
    """One example sentence returned by retrieval."""

    sentence_id: int
    lang: Lang
    text: str
    translation: str | None = None
    score: float = Field(description="Similarity score, higher is more relevant")


class Answer(BaseModel):
    """What the LLM produces, after validation."""

    summary: str = Field(description="One-line conclusion; the bot shows only this")
    explanation: str = Field(description="Full explanation; the web page shows this")
    examples: list[int] = Field(
        default_factory=list,
        description="sentence_ids cited; must be a subset of the retrieved ids",
    )
    grounded: bool = Field(
        default=False,
        description=(
            "True only when the answer cites at least one retrieved example. "
            "False means no real example supported it: terminals must label it "
            "as AI-generated without evidence."
        ),
    )


class AskRequest(BaseModel):
    user_id: str = Field(default="anonymous", description="Unified user id across terminals")
    channel: Channel = "web"
    query: str = Field(min_length=1, max_length=500)
    top_k: int = Field(default=5, ge=1, le=20)


class AskResponse(BaseModel):
    answer: Answer
    retrieved: list[RetrievedItem]
