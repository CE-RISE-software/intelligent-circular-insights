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

demo:  ## Run the API locally
	uv run uvicorn apps.api.main:app --reload --port 8000

gate-s0:  ## The Sprint 0 exit gate
	@$(MAKE) check
	uv run pytest tests/unit/test_layering.py tests/unit/test_envelope_invariants.py -q
	uv run pytest -m contract -q
	@echo "Sprint 0 gate: green"

.PHONY: help setup lint format typecheck layering check test test-fast contract cov live demo gate-s0
