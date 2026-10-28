# CLAUDE.md — rules for AI assistants working in this repo

Two people build LingoRAG, each with their own Claude. Read this file and
`docs/plan.md` before making changes, so both assistants follow the same rules.

## What this project is

A multilingual RAG language-learning assistant (English / Chinese / Thai).
Core question it answers: "I want to say X — what is the natural way to say it,
and is there real evidence?" Retrieval provides real example sentences; the LLM
explains them and may cite only retrieved sentence ids.

## Architecture (one core API, several terminals)

- `api/index.py` — the core API. Every terminal calls `POST /api/ask`.
- Phase 1: web (`frontend/`, Next.js on Vercel)
- Phase 2: Telegram bot (`/api/bot` webhook, not built yet)
- Phase 3: mobile app (calls `/api/ask` directly, not built yet)

## Ownership — only change your own area unless the PR says otherwise

| Area | Directories | Owner |
| --- | --- | --- |
| Data & retrieval | `ingest/`, `retrieval/`, `data/` | TBD |
| Generation & product | `generation/`, `api/`, `frontend/` | TBD |
| Shared contract | `shared/schemas.py` | both — changes need both to review |

## Rules

1. `shared/schemas.py` is the contract. If you change it, update
   `frontend/lib/api.ts` in the same PR and flag it in the PR description.
2. The API returns structured JSON only (summary + explanation + example ids).
   Terminals do their own formatting. Never return pre-formatted text for one terminal.
3. Never let generated examples through: `generation/answer.py::parse_answer`
   must keep dropping ids that were not retrieved.
4. Everything must keep working in fake mode (no keys, no DB):
   `STORE=memory`, `EMBEDDING_PROVIDER=fake`, `LLM_PROVIDER=fake`. CI runs this way.
5. Never commit secrets. Keys go in `.env` (git-ignored) or Vercel env vars.
   This repo is public.
6. Ingestion and model-heavy work run locally or on Colab, never on Vercel
   (function size and time limits).
7. Work on a branch, open a PR, let the other person review. No direct pushes to `main`.
8. Before opening a PR: `pytest -q` and `ruff check .` pass; `npm run build` passes
   if `frontend/` changed.
9. Keep the scope small: the walking skeleton first, improvements one at a time,
   each with a before/after check.

## Commands

```
make install      # deps
make test         # pytest (fake mode)
make api          # API on :8000
make web          # frontend on :3000
make db-up        # local Postgres + pgvector
make load-sample  # embed sample data into Postgres (STORE=postgres)
make tatoeba      # build data/pairs.tsv from Tatoeba
```
