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
