# @path[Makefile]
# lint-editor development tasks
# =============================
#
# common entry points for local development.
# run `make` or `make help` to list the targets.

.DEFAULT_GOAL := help

.PHONY: help setup install hooks lint format typecheck test test-cov hook-test self-test all check clean

# Getting started
# ---------------
help:  ## show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  %-14s %s\n", $$1, $$2}'

setup: install hooks  ## install dependencies and git hooks

install:  ## install runtime and dev dependencies with uv
	uv sync

hooks:  ## install the pre-commit and pre-push hooks
	uv run pre-commit install --install-hooks

# Code quality
# ------------
lint:  ## run the ruff linter
	uv run ruff check .

format:  ## format the code with ruff
	uv run ruff format .

typecheck:  ## type check with mypy
	uv run mypy src/

# Testing
# -------
test:  ## run the test suite
	uv run pytest

test-cov:  ## run the tests with a coverage report
	uv run pytest --cov=lint_editor --cov-report=term-missing

# Integration
# -----------
hook-test:  ## run every pre-commit hook against all files
	uv run pre-commit run --all-files

self-test:  ## check this repository with its own hook
	uv run pre-commit run lint-editor --all-files

# All-in-one
# ----------
all: lint typecheck test  ## run lint, typecheck, and tests

check: hook-test  ## run the full pre-commit gate

# Housekeeping
# ------------
clean:  ## remove caches and build artifacts
	rm -rf build/ dist/ *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
