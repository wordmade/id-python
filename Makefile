.PHONY: test lint type-check build clean install-dev help

## Run tests
test:
	python -m pytest tests/ -v

## Run tests with coverage
test-cov:
	python -m pytest tests/ -v --cov=wordmade_id --cov-report=term-missing

## Lint with ruff
lint:
	ruff check src/ tests/
	ruff format --check src/ tests/

## Format code
format:
	ruff format src/ tests/
	ruff check --fix src/ tests/

## Type check with mypy
type-check:
	mypy src/wordmade_id/

## Build distribution
build:
	python -m build

## Clean build artifacts
clean:
	rm -rf dist/ build/ *.egg-info src/*.egg-info .pytest_cache .mypy_cache .coverage htmlcov

## Install for development
install-dev:
	pip install -e ".[dev]"

## Show help
help:
	@echo "id-python — Wordmade ID Python SDK"
	@echo ""
	@echo "  make test         Run tests"
	@echo "  make test-cov     Run tests with coverage"
	@echo "  make lint         Lint with ruff"
	@echo "  make format       Format code"
	@echo "  make type-check   Type check with mypy"
	@echo "  make build        Build distribution"
	@echo "  make install-dev  Install for development"
	@echo "  make clean        Clean build artifacts"
