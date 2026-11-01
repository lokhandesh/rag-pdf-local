# Local PDF RAG

Ask questions about your PDF documents. Everything runs on your machine: no cloud deployment needed.

```
PDF ─► extract text per page ─► chunk (800 chars, 150 overlap) ─► embed ─► Chroma (local disk)
                                                                              │
Question ─► embed ─► top-k similar chunks ─► prompt + LLM ─► answer with [file p.N] citations
```

| Part | Default | Alternatives (set in `.env`) |
|---|---|---|
| PDF parsing | pypdf | — (scanned PDFs need OCR first, e.g. `ocrmypdf`) |
| Embeddings | fastembed `BAAI/bge-small-en-v1.5` (CPU, no GPU needed) | `EMBEDDING_BACKEND=hash` for offline tests |
| Vector DB | Chroma, persisted in `storage/chroma` | — |
| LLM | Ollama `llama3.2:3b` (local, free) | `LLM_PROVIDER=anthropic` (Claude API) or `none` (retrieval only) |
| API + UI | FastAPI on http://localhost:8000 | — |

## Project layout

```
app/
  config.py        settings from env / .env
  pdf_loader.py    PDF -> pages (keeps page numbers)
  chunker.py       pages -> overlapping chunks
  embeddings.py    fastembed or hash embedder
  vectorstore.py   Chroma wrapper (add / search / delete by file)
  llm.py           Ollama, Claude or retrieval-only answer generation
  rag.py           the pipeline: ingest() and ask()
  main.py          FastAPI endpoints
  static/index.html  simple web UI (upload + ask)
scripts/
  ingest.py          CLI: ingest data/pdfs/*.pdf
  make_sample_pdf.py creates a sample handbook PDF for testing
tests/             offline tests (no model download, no LLM)
Dockerfile, docker-compose.yml, Makefile, .github/workflows/ci.yml
```

---

## Option A: Run with Docker (recommended)

Needs Docker Desktop (Windows/macOS) or Docker Engine (Linux).

```bash
cp .env.example .env                       # Windows: copy .env.example .env
docker compose up -d --build               # builds API image, starts API + Ollama
docker compose exec ollama ollama pull llama3.2:3b    # first time only (~2 GB)
```

Open **http://localhost:8000**, upload a PDF and ask a question.
Or drop PDFs into `data/pdfs/` and run `curl -X POST localhost:8000/ingest-folder`.

Stop with `docker compose down`. Your vector DB and model survive in Docker volumes.
Wipe everything with `docker compose down -v`.

**Using Claude instead of Ollama:** in `.env` set `LLM_PROVIDER=anthropic` and `ANTHROPIC_API_KEY=...`,
then `docker compose up -d --build rag-api` (Ollama isn't needed).

## Option B: Run without Docker

Needs Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate                  # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env                       # Windows: copy .env.example .env

python -m scripts.make_sample_pdf          # optional: creates data/pdfs/sample_company_handbook.pdf
python -m scripts.ingest                   # ingests data/pdfs/*.pdf (first run downloads the embedding model)
uvicorn app.main:app --reload              # http://localhost:8000
```

For answers you need an LLM: install Ollama from https://ollama.com and run `ollama pull llama3.2:3b`,
or set `LLM_PROVIDER=anthropic` + `ANTHROPIC_API_KEY`, or set `LLM_PROVIDER=none` to see retrieval only.

On macOS/Linux the Makefile has shortcuts: `make install sample ingest run test`.

## API

| Method | Path | What it does |
|---|---|---|
| GET | `/` | Web UI |
| GET | `/health` | Status, chunk count, active backends |
| POST | `/upload` | Upload one PDF (multipart field `file`); re-uploading the same name replaces it |
| POST | `/ingest-folder` | Ingest every PDF in `DATA_DIR` |
| GET | `/documents` | Indexed files and chunk counts |
| DELETE | `/documents/{name}` | Remove a file from the index |
| POST | `/ask` | `{"question": "...", "top_k": 4}` → answer + source passages |

Interactive API docs: http://localhost:8000/docs

```bash
curl -F "file=@mydoc.pdf" localhost:8000/upload
curl -X POST localhost:8000/ask -H "Content-Type: application/json" \
     -d '{"question": "How many days of annual leave do I get?"}'
```

## Testing

```bash
pytest -q          # 11 tests, fully offline (hash embeddings, no LLM, temp DB)
ruff check app scripts tests
```

**Quality check with the sample PDF** (after `make sample ingest run`): these should retrieve the page shown.

| Question | Expected page |
|---|---|
| How many days of annual leave do I get? | 1 (18 days) |
| How long is parental leave? | 1 (16 weeks primary) |
| Can I work from home? | 2 (up to 3 days/week) |
| What is the meal allowance when travelling? | 3 (SGD 80/day) |
| How do I report a lost laptop? | 4 (IT helpdesk within 24 h) |

The **"retrieved passages"** panel in the UI shows the score and page for each hit, which is the
quickest way to see whether a bad answer is a retrieval problem or an LLM problem.

## CI workflow (no deployment)

`.github/workflows/ci.yml` runs on every push / PR to GitHub:
lint → tests → build the Docker image → start it and hit `/health` → save the image as a
downloadable build artifact. Nothing is deployed anywhere.

## Tuning tips

- **Answers miss details** → raise `TOP_K` (6–8) or lower `CHUNK_SIZE` (500).
- **Answers cut mid-thought** → raise `CHUNK_OVERLAP`.
- **Irrelevant passages** → set `MIN_SCORE` (e.g. 0.3 with fastembed).
- **Better answers** → bigger Ollama model (`llama3.1:8b`, `qwen2.5:7b`) or `LLM_PROVIDER=anthropic`.
- **Changing the embedding model** creates a fresh collection automatically; re-run ingest.
- **Scanned PDFs** return 0 pages with a warning → run `ocrmypdf in.pdf out.pdf` first.
