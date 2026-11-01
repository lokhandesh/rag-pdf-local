"""The RAG pipeline: ingest PDFs and answer questions."""
from functools import lru_cache
from pathlib import Path
from typing import BinaryIO

from app.chunker import chunk_pages
from app.config import Settings, get_settings
from app.embeddings import get_embedder
from app.llm import generate
from app.pdf_loader import load_pdf
from app.vectorstore import VectorStore


class RAGPipeline:
    def __init__(self, settings: Settings):
        self.s = settings
        self.embedder = get_embedder(settings.embedding_backend, settings.embedding_model)
        tag = "hash" if settings.embedding_backend == "hash" else settings.embedding_model
        self.store = VectorStore(settings.chroma_dir, settings.collection_name, tag)

    def ingest(self, file: str | Path | BinaryIO, source: str | None = None) -> dict:
        name = source or (Path(file).name if isinstance(file, (str, Path)) else "upload.pdf")
        pages = load_pdf(file, name)
        if not pages:
            return {"source": name, "pages": 0, "chunks": 0,
                    "warning": "No extractable text (scanned PDF? run OCR first)"}
        chunks = chunk_pages(pages, self.s.chunk_size, self.s.chunk_overlap)
        vectors = self.embedder.embed_documents([c.text for c in chunks])
        self.store.delete_source(name)        # re-ingesting a file replaces it
        self.store.add(chunks, vectors)
        return {"source": name, "pages": len(pages), "chunks": len(chunks)}

    def ingest_folder(self, folder: Path) -> list[dict]:
        return [self.ingest(p) for p in sorted(folder.glob("*.pdf"))]

    def retrieve(self, question: str, k: int | None = None) -> list[dict]:
        hits = self.store.search(self.embedder.embed_query(question), k or self.s.top_k)
        return [h for h in hits if h["score"] >= self.s.min_score]

    def ask(self, question: str, k: int | None = None) -> dict:
        hits = self.retrieve(question, k)
        answer = generate(question, hits, self.s)
        return {"question": question, "answer": answer, "sources": hits}


@lru_cache
def get_pipeline() -> RAGPipeline:
    return RAGPipeline(get_settings())
