.PHONY: research-offline
research-offline:
	@echo "Running offline research with fixtures..."
	RESEARCH_ENABLED=1 python -m tools.web_research.cli "hello world"

.PHONY: venv install safe-install dev deps lint fmt type health pre-commit-install cli-health

VENV_DIR=.venv
PY=$(VENV_DIR)/bin/python
PIP=$(VENV_DIR)/bin/pip

venv:
	python3 -m venv $(VENV_DIR)
	$(PY) -m pip install --upgrade pip

# Install runtime-safe deps only (excludes private/unavailable ones)
safe-install: venv
	$(PIP) install streamlit python-dotenv pandas gitpython --quiet

# Install development tooling
.dev:
	$(PIP) install black ruff mypy pre-commit --quiet

dev: venv .dev

lint:
	$(VENV_DIR)/bin/ruff check src

fmt:
	$(VENV_DIR)/bin/ruff format src
	$(VENV_DIR)/bin/black --line-length=100 src

type:
	$(VENV_DIR)/bin/mypy src

health:
	$(PY) health_check.py || true

cli-health:
	PYTHONPATH=src $(PY) -m builder.cli health || true

pre-commit-install:
	$(VENV_DIR)/bin/pre-commit install

.PHONY: zap k6 db-upgrade
zap:
	@bash scripts/ci/run_zap_blocking.sh http://127.0.0.1:8000 scripts/ci/zap-allowlist.txt

k6:
	@docker run --rm -e API=http://127.0.0.1:8000 -v $(PWD)/scripts:/scripts grafana/k6 run /scripts/k6_smoke.js

db-upgrade:
	@alembic -c backend/alembic.ini upgrade head

.PHONY: post-merge
post-merge:
	@bash scripts/ops/post_merge_runner.sh | tee /tmp/post_merge_runner.out; test $${PIPESTATUS[0]} -eq 0

.PHONY: next5
next5:
	@bash scripts/ops/next5_orchestrator.sh | tee /tmp/next5_orchestrator.out; test $${PIPESTATUS[0]} -eq 0

.PHONY: all-post-merge
all-post-merge:
	@set -e; \
	echo "[ $$(date -Iseconds) ] Starting full post-merge chain"; \
	$(MAKE) post-merge; \
	echo "[ $$(date -Iseconds) ] post-merge complete"; \
	$(MAKE) next5; \
	echo "[ $$(date -Iseconds) ] next5 complete"; \
	echo "[ $$(date -Iseconds) ] All steps finished successfully"

.PHONY: web-upgrade-next
web-upgrade-next:
	@bash scripts/web/upgrade_next.sh $(version)
