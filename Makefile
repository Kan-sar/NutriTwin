PYTHON ?= python
VENV_PYTHON ?= .venv/Scripts/python.exe
VENV_BIN ?= .venv/Scripts

.PHONY: bootstrap bootstrap-research up migrate seed test lint typecheck validate-data validate-chem demo check down

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
	$(VENV_BIN)/alembic.exe upgrade head

seed:
	$(VENV_PYTHON) scripts/seed.py

test:
	$(VENV_PYTHON) -m pytest --cov --cov-report=term-missing

lint:
	$(VENV_BIN)/ruff.exe check .
	$(VENV_BIN)/ruff.exe format --check .

typecheck:
	$(VENV_PYTHON) -m mypy apps/api/src packages/domain/src packages/data_pipeline/src services/worker/src scripts

validate-data:
	$(VENV_PYTHON) scripts/validate_data.py

validate-chem:
	$(VENV_PYTHON) scripts/validate_data.py --require-rdkit

demo:
	$(VENV_PYTHON) scripts/demo.py

check: lint typecheck validate-data test

down:
	docker compose -f infra/docker/compose.yaml down
