"""FastAPI service: upload PDFs, ask questions, simple web UI at /."""
import io
import logging
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.config import get_settings
from app.rag import get_pipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("rag")

app = FastAPI(title="Local PDF RAG", version="1.0.0")
STATIC = Path(__file__).parent / "static"
MAX_UPLOAD_MB = 50


class AskRequest(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=20)


@app.get("/")
def ui():
    return FileResponse(STATIC / "index.html")


@app.get("/health")
def health():
    s = get_settings()
    return {"status": "ok", "chunks": get_pipeline().store.count(),
            "embedding_backend": s.embedding_backend, "llm_provider": s.llm_provider}


@app.get("/documents")
def documents():
    return {"documents": get_pipeline().store.sources()}


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(400, "Only .pdf files are supported")
    data = await file.read()
    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(413, f"File larger than {MAX_UPLOAD_MB} MB")
    name = Path(file.filename).name
    # keep a copy so the folder can be re-ingested later
    s = get_settings()
    s.data_dir.mkdir(parents=True, exist_ok=True)
    (s.data_dir / name).write_bytes(data)
    try:
        result = get_pipeline().ingest(io.BytesIO(data), source=name)
    except Exception as e:  # corrupt / encrypted PDFs
        log.exception("ingest failed")
        raise HTTPException(422, f"Could not read PDF: {e}") from e
    log.info("ingested %s", result)
    return result


@app.post("/ingest-folder")
def ingest_folder():
    s = get_settings()
    return {"results": get_pipeline().ingest_folder(s.data_dir)}


@app.delete("/documents/{name}")
def delete_document(name: str):
    get_pipeline().store.delete_source(name)
    return {"deleted": name}


@app.post("/ask")
def ask(req: AskRequest):
    try:
        return get_pipeline().ask(req.question, req.top_k)
    except Exception as e:
        log.exception("ask failed")
        raise HTTPException(502, f"Answer generation failed: {e}") from e
