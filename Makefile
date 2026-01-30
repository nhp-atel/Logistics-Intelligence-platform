.PHONY: help install dev up down logs generate-data dbt-run dbt-test dbt-docs \
        test lint format typecheck clean deploy-dev deploy-prod verify-data \
        trigger-dag test-api build-api

# Default target
help:
	@echo "Logistics Data Platform - Available Commands"
	@echo "============================================"
	@echo ""
	@echo "Development Setup:"
	@echo "  make install        Install production dependencies"
	@echo "  make dev            Install development dependencies"
	@echo "  make up             Start local Docker environment"
	@echo "  make down           Stop local Docker environment"
	@echo "  make logs           View Docker container logs"
	@echo ""
	@echo "Data Generation:"
	@echo "  make generate-data  Generate synthetic logistics data"
	@echo "  make generate-small Generate small sample dataset (1000 packages)"
	@echo "  make generate-large Generate large dataset (100000 packages)"
	@echo ""
	@echo "dbt Commands:"
	@echo "  make dbt-run        Run all dbt models"
	@echo "  make dbt-test       Run dbt tests"
	@echo "  make dbt-docs       Generate and serve dbt documentation"
	@echo "  make dbt-clean      Clean dbt artifacts"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  make test           Run all tests"
	@echo "  make test-unit      Run unit tests only"
	@echo "  make test-int       Run integration tests only"
	@echo "  make lint           Run linting checks"
	@echo "  make format         Format code with ruff"
	@echo "  make typecheck      Run type checking with mypy"
	@echo ""
	@echo "Deployment:"
	@echo "  make deploy-dev     Deploy to dev environment"
	@echo "  make deploy-prod    Deploy to production"
	@echo "  make build-api      Build API Docker image"
	@echo ""
	@echo "Operations:"
	@echo "  make trigger-dag    Trigger an Airflow DAG (DAG_ID=<dag_id>)"
	@echo "  make verify-data    Verify data in BigQuery"
	@echo "  make test-api       Test API endpoints"
	@echo "  make clean          Clean all generated files"

# Variables
PYTHON := python3
PIP := pip
PROJECT_ID ?= logistics-data-platform
ENVIRONMENT ?= dev
DAG_ID ?= daily_ingestion

# Development Setup
install:
	$(PIP) install -r requirements.txt

dev:
	$(PIP) install -e ".[dev]"
	pre-commit install

up:
	docker-compose up -d
	@echo "Waiting for services to be healthy..."
	@sleep 10
	@echo "Services started. Airflow UI: http://localhost:8080"

down:
	docker-compose down

logs:
	docker-compose logs -f

# Data Generation
generate-data:
	$(PYTHON) -m data_generation generate --packages 10000

generate-small:
	$(PYTHON) -m data_generation generate --packages 1000

generate-large:
	$(PYTHON) -m data_generation generate --packages 100000

upload-data:
	$(PYTHON) -m data_generation upload --bucket $(PROJECT_ID)-raw-data

# dbt Commands
dbt-run:
	cd dbt && dbt run --profiles-dir .

dbt-test:
	cd dbt && dbt test --profiles-dir .

dbt-docs:
	cd dbt && dbt docs generate --profiles-dir . && dbt docs serve --profiles-dir .

dbt-clean:
	cd dbt && dbt clean --profiles-dir .

dbt-debug:
	cd dbt && dbt debug --profiles-dir .

# Testing & Quality
test:
	pytest tests/ -v --cov

test-unit:
	pytest tests/unit/ -v

test-int:
	pytest tests/integration/ -v

lint:
	ruff check .

format:
	ruff format .
	ruff check --fix .

typecheck:
	mypy data_generation api feature_store

quality: lint typecheck test

# Deployment
deploy-dev:
	cd infrastructure/terraform && \
		terraform workspace select dev || terraform workspace new dev && \
		terraform apply -var-file=environments/dev.tfvars

deploy-prod:
	cd infrastructure/terraform && \
		terraform workspace select prod || terraform workspace new prod && \
		terraform apply -var-file=environments/prod.tfvars

build-api:
	docker build -t logistics-api:latest -f api/Dockerfile .

push-api:
	docker tag logistics-api:latest gcr.io/$(PROJECT_ID)/logistics-api:latest
	docker push gcr.io/$(PROJECT_ID)/logistics-api:latest

# Operations
trigger-dag:
	airflow dags trigger $(DAG_ID)

verify-data:
	$(PYTHON) scripts/verify_data.py

test-api:
	$(PYTHON) scripts/test_api.py

# Great Expectations
ge-init:
	great_expectations init

ge-validate:
	great_expectations checkpoint run data_quality_checkpoint

# Cleanup
clean:
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf __pycache__
	rm -rf */__pycache__
	rm -rf */*/__pycache__
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

clean-data:
	rm -rf data/generated/*

# Infrastructure
tf-init:
	cd infrastructure/terraform && terraform init

tf-plan:
	cd infrastructure/terraform && terraform plan -var-file=environments/$(ENVIRONMENT).tfvars

tf-apply:
	cd infrastructure/terraform && terraform apply -var-file=environments/$(ENVIRONMENT).tfvars

tf-destroy:
	cd infrastructure/terraform && terraform destroy -var-file=environments/$(ENVIRONMENT).tfvars
