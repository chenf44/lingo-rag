"""Turn a query + retrieved examples into a validated Answer."""

import json
import re
from functools import lru_cache

from generation.llm import LLM, build_llm
from generation.prompt import SYSTEM_PROMPT, build_user_prompt
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
    )


def generate_answer(query: str, retrieved: list[RetrievedItem], llm: LLM) -> Answer:
    if not retrieved:
        return Answer(summary="没有找到相关例句。", explanation="", examples=[])
    raw = llm.complete(SYSTEM_PROMPT, build_user_prompt(query, retrieved))
    return parse_answer(raw, {r.sentence_id for r in retrieved})


@lru_cache
def get_llm() -> LLM:
    return build_llm(get_settings())
