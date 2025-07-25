.PHONY: test test-unit test-integration test-coverage install install-dev lint format clean

# Install dependencies
install:
	pip install -r requirements.txt

install-dev: install
	pip install -r requirements-dev.txt
	pip install -e .

# Run all tests
test:
	pytest

# Run only unit tests
test-unit:
	pytest -m "not integration"

# Run only integration tests  
test-integration:
	pytest -m integration

# Run tests with coverage report
test-coverage:
	pytest --cov=github_backlog_generator --cov-report=html --cov-report=term

# Run specific test file
test-file:
	@read -p "Enter test file name (e.g., test_phase_generator.py): " file; \
	pytest tests/$$file -v

# Linting and formatting
lint:
	flake8 src/ tests/
	mypy src/

format:
	black src/ tests/
	isort src/ tests/

# Clean up
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf *.egg-info/
	rm -rf dist/
	rm -rf build/

# Development workflow
dev: install-dev lint test

# Quick test during development
quick-test:
	pytest -x -v --tb=short

# Watch tests (requires pytest-watch)
watch:
	ptw -- -x -v --tb=short