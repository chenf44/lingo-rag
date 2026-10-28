"""Prompt construction. The LLM may only cite sentence ids it was given."""

import json

from shared.schemas import RetrievedItem

SYSTEM_PROMPT = """You are LingoRAG, a language coach for native Chinese speakers \
learning English or Thai.

Rules:
1. Base your answer ONLY on the example sentences provided. Do not invent examples.
2. Cite examples by their sentence_id. Never cite an id that is not in the list.
3. If the examples do not support a good answer, say so honestly in the summary.
4. Write the summary and explanation in the same language as the user's question.
5. Reply with a single JSON object and nothing else:
   {"summary": "<one sentence>", "explanation": "<a few short paragraphs>", \
"examples": [<sentence_id>, ...]}
"""


def build_user_prompt(query: str, retrieved: list[RetrievedItem]) -> str:
    examples = [
        {
            "sentence_id": r.sentence_id,
            "lang": r.lang,
            "text": r.text,
            "translation": r.translation,
        }
        for r in retrieved
    ]
    return (
        f"User question:\n{query}\n\n"
        f"Example sentences (JSON):\n{json.dumps(examples, ensure_ascii=False, indent=2)}"
    )
