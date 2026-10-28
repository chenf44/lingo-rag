# LingoRAG

A multilingual RAG language-learning assistant for native Chinese speakers
learning **English** and **Thai**. Ask in Chinese what you want to say, and get
natural expressions backed by **real example sentences**, with an explanation
that may only cite sentences it actually retrieved.

> Status: walking skeleton (Phase 1, week 1). Runs end to end in offline
> "fake" mode with no API keys.

## How it works

```
Query ──► embed ──► vector search (pgvector) ──► top-k example sentences
                                                     │
                     LLM (cites sentence ids only) ◄─┘
                                │
              validated answer: summary + explanation + example ids
```

One core API, several terminals:

| Phase | Terminal | Calls |
| --- | --- | --- |
| 1 | Web (Next.js) | `POST /api/ask` |
| 2 | Telegram bot | `/api/bot` webhook → `/api/ask` |
| 3 | Mobile app | `POST /api/ask` |

## Quick start (no keys, no database)

```bash
pip install -r requirements-dev.txt
make test                 # 8 tests, offline
make api                  # http://localhost:8000/api/health

cd frontend && npm install && cp .env.example .env.local
npm run dev               # http://localhost:3000
```

Try: `curl -X POST localhost:8000/api/ask -H 'content-type: application/json' -d '{"query":"改天我请你吃饭"}'`

## Switching to real providers

Copy `.env.example` to `.env` and set:

| Setting | Values |
| --- | --- |
| `STORE` | `memory` (sample data in RAM) or `postgres` (`DATABASE_URL`) |
| `EMBEDDING_PROVIDER` | `fake` or `openai_compatible` (+ base URL, key, model, `EMBEDDING_DIM`) |
| `LLM_PROVIDER` | `fake`, `anthropic` or `openai_compatible` (+ key, model) |

Load data into Postgres (local Docker or Neon):

```bash
make db-up                 # local pgvector, or point DATABASE_URL at Neon
make tatoeba               # builds data/pairs.tsv (1000 pairs per language)
STORE=postgres python -m ingest.load --file data/pairs.tsv
```

Use the same embedding provider and model for loading and for queries.

## Repo layout

```
api/          core API (FastAPI): /api/health, /api/ask
shared/       interface contract (schemas.py) and settings
retrieval/    embedding providers, vector stores, search
generation/   prompt, LLM providers, answer validation
ingest/       Tatoeba download, loading into Postgres
frontend/     Next.js web app (Phase 1 terminal)
data/sample/  small sample so everything runs offline
tests/        pytest suite (fake mode)
docs/plan.md  plan summary;  CLAUDE.md  rules for AI assistants
```

## Deployment (Vercel)

Two Vercel projects from this one repo:

1. **API** — root directory `/`. Uses `vercel.json` + `requirements.txt`; set
   the provider env vars and `ALLOWED_ORIGINS` (the frontend URL).
2. **Web** — root directory `frontend/`. Set `NEXT_PUBLIC_API_URL` to the API URL.

Database: Neon via the Vercel Marketplace (pgvector). Heavy work (downloads,
batch embedding) runs locally or on Colab, not on Vercel.

## Contributing

Branch → PR → review by the other owner → merge. See `CLAUDE.md` for ownership
and rules. CI runs lint, tests and the frontend build on every PR.

## Data attribution

Example sentences come from [Tatoeba](https://tatoeba.org) under CC BY 2.0 FR.
The sentences in `data/sample/pairs.tsv` were written for this project as
placeholder data.
