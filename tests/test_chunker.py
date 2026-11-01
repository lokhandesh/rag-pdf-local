import pytest

from app.chunker import chunk_pages
from app.pdf_loader import Page


def test_short_page_is_one_chunk():
    chunks = chunk_pages([Page("a.pdf", 1, "Hello world.")], size=200, overlap=20)
    assert len(chunks) == 1
    assert chunks[0].id == "a.pdf::p1::c0"
    assert chunks[0].page == 1


def test_long_page_is_split_with_overlap_and_size_limit():
    text = " ".join(f"Sentence number {i} about leave policy." for i in range(200))
    chunks = chunk_pages([Page("a.pdf", 3, text)], size=300, overlap=60)
    assert len(chunks) > 5
    assert all(len(c.text) <= 300 + 5 for c in chunks)
    # the start of chunk 2 should repeat words from the end of chunk 1
    assert chunks[1].text.split()[0] in chunks[0].text
    assert len({c.id for c in chunks}) == len(chunks)


def test_overlap_must_be_smaller_than_size():
    with pytest.raises(ValueError):
        chunk_pages([Page("a.pdf", 1, "x")], size=100, overlap=100)
