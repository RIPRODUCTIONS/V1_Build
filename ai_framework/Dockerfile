# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements if exists
COPY ai_framework/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt || true

# Copy project
COPY ai_framework/ /app/

# Env defaults
ENV HOST=0.0.0.0 \
    PORT=8001 \
    ALLOWED_ORIGINS="http://localhost:8001,http://127.0.0.1:8001" \
    TRUSTED_HOSTS="*"

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -fsS http://127.0.0.1:8001/ready || exit 1

CMD ["python", "server.py"]





