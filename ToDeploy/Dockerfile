# syntax=docker/dockerfile:1
# Self-contained LUMEEI AI Mind API image.
#
# Build (from this ToDeploy folder):
#   docker build -t lumeei-ai-mind-api .
#
# Run (LLM optional):
#   docker run --rm -p 8080:8080 lumeei-ai-mind-api
#   docker run --rm -p 8080:8080 \
#     -e LLM_MODEL_PATH=/app/models/model.gguf \
#     -v D:/models/qwen.gguf:/app/models/model.gguf:ro \
#     lumeei-ai-mind-api

FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-llm.txt ./
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install -r requirements-llm.txt

COPY app ./app
COPY plant_console ./plant_console
COPY data ./data
# Optional: bake GGUF into the image if present at build time.
COPY models ./models

ENV MATERIALS_DIR=/app/data/materials \
    EMBEDDING_ONNX=/app/data/embedding/model.onnx \
    EMBEDDING_VOCAB=/app/data/embedding/vocab.txt \
    LLM_MODEL_PATH=/app/models/qwen2.5-1.5b-instruct-q4_k_m.gguf

CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
