FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

# Avoid compiling aiohttp C extensions in constrained CI
ENV AIOHTTP_NO_EXTENSIONS=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN python -m venv /app/.venv \
    && /app/.venv/bin/pip install -U pip \
    && /app/.venv/bin/pip install -r /app/requirements.txt

COPY app /app/app
COPY scripts /app/scripts

# Keep PATH minimal and predictable
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
