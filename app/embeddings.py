"""Embedding backends.

fastembed: a real semantic embedding model (ONNX, CPU-only, no PyTorch). The model
           (~130 MB) is downloaded from Hugging Face on first use and cached.
hash:      deterministic word/bigram hashing. No download, no semantics — good for
           tests, CI and offline smoke tests, not for real-quality retrieval.
"""
import hashlib
import itertools
import math
import re
from functools import lru_cache
from typing import Protocol


class Embedder(Protocol):
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    def embed_query(self, text: str) -> list[float]: ...


class FastEmbedEmbedder:
    def __init__(self, model_name: str):
        from fastembed import TextEmbedding
        self.model = TextEmbedding(model_name=model_name)

    def embed_documents(self, texts):
        return [v.tolist() for v in self.model.embed(texts)]

    def embed_query(self, text):
        return next(iter(self.model.query_embed(text))).tolist()


class HashEmbedder:
    def __init__(self, dim: int = 1024):
        self.dim = dim

    @staticmethod
    def _stem(w: str) -> str:
        for suf in ("ing", "ed", "es", "s"):
            if w.endswith(suf) and len(w) - len(suf) >= 3:
                return w[: -len(suf)]
        return w

    def _vec(self, text: str) -> list[float]:
        words = [self._stem(w) for w in re.findall(r"[a-z0-9]+", text.lower())]
        tokens = words + [f"{a}_{b}" for a, b in itertools.pairwise(words)]
        v = [0.0] * self.dim
        for t in tokens:
            h = int(hashlib.md5(t.encode()).hexdigest(), 16)
            v[h % self.dim] += 1.0 if (h >> 64) & 1 else -1.0
        n = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / n for x in v]

    def embed_documents(self, texts):
        return [self._vec(t) for t in texts]

    def embed_query(self, text):
        return self._vec(text)


@lru_cache
def get_embedder(backend: str, model_name: str) -> Embedder:
    if backend == "fastembed":
        return FastEmbedEmbedder(model_name)
    if backend == "hash":
        return HashEmbedder()
    raise ValueError(f"Unknown EMBEDDING_BACKEND: {backend!r} (use 'fastembed' or 'hash')")
