FROM python:3.11-slim

WORKDIR /app

COPY platform/orchestration/manager/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY platform /app/platform

ENV PYTHONPATH=/app
ENV REDIS_URL=redis://host.docker.internal:6379/0
ENV MANAGER_METRICS_PORT=9109

CMD ["python", "platform/orchestration/manager/consumer.py"]

