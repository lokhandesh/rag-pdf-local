.PHONY: install sample ingest run test lint docker-build up pull-model down logs clean

PY ?= python

## --- Local (no Docker) ---
install:        ## create venv deps
	$(PY) -m pip install -r requirements-dev.txt

sample:         ## generate a sample PDF in data/pdfs
	$(PY) -m scripts.make_sample_pdf

ingest:         ## ingest all PDFs in data/pdfs
	$(PY) -m scripts.ingest

run:            ## start API + UI on http://localhost:8000
	$(PY) -m uvicorn app.main:app --reload --port 8000

test:           ## run tests (offline)
	$(PY) -m pytest -q

lint:
	$(PY) -m ruff check app scripts tests

## --- Docker ---
docker-build:
	docker build -t rag-pdf-local:latest .

up:             ## start API + Ollama
	docker compose up -d --build

pull-model:     ## download the Ollama model (first time)
	docker compose exec ollama ollama pull $${OLLAMA_MODEL:-llama3.2:3b}

down:
	docker compose down

logs:
	docker compose logs -f rag-api

clean:          ## wipe the local vector DB
	rm -rf storage
