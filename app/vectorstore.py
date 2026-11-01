"""Thin wrapper around a persistent local Chroma collection."""
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.chunker import Chunk


class VectorStore:
    def __init__(self, path: Path, collection: str, embedding_tag: str):
        path.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=str(path), settings=ChromaSettings(anonymized_telemetry=False)
        )
        # One collection per embedding model: vectors from different models aren't comparable.
        safe_tag = "".join(c if c.isalnum() else "_" for c in embedding_tag)[:40]
        self.col = self.client.get_or_create_collection(
            name=f"{collection}_{safe_tag}",
            embedding_function=None,                 # we always pass our own vectors
            metadata={"hnsw:space": "cosine"},
        )

    def delete_source(self, source: str) -> None:
        self.col.delete(where={"source": source})

    def add(self, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        for i in range(0, len(chunks), 500):     # batch to keep requests small
            batch, vecs = chunks[i:i + 500], vectors[i:i + 500]
            self.col.upsert(
                ids=[c.id for c in batch],
                documents=[c.text for c in batch],
                embeddings=vecs,
                metadatas=[{"source": c.source, "page": c.page} for c in batch],
            )

    def search(self, vector: list[float], k: int) -> list[dict]:
        if self.col.count() == 0:
            return []
        res = self.col.query(query_embeddings=[vector], n_results=min(k, self.col.count()))
        return [
            {"id": i, "text": d, "source": m["source"], "page": m["page"],
             "score": round(1 - dist, 4)}
            for i, d, m, dist in zip(res["ids"][0], res["documents"][0],
                                     res["metadatas"][0], res["distances"][0], strict=True)
        ]

    def sources(self) -> dict[str, int]:
        metas = self.col.get(include=["metadatas"])["metadatas"]
        counts: dict[str, int] = {}
        for m in metas:
            counts[m["source"]] = counts.get(m["source"], 0) + 1
        return dict(sorted(counts.items()))

    def count(self) -> int:
        return self.col.count()
