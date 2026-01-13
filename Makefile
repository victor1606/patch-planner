.PHONY: help install test test-coverage clean run compare visualize lint format

help:
	@echo "PatchPlanner - Makefile Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install          Install package in development mode"
	@echo "  make install-dev      Install with development dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  make test             Run all tests"
	@echo "  make test-coverage    Run tests with coverage report"
	@echo "  make test-verbose     Run tests with verbose output"
	@echo ""
	@echo "Running:"
	@echo "  make run              Run hybrid strategy on scenario1"
	@echo "  make compare          Run all strategies on all scenarios"
	@echo "  make visualize        Generate comparison charts"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean            Remove generated files and caches"
	@echo "  make clean-all        Deep clean including virtual environment"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint             Run code quality checks (if ruff installed)"
	@echo "  make format           Format code (if black installed)"

install:
	pip install -e .

install-dev:
	pip install -e .
	pip install pytest pytest-cov

test:
	python -m pytest tests/ -v

test-coverage:
	python -m pytest tests/ --cov=patchplanner --cov-report=term --cov-report=html
	@echo ""
	@echo "Coverage report generated in htmlcov/index.html"

test-verbose:
	python -m pytest tests/ -vv -s

run:
	python scripts/run.py scenario1 hybrid

compare:
	python scripts/run_comparison.py

visualize:
	@if [ ! -f results/all_results.json ]; then \
		echo "Error: results/all_results.json not found. Run 'make compare' first."; \
		exit 1; \
	fi
	python scripts/visualize_results.py results/all_results.json

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf htmlcov/ .coverage
	@echo "Cleaned generated files and caches"

clean-all: clean
	rm -rf .venv/
	rm -rf results/
	rm -rf figures/
	@echo "Deep clean completed"

lint:
	@if command -v ruff >/dev/null 2>&1; then \
		ruff check src/ tests/; \
	else \
		echo "ruff not installed. Install with: pip install ruff"; \
	fi

format:
	@if command -v black >/dev/null 2>&1; then \
		black src/ tests/ scripts/; \
	else \
		echo "black not installed. Install with: pip install black"; \
	fi
