# Logistics & Delivery Analytics Platform

A production-grade data engineering platform that simulates a logistics company's data infrastructure, demonstrating end-to-end data pipeline capabilities.

## Overview

This project implements a complete data platform for package delivery tracking, delivery time prediction, route optimization analytics, and customer satisfaction insights.

### Key Features

- **Synthetic Data Generation**: Realistic logistics data with configurable volumes
- **ETL Pipelines**: Airflow DAGs for batch and streaming ingestion
- **Data Modeling**: dbt-based dimensional model with facts and dimensions
- **Data Quality**: Great Expectations validation framework
- **ML Features**: Feature store for delivery prediction and customer segmentation
- **REST API**: FastAPI-based data access layer
- **Infrastructure as Code**: Terraform for GCP resources

## Architecture

```
Data Sources → Ingestion (GCS/Pub/Sub) → Orchestration (Airflow)
     ↓
Transformation (dbt) → Data Warehouse (BigQuery)
     ↓
Feature Store → Serving (FastAPI/Cloud Run)
```

## Technology Stack

| Layer | Technology |
|-------|------------|
| Cloud Platform | Google Cloud Platform |
| Object Storage | Cloud Storage |
| Event Streaming | Pub/Sub |
| Orchestration | Cloud Composer (Airflow) |
| Data Modeling | dbt |
| Data Warehouse | BigQuery |
| Data Quality | Great Expectations |
| API | FastAPI + Cloud Run |
| IaC | Terraform |
| CI/CD | GitHub Actions |

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Google Cloud SDK (for deployment)
- Make

### Local Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/logistics-data-platform.git
cd logistics-data-platform

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
make dev

# Copy environment template
cp .env.example .env
# Edit .env with your settings

# Start local services (Airflow, PostgreSQL, Jupyter)
make up

# Generate sample data
make generate-data

# Access services:
# - Airflow: http://localhost:8080 (airflow/airflow)
# - Jupyter: http://localhost:8888
# - API: http://localhost:8000/docs
```

### Generate Synthetic Data

```bash
# Generate 10,000 packages with related data
python -m data_generation generate --packages 10000

# Generate larger dataset
python -m data_generation generate --packages 100000 --weather

# Output formats: parquet (default), csv, json
python -m data_generation generate --packages 5000 --format csv
```

### Run dbt Models

```bash
# Install dbt packages
cd dbt && dbt deps

# Run all models
dbt run --profiles-dir .

# Run tests
dbt test --profiles-dir .

# Generate documentation
dbt docs generate && dbt docs serve
```

## Project Structure

```
logistics-data-platform/
├── airflow/              # Airflow DAGs and plugins
│   └── dags/
│       ├── ingestion/    # Data ingestion DAGs
│       ├── transformation/# dbt transformation DAGs
│       ├── quality/      # Data quality DAGs
│       └── features/     # Feature computation DAGs
├── api/                  # FastAPI application
│   ├── routers/          # API endpoints
│   ├── models/           # Pydantic models
│   └── services/         # Business logic
├── data_generation/      # Synthetic data generators
│   └── generators/       # Entity generators
├── dbt/                  # dbt project
│   └── models/
│       ├── staging/      # Staging models
│       ├── intermediate/ # Intermediate models
│       └── marts/        # Fact/dimension models
├── feature_store/        # ML feature definitions
├── great_expectations/   # Data quality expectations
├── infrastructure/       # Terraform IaC
│   └── terraform/
├── tests/                # Test suite
└── docs/                 # Documentation
```

## Data Model

### Dimensional Model

**Fact Tables:**
- `fact_deliveries` - Package delivery metrics
- `fact_tracking_events` - Package scan events

**Dimension Tables:**
- `dim_customers` - Customer information (SCD Type 2)
- `dim_locations` - Facilities and addresses
- `dim_drivers` - Driver information
- `dim_date` - Date dimension

### Feature Tables

- `ftr_delivery_predictions` - Features for delivery time ML
- `ftr_customer_segments` - Customer behavior features
- `ftr_route_performance` - Route optimization metrics

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Health check |
| `GET /api/v1/deliveries/{id}` | Get delivery by ID |
| `GET /api/v1/deliveries` | List deliveries with filters |
| `GET /api/v1/tracking/{id}` | Get tracking history |
| `GET /api/v1/features/customer/{id}` | Get customer features |
| `GET /api/v1/analytics/summary` | Get aggregate statistics |

## Deployment

### Deploy Infrastructure

```bash
# Initialize Terraform
cd infrastructure/terraform
terraform init

# Plan changes
terraform plan -var-file=environments/dev.tfvars

# Apply changes
terraform apply -var-file=environments/dev.tfvars
```

### Deploy API

```bash
# Build Docker image
make build-api

# Push to Container Registry
make push-api

# Deploy to Cloud Run (via Terraform)
make deploy-dev
```

## Development

### Running Tests

```bash
# All tests
make test

# Unit tests only
make test-unit

# Integration tests
make test-int

# With coverage
pytest tests/ -v --cov
```

### Code Quality

```bash
# Linting
make lint

# Format code
make format

# Type checking
make typecheck

# All quality checks
make quality
```

## Cost Optimization

This project is designed to minimize cloud costs:

| Resource | Free Tier | Strategy |
|----------|-----------|----------|
| BigQuery | 10GB storage, 1TB queries | Partitioning, limit dev queries |
| Cloud Storage | 5GB | Clean up test data |
| Cloud Composer | None | Use local Airflow for dev |
| Cloud Run | 2M requests | Sufficient for demo |

**Recommendation:** Develop locally with Docker, deploy to GCP only for demo.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run quality checks: `make quality`
5. Submit a pull request

## License

MIT License - see LICENSE file for details.
