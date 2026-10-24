# @path[Makefile]
# ==============================================================================
# lint-editor development tasks
#
# common entry points for local development.
# run `make` or `make help` to list the targets.

.DEFAULT_GOAL := help

MESSAGE ?= tmp/commit.tmp

.PHONY: help setup install hooks lint format format-check typecheck test test-cov hook-test self-test all check release clean

# Getting started
# ---------------
help:  ## show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  %-14s %s\n", $$1, $$2}'

setup: install hooks  ## install dependencies and git hooks

install:  ## install runtime and dev dependencies with uv
	uv sync --locked

hooks:  ## install the pre-commit and pre-push hooks
	uv run pre-commit install --install-hooks

# Code quality
# ------------
lint:  ## run the ruff linter
	uv run ruff check .

format:  ## format the code with ruff
	uv run ruff format .

format-check:  ## verify formatting without writing
	uv run ruff format --check .

typecheck:  ## type check with mypy
	uv run mypy src/

# Testing
# -------
test:  ## run the test suite
	uv run pytest

test-cov:  ## run the tests with a coverage report
	uv run pytest --cov=lint_editor --cov=lint_commit --cov-report=term-missing

# Integration
# -----------
hook-test:  ## run every pre-commit hook against all files
	uv run pre-commit run --all-files

self-test:  ## check the repository with both hooks
	uv run pre-commit run lint-editor --all-files
	@test -f $(MESSAGE) || (echo "missing $(MESSAGE), add a draft message" >&2; exit 1)
	uv run lint-commit $(MESSAGE)

# All-in-one
# ----------
all: lint format-check typecheck test  ## run lint, format check, typecheck, and tests

check: hook-test  ## run the full pre-commit gate

# Release
# -------
release:  ## bump the version, sync the readme, tag, and push
	bash scripts/release.sh $(BUMP)

# Housekeeping
# ------------
clean:  ## remove caches and build artifacts
	rm -rf build/ dist/ *.egg-info/
	find . -path ./.venv -prune -o -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -path ./.venv -prune -o -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -path ./.venv -prune -o -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -path ./.venv -prune -o -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
