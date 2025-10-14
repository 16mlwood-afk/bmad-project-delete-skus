# Makefile for SKU Cleanup Tool Development

.PHONY: help install test test-all test-coverage lint format clean docs

# Default target
help:
	@echo "Available commands:"
	@echo "  install      Install development dependencies"
	@echo "  test         Run basic tests"
	@echo "  test-all     Run all tests with coverage"
	@echo "  lint         Run linting and code quality checks"
	@echo "  format       Format code with black and isort"
	@echo "  clean        Clean up build artifacts and cache"
	@echo "  docs         Generate documentation"
	@echo "  benchmark    Run performance benchmarks"

# Install dependencies
install:
	pip install -r requirements.txt
	pip install pytest pytest-cov black isort mypy flake8 bandit safety

# Run basic tests
test:
	pytest tests/ -v

# Run all tests with coverage
test-all:
	pytest --cov=. --cov-report=html --cov-report=term-missing tests/

# Run specific test categories
test-unit:
	pytest tests/test_*.py -k "not performance and not integration" -v

test-integration:
	pytest tests/test_integration_simple.py -v

test-performance:
	pytest tests/test_performance.py -v

# Code quality checks
lint:
	@echo "Running code quality checks..."
	black --check --diff .
	isort --check-only --diff .
	mypy . --ignore-missing-imports
	flake8 . --max-line-length=100 --extend-ignore=E203,W503

# Format code
format:
	@echo "Formatting code..."
	black .
	isort .

# Security checks
security:
	@echo "Running security checks..."
	safety check
	bandit -r . -f json -o bandit-report.json

# Clean up
clean:
	@echo "Cleaning up..."
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

# Documentation
docs:
	@echo "Generating documentation..."
	# Add documentation generation commands here
	@echo "Documentation generation not yet implemented"

# Performance benchmarks
benchmark:
	@echo "Running performance benchmarks..."
	python -c "
	import time
	from data_processor import DataProcessor
	from datetime import datetime, timedelta

	processor = DataProcessor()

	# Benchmark different dataset sizes
	sizes = [100, 1000, 5000, 10000]
	results = []

	for size in sizes:
		sku_data = []
		for i in range(size):
			age_days = 400 if i % 3 == 0 else 15
			created_date = (datetime.now() - timedelta(days=age_days)).strftime('%d/%m/%Y')
			sku_data.append({
				'sku': f'PERF-{i:06d}',
				'asin': f'B{i:011d}',
				'created_date': created_date,
				'fulfillment_channel': 'MERCHANT',
				'quantity': 0,
				'status': 'Active'
			})

		start_time = time.perf_counter()
		processed = processor.process_sku_data(sku_data)
		end_time = time.perf_counter()

		processing_time = end_time - start_time
		throughput = size / processing_time

		results.append(f'Size {size}: {throughput:.0f} SKUs/second, {processing_time:.2f}s total')

	print('Performance Benchmarks:')
	for result in results:
		print(f'  {result}')
	"

# Development environment setup
dev-setup: install
	@echo "Setting up development environment..."
	pre-commit install
	@echo "✅ Development environment ready!"

# Run all quality checks
quality: lint security test-all
	@echo "✅ All quality checks passed!"

# Quick development cycle
dev: format lint test
	@echo "✅ Development cycle complete!"
