# Multi-stage Dockerfile for Autonomous Task Solver System
# Production-ready with optimization and security best practices

# Stage 1: Base image with system dependencies
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Stage 2: Python dependencies
FROM base as dependencies

# Copy requirements files
COPY requirements.txt .
COPY requirements-dev.txt .

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

# Stage 3: Development dependencies (optional)
FROM dependencies as dev-dependencies

# Install development dependencies
RUN pip install -r requirements-dev.txt

# Stage 4: Application code
FROM dependencies as app

# Copy application code
COPY autonomous_system/ ./autonomous_system/
COPY config/ ./config/
COPY scripts/ ./scripts/

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/config

# Configuration files will be mounted at runtime

# Copy startup scripts
COPY scripts/start.sh /app/scripts/start.sh
COPY scripts/healthcheck.sh /app/scripts/healthcheck.sh

# Make scripts executable
RUN chmod +x /app/scripts/*.sh

# Create data directories with proper permissions
RUN mkdir -p /app/data/databases \
    /app/data/logs \
    /app/data/cache \
    /app/data/models \
    /app/data/uploads \
    /app/data/exports

# Set proper ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose ports
EXPOSE 8000 8080 9000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD /app/scripts/healthcheck.sh

# Default command
CMD ["/app/scripts/start.sh"]

# Stage 5: Production image (minimal)
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1

# Install only essential system dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    libffi7 \
    libssl3 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy only production dependencies
COPY --from=dependencies /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Copy application code
COPY --from=app /app/autonomous_system ./autonomous_system
COPY --from=app /app/config ./config
COPY --from=app /app/scripts ./scripts

# Create directories
RUN mkdir -p /app/data /app/logs /app/config

# Configuration files will be mounted at runtime

# Make scripts executable
RUN chmod +x /app/scripts/*.sh

# Create data directories
RUN mkdir -p /app/data/databases \
    /app/data/logs \
    /app/data/cache \
    /app/data/models

# Set ownership
RUN chown -R appuser:appuser /app

# Switch user
USER appuser

# Expose ports
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD /app/scripts/healthcheck.sh

# Production command
CMD ["/app/scripts/start.sh"]

# Stage 6: Testing image
FROM dev-dependencies as testing

# Copy test files
COPY tests/ ./tests/
COPY pytest.ini .pytest.ini

# Install test dependencies
RUN pip install pytest pytest-cov pytest-asyncio

# Set test environment
ENV TESTING=1
ENV PYTHONPATH=/app

# Run tests by default
CMD ["pytest", "tests/", "-v", "--cov=autonomous_system", "--cov-report=html"]

# Stage 7: Development image
FROM dev-dependencies as development

# Install additional development tools
RUN pip install ipython jupyter debugpy

# Copy development configuration
COPY .env.development /app/.env

# Set development environment
ENV DEVELOPMENT=1
ENV PYTHONPATH=/app

# Expose additional ports for development
EXPOSE 8000 8080 9000 8888

# Development command with auto-reload
CMD ["python", "-m", "autonomous_system.autonomous_orchestrator"]
