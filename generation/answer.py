"""Turn a query + retrieved examples into a validated Answer."""

import json
import re
from functools import lru_cache

from generation.llm import LLM, build_llm
from generation.prompt import (
    NO_EVIDENCE_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
    build_no_evidence_prompt,
    build_user_prompt,
)
from shared.config import get_settings
from shared.schemas import Answer, RetrievedItem

_JSON_OBJECT = re.compile(r"\{.*\}", re.DOTALL)
_FAILED = "抱歉，这次没能生成有效的回答。"


def parse_answer(raw: str, allowed_ids: set[int]) -> Answer:
    """Parse the model's JSON and drop any example id it was not given.

    This check is what stops the system from presenting invented examples.
    """
    failed = Answer(summary=_FAILED, explanation=raw.strip(), examples=[])
    match = _JSON_OBJECT.search(raw)
    if not match:
        return failed
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return failed

    cited = []
    for x in data.get("examples", []):
        try:
            sid = int(x)
        except (TypeError, ValueError):
            continue
        if sid in allowed_ids and sid not in cited:
            cited.append(sid)

    return Answer(
        summary=str(data.get("summary", "")).strip(),
        explanation=str(data.get("explanation", "")).strip(),
        examples=cited,
        grounded=bool(cited),
    )


def generate_answer(query: str, retrieved: list[RetrievedItem], llm: LLM) -> Answer:
    """Grounded answer when examples exist; otherwise an explicitly ungrounded one.

    grounded is derived from what was actually cited, never from the model's
    own claim, so an answer that cites nothing is always marked ungrounded.
    """
    if not retrieved:
        raw = llm.complete(NO_EVIDENCE_SYSTEM_PROMPT, build_no_evidence_prompt(query))
        return parse_answer(raw, allowed_ids=set())
    raw = llm.complete(SYSTEM_PROMPT, build_user_prompt(query, retrieved))
    return parse_answer(raw, {r.sentence_id for r in retrieved})


@lru_cache
def get_llm() -> LLM:
    return build_llm(get_settings())
