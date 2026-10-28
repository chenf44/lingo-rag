# LingoRAG plan (summary)

The full planning doc lives in Claude Docs and is shared between the two owners.
This file keeps the points the code depends on, so both AI assistants see them.

## Product

- **Target user:** native Chinese speakers learning English or Thai.
- **Core pain point (MVP):** "I want to say X — what is the natural way to say it,
  and is there real evidence?"
- **Differentiation:** for Chinese speakers, supports Thai, explains rather than
  only listing examples, and never invents examples.

## Phases

| Phase | Terminal | Purpose |
| --- | --- | --- |
| 1 | Web (Next.js on Vercel) | Run the full RAG flow, portfolio demo, evaluation |
| 2 | Telegram bot | Mobile, in-the-moment use ("check before I send") |
| 3 | Mobile app | Habits and monetization |

## Week 1 goal — walking skeleton

1000 English sentences with Chinese translations → embedding → Neon (pgvector)
→ Chinese query → vector search top 5 → LLM → web page shows explanation + examples.

Deliberately NOT in week 1: BM25, rerank, Thai at scale, collocation statistics,
mistake notebook, evaluation.

## Later (one at a time, each with a before/after check)

1. Hybrid retrieval: BM25 + vector (+ SQL collocation stats)
2. Rerank
3. Thai segmentation with PyThaiNLP (compare segmented vs not)
4. Collocation extraction with spaCy + PMI
5. Mistake notebook with a unified `user_id`
6. Evaluation: ~100 test queries, Hit@5 / MRR, citation accuracy

## Open decisions

- Who owns which area
- Embedding API provider (must support English, Chinese, Thai)
- LLM provider and how costs are shared
- Open-source license
