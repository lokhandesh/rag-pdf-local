"""Split page text into overlapping chunks, preferring paragraph/sentence boundaries."""
import re
from dataclasses import dataclass

from app.pdf_loader import Page


@dataclass
class Chunk:
    id: str
    text: str
    source: str
    page: int


_SEPARATORS = ["\n\n", "\n", ". ", " "]


def _split(text: str, size: int) -> list[str]:
    """Recursively split text into pieces no longer than `size`."""
    if len(text) <= size:
        return [text]
    for sep in _SEPARATORS:
        if sep in text:
            parts, buf = [], ""
            for piece in text.split(sep):
                candidate = f"{buf}{sep}{piece}" if buf else piece
                if len(candidate) <= size:
                    buf = candidate
                else:
                    if buf:
                        parts.append(buf)
                    buf = piece
            if buf:
                parts.append(buf)
            out = []
            for p in parts:
                out.extend(_split(p, size) if len(p) > size else [p])
            return out
    return [text[i:i + size] for i in range(0, len(text), size)]  # no separators at all


def chunk_pages(pages: list[Page], size: int = 800, overlap: int = 150) -> list[Chunk]:
    if overlap >= size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")
    chunks: list[Chunk] = []
    for page in pages:
        pieces = _split(page.text, size - overlap)
        for i, piece in enumerate(pieces):
            # prepend the tail of the previous piece so context isn't cut mid-thought
            if i > 0 and overlap:
                tail = pieces[i - 1][-overlap:]
                tail = tail[tail.find(" ") + 1:] if " " in tail else tail
                piece = f"{tail} {piece}"
            text = re.sub(r"\s+", " ", piece).strip()
            if text:
                chunks.append(Chunk(
                    id=f"{page.source}::p{page.page}::c{i}",
                    text=text, source=page.source, page=page.page,
                ))
    return chunks
