FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN python -m venv /app/.venv && /app/.venv/bin/pip install -U pip && /app/.venv/bin/pip install -r /app/requirements.txt
COPY app /app/app
COPY scripts /app/scripts
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
