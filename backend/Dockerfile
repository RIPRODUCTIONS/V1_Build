FROM mcr.microsoft.com/playwright/python:v1.54.0-jammy

ENV AIOHTTP_NO_EXTENSIONS=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -U pip \
    && pip install --no-cache-dir -r /app/requirements.txt \
    && pip install --no-cache-dir playwright

COPY app /app/app
COPY scripts /app/scripts

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
