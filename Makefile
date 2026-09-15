PYTHON ?= python
ifeq ($(OS),Windows_NT)
VENV_PYTHON ?= .venv/Scripts/python.exe
else
VENV_PYTHON ?= .venv/bin/python
endif
FLUTTER ?= flutter

.PHONY: bootstrap bootstrap-research up migrate seed test lint typecheck validate-data validate-chem import-fdc demo check down client-check

bootstrap:
	$(PYTHON) -m venv .venv
	$(VENV_PYTHON) -m pip install --upgrade pip
	$(VENV_PYTHON) -m pip install -r requirements.lock
	$(VENV_PYTHON) -m pip install --no-deps -e .

bootstrap-research: bootstrap
	$(VENV_PYTHON) -m pip install -r requirements-chem.lock -r requirements-evidence.lock
	$(VENV_PYTHON) -m playwright install chromium

up:
	docker compose -f infra/docker/compose.yaml up --build -d

migrate:
	$(VENV_PYTHON) -m alembic upgrade head

seed:
	$(VENV_PYTHON) scripts/seed.py

test:
	$(VENV_PYTHON) -m pytest --cov --cov-report=term-missing

lint:
	$(VENV_PYTHON) -m ruff check .
	$(VENV_PYTHON) -m ruff format --check .

typecheck:
	$(VENV_PYTHON) -m mypy apps/api/src packages/domain/src packages/data_pipeline/src services/worker/src scripts

validate-data:
	$(VENV_PYTHON) scripts/validate_data.py

validate-chem:
	$(VENV_PYTHON) scripts/validate_data.py --require-rdkit

import-fdc:
	$(VENV_PYTHON) scripts/import_fdc_foundation.py --download

demo:
	$(VENV_PYTHON) scripts/demo.py

check: lint typecheck validate-data test
	$(VENV_PYTHON) scripts/check_docs.py

down:
	docker compose -f infra/docker/compose.yaml down

client-check:
	cd apps/mobile && $(FLUTTER) --no-version-check analyze
	cd apps/mobile && $(FLUTTER) --no-version-check test
