"""Central configuration, read from environment variables or a .env file."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Storage
    data_dir: Path = Path("data/pdfs")          # where PDFs live
    chroma_dir: Path = Path("storage/chroma")   # persistent vector DB
    collection_name: str = "pdf_docs"

    # Chunking
    chunk_size: int = 800        # characters per chunk
    chunk_overlap: int = 150     # characters shared between neighbouring chunks

    # Retrieval
    top_k: int = 4
    min_score: float = 0.0       # drop chunks below this cosine similarity

    # Embeddings: "fastembed" (real semantic model, downloaded on first run)
    #             "hash" (offline keyword-style embedder, for tests / air-gapped use)
    embedding_backend: str = "fastembed"
    embedding_model: str = "BAAI/bge-small-en-v1.5"

    # LLM: "ollama" (fully local), "anthropic" (Claude API) or "none" (return retrieved text only)
    llm_provider: str = "ollama"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-5-5"
    max_tokens: int = 800


@lru_cache
def get_settings() -> Settings:
    return Settings()
