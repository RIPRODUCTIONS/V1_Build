.PHONY: bootstrap up down schema fmt lint test

PY=python3

bootstrap:
	@echo "Bootstrap platform tooling..."
	$(PY) -m pip install -U pip
	$(PY) -m pip install ruff black

up:
	@echo "Starting local infra (docker-compose)..."
	docker compose -f platform/infra/docker-compose.yml up -d
	@echo "Grafana: http://localhost:3001 (admin/admin)"
	@echo "Prometheus: http://localhost:9090"
	@echo "Manager Health: http://localhost:8011/health"
	@echo "Manager Metrics: http://localhost:9109/metrics"

down:
	@echo "Stopping local infra and removing volumes..."
	docker compose -f platform/infra/docker-compose.yml down -v

schema:
	@echo "Exporting JSON Schemas..."
	PYTHONPATH=. $(PY) shared/scripts/export_json_schema.py

fmt:
	ruff format platform
	black --line-length 100 platform

lint:
	ruff check platform

test:
	@echo "No platform tests yet; add under platform/**"

manager:
	@echo "Run manager consumer"
	PYTHONPATH=. python platform/orchestration/manager/consumer.py

manager-image:
	@echo "Build manager consumer image"
	docker build -f platform/orchestration/manager/Dockerfile -t manager-consumer:dev .

manager-up:
	@echo "Starting manager in compose"
	docker compose -f platform/infra/docker-compose.yml up -d manager

manager-down:
	@echo "Stopping manager in compose"
	docker compose -f platform/infra/docker-compose.yml rm -sf manager

manager-logs:
	@echo "Tailing manager logs"
	docker compose -f platform/infra/docker-compose.yml logs -f manager
