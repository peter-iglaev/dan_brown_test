.PHONY: help install test run docker-build docker-run clean lint format

help:
	@echo "Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make test         - Run tests with coverage"
	@echo "  make run          - Run the service locally"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-run   - Run Docker container"
	@echo "  make lint         - Run code quality checks"
	@echo "  make format       - Format code with ruff"
	@echo "  make clean        - Clean up generated files"

install:
	pip install --upgrade pip
	pip install -r requirements.txt

test:
	pytest tests/ -v --cov=app --cov-report=term-missing

test-fast:
	pytest tests/ -v -x

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

docker-build:
	docker build -t fx-service .

docker-run:
	docker run -p 8000:8000 fx-service

docker-compose-up:
	docker-compose up -d

docker-compose-down:
	docker-compose down

lint:
	ruff check app/ tests/

format:
	ruff format app/ tests/

clean:
	rm -rf __pycache__ .pytest_cache .coverage htmlcov *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
