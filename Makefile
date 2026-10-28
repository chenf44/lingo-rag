.PHONY: install test lint api web db-up load-sample tatoeba

install:          ## Python + frontend dependencies
	pip install -r requirements-dev.txt
	cd frontend && npm install

test:             ## Run the Python test suite (fake mode, no keys needed)
	pytest -q

lint:
	ruff check .

api:              ## Core API on http://localhost:8000
	uvicorn api.index:app --reload --port 8000

web:              ## Frontend on http://localhost:3000
	cd frontend && npm run dev

db-up:            ## Local Postgres + pgvector
	docker compose up -d

load-sample:      ## Embed the sample sentences into Postgres (needs STORE=postgres)
	python -m ingest.load --file data/sample/pairs.tsv

tatoeba:          ## Download Tatoeba and build data/pairs.tsv (1000 per language)
	python -m ingest.tatoeba --download --limit 1000
