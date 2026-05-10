PYTHON ?= python
PIP ?= $(PYTHON) -m pip
PYTEST ?= .venv/bin/pytest
RUFF ?= .venv/bin/ruff
MYPY ?= .venv/bin/mypy
ALEMBIC ?= .venv/bin/alembic
SPHINXBUILD ?= .venv/bin/sphinx-build
COMPOSE ?= docker compose

.PHONY: install test lint typecheck alembic-sql compose-config compose-telegram-config docs docs-clean check up up-telegram down clean

install:
	$(PIP) install -r requirements.txt

test:
	$(PYTEST)

lint:
	$(RUFF) check .

typecheck:
	$(MYPY) app tests alembic

alembic-sql:
	$(ALEMBIC) upgrade head --sql

compose-config:
	$(COMPOSE) config

compose-telegram-config:
	$(COMPOSE) --profile telegram config

docs:
	$(SPHINXBUILD) -b html docs docs/_build/html

docs-clean:
	rm -rf docs/_build

check: test lint typecheck compose-config compose-telegram-config

up:
	$(COMPOSE) up --build

up-telegram:
	$(COMPOSE) --profile telegram up --build

down:
	$(COMPOSE) down

clean:
	$(COMPOSE) down -v
