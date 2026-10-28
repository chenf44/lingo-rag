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

### Prerequisites

- **Python 3.11 or newer.** macOS ships Python 3.9 as `python3`, which is too old.
  Install a newer one from [python.org](https://www.python.org/downloads/macos/)
  (or `brew install python@3.13`), then call it by its versioned name, e.g. `python3.14`.
  Do **not** use the `python3.14t` ("free-threaded") build; some dependencies do not
  install on it.
- **Node.js 20 or newer** for the frontend.

### First time

```bash
git clone https://github.com/chenf44/lingo-rag.git
cd lingo-rag

python3.14 -m venv .venv          # use the Python version you installed
source .venv/bin/activate         # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
make test                         # expect: 8 passed
```

Then run the API and the web app in **two terminal windows** (both keep running):

```bash
# Window 1 — API on http://localhost:8000
cd lingo-rag
source .venv/bin/activate
make api

# Window 2 — web app on http://localhost:3000
cd lingo-rag/frontend
npm install                       # first time only
cp .env.example .env.local        # first time only
npm run dev
```

Open http://localhost:3000 and click an example question. Stop either one with `Ctrl + C`.

### Every time after

Every new terminal needs the virtual environment activated before `make api`
or `make test` (otherwise `uvicorn` / `pytest` are "not found"):

```bash
cd lingo-rag && source .venv/bin/activate && make api      # window 1
cd lingo-rag/frontend && npm run dev                        # window 2
```

### Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `zsh: command not found: python` | macOS has no `python` command | Use `python3.14` (or your version) to create the venv; inside the venv, `python` works |
| `make: pytest: No such file or directory` | venv not created or not activated | `source .venv/bin/activate` (create it first if needed) |
| `make: No rule to make target '#'` | A pasted command included its `# comment`; zsh does not treat `#` as a comment by default | Paste only the command part |
| Web page shows "请求失败" / "Failed to fetch" | API is not running | Start window 1 (`make api`) |

Try the API directly: `curl -X POST localhost:8000/api/ask -H 'content-type: application/json' -d '{"query":"改天我请你吃饭"}'`

## Switching to real providers

Copy `.env.example` to `.env` and set:

| Setting | Values |
| --- | --- |
| `STORE` | `memory` (sample data in RAM) or `postgres` (`DATABASE_URL`) |
| `EMBEDDING_PROVIDER` | `fake` or `openai_compatible` (+ base URL, key, model, `EMBEDDING_DIM`) |
| `LLM_PROVIDER` | `fake`, `anthropic` or `openai_compatible` (+ key, model) |
| `MIN_RELEVANCE_SCORE` | Examples below this score are dropped. If none remain, the answer has `grounded: false` and the UI labels it "AI-generated, no real evidence". Re-tune per embedding model |

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
