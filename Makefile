.PHONY: build up down migrate lint format-check format test test-cov compile smoke e2e \
	local-install local-test local-lint local-format local-run local-migrate

COMPOSE := docker compose
APP := $(COMPOSE) run --rm app
APP_NODEPS := $(COMPOSE) run --rm --no-deps app
COV_CMD := pytest --cov=app --cov=legacy --cov-report=term-missing

build:
	$(COMPOSE) build

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down -v

migrate:
	$(APP) alembic upgrade head

lint:
	$(APP_NODEPS) ruff check .

format-check:
	$(APP_NODEPS) ruff format --check .

format:
	$(APP_NODEPS) ruff format .

test:
	$(APP) pytest

test-cov:
	$(APP) $(COV_CMD) --cov-fail-under=90

compile:
	$(APP_NODEPS) python -m compileall -q app legacy tests

smoke:
	curl -f http://localhost:8000/health
	curl -f http://localhost:8000/openapi.json

e2e:
	$(COMPOSE) exec -T -e E2E_BASE_URL=http://localhost:8000 app pytest tests/e2e

local-install:
	pip install -e ".[dev]"

local-test:
	pytest

local-lint:
	ruff check .

local-format:
	ruff format .

local-run:
	uvicorn app.main:app --reload

local-migrate:
	alembic upgrade head
