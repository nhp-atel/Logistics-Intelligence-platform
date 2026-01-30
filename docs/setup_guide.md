# Setup Guide

This guide walks you through setting up the Logistics Data Platform for local development and GCP deployment.

## Prerequisites

### Required Software

- Python 3.11+
- Docker & Docker Compose
- Git
- Make
- Google Cloud SDK (for GCP deployment)

### Optional Tools

- Terraform 1.5+ (for infrastructure deployment)
- dbt CLI (for model development)

## Local Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/logistics-data-platform.git
cd logistics-data-platform
```

### 2. Create Python Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate it
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# Install development dependencies
pip install -e ".[dev]"
```

### 3. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit with your settings
# For local development, you can use defaults
```

### 4. Start Docker Services

```bash
# Start all services (Airflow, PostgreSQL, Jupyter)
make up

# Wait for services to be healthy
docker-compose ps

# View logs if needed
make logs
```

### 5. Access Services

| Service | URL | Credentials |
|---------|-----|-------------|
| Airflow | http://localhost:8080 | airflow / airflow |
| Jupyter | http://localhost:8888 | No password |
| API | http://localhost:8000/docs | No auth in dev |
| PostgreSQL | localhost:5432 | airflow / airflow |

### 6. Generate Sample Data

```bash
# Generate 10,000 packages with related data
make generate-data

# Or customize
python -m data_generation generate \
  --packages 5000 \
  --customers 1000 \
  --format parquet \
  --weather
```

## GCP Setup

### 1. Create GCP Project

```bash
# Set your project ID
export PROJECT_ID=your-project-id

# Create project (or use existing)
gcloud projects create $PROJECT_ID

# Set as default
gcloud config set project $PROJECT_ID

# Enable billing (required)
# Do this in the GCP Console
```

### 2. Enable Required APIs

```bash
gcloud services enable \
  bigquery.googleapis.com \
  storage.googleapis.com \
  pubsub.googleapis.com \
  composer.googleapis.com \
  run.googleapis.com \
  cloudfunctions.googleapis.com \
  cloudscheduler.googleapis.com \
  iam.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com
```

### 3. Create Service Account

```bash
# Create service account
gcloud iam service-accounts create logistics-sa \
  --display-name="Logistics Data Platform Service Account"

# Grant required roles
for role in \
  roles/bigquery.admin \
  roles/storage.admin \
  roles/pubsub.admin \
  roles/composer.admin \
  roles/run.admin
do
  gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:logistics-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="$role"
done

# Create and download key
gcloud iam service-accounts keys create credentials/service-account.json \
  --iam-account=logistics-sa@$PROJECT_ID.iam.gserviceaccount.com
```

### 4. Deploy Infrastructure

```bash
cd infrastructure/terraform

# Initialize Terraform
terraform init

# Create terraform.tfvars (or use environment files)
cat > terraform.tfvars << EOF
project_id = "your-project-id"
region = "us-central1"
environment = "dev"
enable_composer = false  # Set true for production
EOF

# Plan and apply
terraform plan
terraform apply
```

### 5. Upload Data to GCS

```bash
# Generate data
make generate-data

# Upload to GCS
python -m data_generation upload \
  --bucket $PROJECT_ID-raw-data \
  --prefix raw
```

### 6. Configure dbt

```bash
cd dbt

# Update profiles.yml with your project ID
# Or set environment variable
export GCP_PROJECT_ID=your-project-id

# Test connection
dbt debug --profiles-dir .

# Run models
dbt run --profiles-dir .
```

## Verification

### Verify Local Setup

```bash
# Check Docker services
docker-compose ps

# Check Airflow
curl http://localhost:8080/health

# Check API
curl http://localhost:8000/health

# Run tests
make test
```

### Verify GCP Setup

```bash
# Check BigQuery datasets
bq ls

# Check GCS buckets
gsutil ls

# Check Pub/Sub topics
gcloud pubsub topics list

# Query test data
bq query --use_legacy_sql=false \
  "SELECT COUNT(*) FROM raw.packages"
```

## Common Issues

### Docker Memory Issues

If Docker runs out of memory:

```bash
# Increase Docker memory in Docker Desktop settings
# Or reduce Airflow workers:
# Edit docker-compose.yml, reduce AIRFLOW__CELERY__WORKER_CONCURRENCY
```

### GCP Authentication Issues

```bash
# Re-authenticate
gcloud auth application-default login

# Or use service account
export GOOGLE_APPLICATION_CREDENTIALS=./credentials/service-account.json
```

### dbt Connection Issues

```bash
# Verify BigQuery permissions
bq ls --project_id=$PROJECT_ID

# Check dbt profiles
cat dbt/profiles.yml

# Test connection
cd dbt && dbt debug
```

### Port Conflicts

If ports 8080, 8000, or 5432 are in use:

```bash
# Find process using port
lsof -i :8080

# Kill it or change docker-compose.yml ports
```

## Next Steps

1. **Explore the data**: Open Jupyter at http://localhost:8888
2. **Run DAGs**: Enable and trigger DAGs in Airflow
3. **Test API**: Try endpoints at http://localhost:8000/docs
4. **Deploy to GCP**: Follow the deployment section above
