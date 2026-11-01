"""Extract text from PDFs page by page, keeping page numbers for citations."""
import re
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

from pypdf import PdfReader


@dataclass
class Page:
    source: str   # file name
    page: int     # 1-based page number
    text: str


def _clean(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"-\n(\w)", r"\1", text)      # re-join hyphenated line breaks
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def load_pdf(file: str | Path | BinaryIO, source: str | None = None) -> list[Page]:
    """Return one Page per PDF page that contains text.

    Scanned (image-only) PDFs return no pages: run OCR first (e.g. ocrmypdf).
    """
    if source is None:
        source = Path(file).name if isinstance(file, (str, Path)) else "upload.pdf"
    reader = PdfReader(file)
    pages = []
    for i, p in enumerate(reader.pages, start=1):
        text = _clean(p.extract_text() or "")
        if text:
            pages.append(Page(source=source, page=i, text=text))
    return pages
