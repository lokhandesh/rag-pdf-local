"""CLI: ingest every PDF in a folder (default: data/pdfs) into the local vector DB.

    python -m scripts.ingest                 # ingest data/pdfs/*.pdf
    python -m scripts.ingest path/to/folder
    python -m scripts.ingest file.pdf
"""
import sys
import time
from pathlib import Path

from app.config import get_settings
from app.rag import get_pipeline


def main() -> None:
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else get_settings().data_dir
    rag = get_pipeline()
    files = [target] if target.is_file() else sorted(target.glob("*.pdf"))
    if not files:
        sys.exit(f"No PDFs found in {target}")
    start = time.time()
    for f in files:
        r = rag.ingest(f)
        note = f"  ⚠ {r['warning']}" if "warning" in r else ""
        print(f"{r['source']}: {r['pages']} pages -> {r['chunks']} chunks{note}")
    print(f"Done in {time.time() - start:.1f}s. Total chunks in DB: {rag.store.count()}")


if __name__ == "__main__":
    main()
