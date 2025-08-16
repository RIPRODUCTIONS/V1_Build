# syntax=docker/dockerfile:1

# Development stage
FROM python:3.11-slim as development

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements if exists
COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt || true

# Copy project
COPY . /app/

# Env defaults
ENV HOST=0.0.0.0 \
    PORT=8001 \
    ALLOWED_ORIGINS="http://localhost:8001,http://127.0.0.1:8001" \
    TRUSTED_HOSTS="*"

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -fsS http://127.0.0.1:8001/ready || exit 1

CMD ["python", "server.py"]

# Production stage
FROM python:3.11-slim as production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    NODE_ENV=production

WORKDIR /app

# System deps for production
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

# Create non-root user for security
RUN groupadd -r ai_user && useradd -r -g ai_user ai_user

# Copy requirements and install dependencies
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Set proper permissions
RUN chown -R ai_user:ai_user /app

# Switch to non-root user
USER ai_user

# Env defaults for production
ENV HOST=0.0.0.0 \
    PORT=8000 \
    ALLOWED_ORIGINS="http://localhost:8000,http://localhost:3000,http://localhost:9090" \
    TRUSTED_HOSTS="localhost,127.0.0.1" \
    DEBUG=false \
    DEMO_MODE=false

EXPOSE 8000

# Production health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/health || exit 1

# Production command
CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]





