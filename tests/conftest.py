import os
from pathlib import Path

import pytest
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


@pytest.fixture(scope="session", autouse=True)
def test_env(tmp_path_factory):
    """Run tests fully offline: hash embeddings, no LLM, throwaway DB."""
    tmp = tmp_path_factory.mktemp("rag")
    os.environ.update({
        "EMBEDDING_BACKEND": "hash",
        "LLM_PROVIDER": "none",
        "CHROMA_DIR": str(tmp / "chroma"),
        "DATA_DIR": str(tmp / "pdfs"),
    })
    from app.config import get_settings
    from app.rag import get_pipeline
    get_settings.cache_clear()
    get_pipeline.cache_clear()
    yield tmp


@pytest.fixture
def make_pdf(tmp_path):
    def _make(name: str, pages: list[str]) -> Path:
        path = tmp_path / name
        c = canvas.Canvas(str(path), pagesize=A4)
        for text in pages:
            y = 800
            for line in text.split("\n"):
                c.drawString(50, y, line)
                y -= 16
            c.showPage()
        c.save()
        return path
    return _make
