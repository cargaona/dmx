# Makefile for dmx development and deployment

.PHONY: help install install-dev test test-coverage lint format type-check clean build docker run-tests pre-commit

# Default target
help:
	@echo "Available targets:"
	@echo "  install      - Install package"
	@echo "  install-dev  - Install package with development dependencies"
	@echo "  test         - Run tests"
	@echo "  test-coverage - Run tests with coverage report"
	@echo "  lint         - Run linting checks"
	@echo "  format       - Format code with black"
	@echo "  type-check   - Run type checking with mypy"
	@echo "  clean        - Clean build artifacts"
	@echo "  build        - Build package"
	@echo "  docker       - Build Docker image"
	@echo "  run-tests    - Run all quality checks"
	@echo "  pre-commit   - Install pre-commit hooks"

# Installation
install:
	pip install .

install-dev:
	pip install -e ".[dev,test]"


# Testing
test:
	pytest tests/ -v

test-coverage:
	pytest tests/ -v --cov=dmx --cov-report=html --cov-report=term

test-integration:
	pytest tests/ -v -m integration

# Code quality
lint:
	flake8 dmx/ tests/
	
format:
	black dmx/ tests/

format-check:
	black --check dmx/ tests/

type-check:
	mypy dmx/

# Pre-commit
pre-commit:
	pre-commit install

run-pre-commit:
	pre-commit run --all-files

# Build and deployment
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	python -m build

docker:
	docker build -t dmx:latest .

docker-compose-up:
	docker-compose up -d

docker-compose-down:
	docker-compose down

# Run all quality checks
run-tests: format-check lint type-check test

# Development setup
setup-dev: install-dev pre-commit
	@echo "Development environment setup complete!"

# Deployment
deploy-check: run-tests
	@echo "All checks passed - ready for deployment"

# Monitoring
logs:
	docker-compose logs -f dmx

status:
	docker-compose ps

# Documentation
docs:
	@echo "Generating documentation..."
	# Add documentation generation commands here

# Database management (for future features)
migrate:
	@echo "Running database migrations..."
	# Add migration commands here

# Performance testing
perf-test:
	@echo "Running performance tests..."
	# Add performance testing commands here

# Security scanning
security-scan:
	pip-audit
	bandit -r dmx/

# Release management
release-patch:
	bump2version patch

release-minor:
	bump2version minor

release-major:
	bump2version major