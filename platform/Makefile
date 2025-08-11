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

down:
	@echo "Stopping local infra and removing volumes..."
	docker compose -f platform/infra/docker-compose.yml down -v

schema:
	@echo "Exporting JSON Schemas..."
	$(PY) platform/shared/scripts/export_json_schema.py

fmt:
	ruff format platform
	black --line-length 100 platform

lint:
	ruff check platform

test:
	@echo "No platform tests yet; add under platform/**"
