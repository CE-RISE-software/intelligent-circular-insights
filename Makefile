.DEFAULT_GOAL := help
SHELL := /bin/bash

# uv needs to delete directories while installing. If your working tree is on a
# filesystem that refuses deletes (some mounted/synced folders do), point the
# virtualenv somewhere else:
#     export UV_PROJECT_ENVIRONMENT=$$HOME/.venv-ici
# Otherwise the default in-repo .venv is fine and nothing here needs changing.
export UV_LINK_MODE ?= copy

help:  ## List targets
	@grep -hE '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-14s\033[0m %s\n",$$1,$$2}'

setup:  ## Install everything (uv workspace + dev group)
	uv sync --all-packages --dev

lint:  ## ruff check + format check
	uv run ruff check packages apps tests
	uv run ruff format --check packages apps tests

format:  ## ruff format, in place
	uv run ruff format packages apps tests
	uv run ruff check --fix packages apps tests

typecheck:  ## mypy (typed core and LLM boundaries)
	uv run mypy packages/ici_core/src packages/ici_llm/src apps

layering:  ## import-linter: the dependency arrow points inward
	uv run lint-imports --config .importlinter

check: lint typecheck layering  ## Everything that is not a test

test:  ## Full suite. No API key needed — every LLM call is replayed from a cassette.
	uv run pytest

test-fast:  ## Unit + contract only
	uv run pytest tests/unit tests/contract

contract:  ## The port contracts, every implementation
	uv run pytest -m contract

cov:  ## Test with coverage
	uv run pytest --cov=packages --cov-report=term-missing

live:  ## Real OpenAI calls. Run by hand, never in CI. Costs money.
	uv run pytest -m live --run-live --no-header

hooks:  ## Install the pre-commit secret guard (git does not do this from a clone)
	git config core.hooksPath .githooks
	chmod +x .githooks/*
	@echo "Secret guard active. tests/test_no_secrets.py enforces it regardless."

record:  ## Capture cassettes from the real model. Costs money. Capped at 40 calls / $1.
	@test -f .env || { echo "No .env. Copy .env.example and add OPENAI_API_KEY."; exit 1; }
	@grep -q '^OPENAI_API_KEY=sk-' .env || { echo ".env has no OPENAI_API_KEY."; exit 1; }
	@echo "Recording against the live API. The recorder reserves worst-case cost"
	@echo "before every attempt and refuses past 40 calls or 1 estimated USD."
	uv run python -m tooling.record_llm --record --env-file .env
	@echo
	@echo "Now verify the suite still replays without the key:"
	@echo "    LLM_CASSETTE_MODE=replay make test"

secrets:  ## Check that no credential is tracked by git
	uv run pytest tests/test_no_secrets.py -q

web:  ## Install/repair the frontend deps (outside the repo, symlinked in)
	@bash apps/web/setup-web.sh

web-check:  ## Typecheck and build the frontend
	@bash apps/web/setup-web.sh --quiet
	cd apps/web && npx tsc --noEmit && npx vite build

smoke:  ## Playwright, both modes. Starts both servers itself.
	@bash apps/web/setup-web.sh --quiet
	cd apps/web && npx playwright test --grep smoke

demo:  ## Run the API locally
	uv run uvicorn apps.api.main:app --reload --port 8000

gate-s0:  ## The Sprint 0 exit gate
	@$(MAKE) check
	uv run pytest tests/unit/test_layering.py tests/unit/test_envelope_invariants.py -q
	uv run pytest -m contract -q
	@echo "Sprint 0 gate: green"

.PHONY: help setup lint format typecheck layering check test test-fast contract cov live \
        demo gate-s0 hooks record secrets web web-check smoke
