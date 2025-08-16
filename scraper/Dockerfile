# Dockerfile for the modular web scraper
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies (excluding Playwright for now)
RUN pip install --no-cache-dir -r requirements.txt || \
    pip install --no-cache-dir beautifulsoup4 pydantic pyyaml sqlalchemy fastapi uvicorn requests

# Copy application code
COPY . /app/

# Create output directory
RUN mkdir -p /app/output

# Set permissions
RUN chmod +x /app/main_scraper.py

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port for FastAPI (if running as service)
EXPOSE 8000

# Default command
ENTRYPOINT ["python", "main_scraper.py"]
