FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/models \
    FASTEMBED_CACHE_PATH=/models/fastembed

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

# Bake the embedding model into the image so the container works offline.
# Build with --build-arg PRELOAD_MODEL=false to skip (model then downloads on first use).
ARG PRELOAD_MODEL=true
ARG EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
RUN if [ "$PRELOAD_MODEL" = "true" ]; then \
      python -c "from fastembed import TextEmbedding; TextEmbedding('${EMBEDDING_MODEL}')"; \
    fi

COPY app ./app
COPY scripts ./scripts

RUN useradd -m -u 1000 rag && mkdir -p /app/data/pdfs /app/storage && chown -R rag /app /models
USER rag

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
