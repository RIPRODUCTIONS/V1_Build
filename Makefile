.PHONY: up down logs
up:
	docker compose --profile dev up -d --build
down:
	docker compose down -v
logs:
	docker compose logs -f api
SHELL := /bin/bash
ROOT  := $(shell pwd)

export AUTO_KILL ?= 1

.PHONY: up up-debug up-lifespan down logs doctor smoke clean hooks deps audit audit-py audit-js lint lint-py lint-js fmt fmt-py fmt-js test test-backend coverage heal

up:
	@DETACH=1 ./scripts/dev_up.sh

up-debug:
	@DEBUG_STARTUP=1 DETACH=1 ./scripts/dev_up.sh

up-lifespan:
	@DISABLE_LIFESPAN=1 DEBUG_STARTUP=1 DETACH=1 ./scripts/dev_up.sh

down:
	@./scripts/dev_down.sh

logs:
	@tail -f logs/backend-dev.log

doctor:
	@./scripts/doctor.sh

smoke:
	@cd backend && . .venv/bin/activate && python scripts/smoke_check.py

clean:
	@rm -f $(ROOT)/.dev/backend.pid
	@rm -f $(ROOT)/logs/backend-dev.log

hooks:
	@./scripts/install_hooks.sh

# Layer 7: Dependency Guardian
deps:
	cd backend && python -m pip install --upgrade pip && pip install -r requirements.txt || true
	[ -d "frontend" ] && cd frontend && npm ci || true

audit: audit-py audit-js

audit-py:
	cd backend && python -m pip install --upgrade pip pip-audit safety || true
	cd backend && pip-audit || true
	cd backend && safety check -r requirements.txt || true

audit-js:
	[ -d "frontend" ] && cd frontend && npm audit --audit-level=high || true

# Layer 8: Code Quality Enforcer
lint: lint-py lint-js

lint-py:
	cd backend && python -m pip install --upgrade pip ruff || true
	cd backend && ruff check .

lint-js:
	[ -d "apps/web" ] && cd apps/web && npm run lint || true

fmt: fmt-py fmt-js

fmt-py:
	cd backend && python -m pip install --upgrade pip ruff || true
	cd backend && ruff check --fix . && ruff format .

fmt-js:
	[ -d "apps/web" ] && cd apps/web && npm run format && npm run lint:fix || true

# Layer 9: Test Coverage Sentinel
COV_PCT ?= 70

test: test-backend

test-backend:
	cd backend && python -m pip install --upgrade pip && pip install -r requirements-dev.txt || true
	cd backend && pytest

coverage:
	cd backend && pytest --cov=app --cov-report=term-missing
	@echo "Enforcing coverage >= $(COV_PCT)%"
	@python -c "import sys, re, subprocess; out = subprocess.run(['bash','-lc','cd backend && pytest --cov=app --cov-report=term'], capture_output=True, text=True).stdout; m = re.search(r'TOTAL\s+\d+\s+\d+\s+(\d+)%', out); pct = int(m.group(1)) if m else 0; print(f'Coverage: {pct}%'); sys.exit(0 if pct >= int('$(COV_PCT)') else 2)"

# Layer 11: Auto-Healing Infrastructure
heal:
	HEALTH_URL="http://127.0.0.1:8000/health" RESTART_CMD="DETACH=1 scripts/dev_up.sh" bash scripts/auto_heal.sh
