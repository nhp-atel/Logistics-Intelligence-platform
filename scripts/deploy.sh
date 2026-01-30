#!/bin/bash
# Deployment script for Logistics Data Platform

set -e

# Configuration
PROJECT_ID=${GCP_PROJECT_ID:-""}
REGION=${GCP_REGION:-"us-central1"}
ENVIRONMENT=${ENVIRONMENT:-"dev"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check required environment variables
check_requirements() {
    log_info "Checking requirements..."

    if [ -z "$PROJECT_ID" ]; then
        log_error "GCP_PROJECT_ID environment variable is required"
        exit 1
    fi

    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI is required but not installed"
        exit 1
    fi

    if ! command -v terraform &> /dev/null; then
        log_error "Terraform is required but not installed"
        exit 1
    fi

    log_info "Requirements check passed"
}

# Deploy infrastructure
deploy_infrastructure() {
    log_info "Deploying infrastructure..."

    cd infrastructure/terraform

    # Initialize Terraform
    terraform init \
        -backend-config="bucket=${PROJECT_ID}-terraform-state" \
        -backend-config="prefix=logistics-data-platform/${ENVIRONMENT}"

    # Plan
    terraform plan \
        -var-file="environments/${ENVIRONMENT}.tfvars" \
        -var="project_id=${PROJECT_ID}" \
        -out=tfplan

    # Apply
    terraform apply -auto-approve tfplan

    cd ../..
    log_info "Infrastructure deployed successfully"
}

# Build and push API container
deploy_api() {
    log_info "Deploying API..."

    # Build image
    docker build -t gcr.io/${PROJECT_ID}/logistics-api:latest -f api/Dockerfile .

    # Push to Container Registry
    docker push gcr.io/${PROJECT_ID}/logistics-api:latest

    # Deploy to Cloud Run
    gcloud run deploy logistics-api \
        --image gcr.io/${PROJECT_ID}/logistics-api:latest \
        --region ${REGION} \
        --platform managed \
        --allow-unauthenticated \
        --set-env-vars="GCP_PROJECT_ID=${PROJECT_ID},ENVIRONMENT=${ENVIRONMENT}"

    log_info "API deployed successfully"
}

# Upload DAGs to Cloud Composer
deploy_dags() {
    log_info "Deploying DAGs..."

    # Get Composer DAGs bucket
    DAGS_BUCKET=$(gcloud composer environments describe logistics-composer-${ENVIRONMENT} \
        --location=${REGION} \
        --format="value(config.dagGcsPrefix)" 2>/dev/null || echo "")

    if [ -z "$DAGS_BUCKET" ]; then
        log_warn "Cloud Composer not enabled, skipping DAG deployment"
        return
    fi

    # Upload DAGs
    gsutil -m cp -r airflow/dags/* ${DAGS_BUCKET}/

    log_info "DAGs deployed successfully"
}

# Run dbt models
deploy_dbt() {
    log_info "Running dbt models..."

    cd dbt

    # Install packages
    dbt deps --profiles-dir .

    # Run models
    dbt run --profiles-dir . --target ${ENVIRONMENT}

    # Run tests
    dbt test --profiles-dir . --target ${ENVIRONMENT}

    cd ..
    log_info "dbt models deployed successfully"
}

# Main deployment
main() {
    log_info "Starting deployment to ${ENVIRONMENT} environment..."
    log_info "Project: ${PROJECT_ID}"
    log_info "Region: ${REGION}"

    check_requirements

    # Parse arguments
    case "$1" in
        infra)
            deploy_infrastructure
            ;;
        api)
            deploy_api
            ;;
        dags)
            deploy_dags
            ;;
        dbt)
            deploy_dbt
            ;;
        all)
            deploy_infrastructure
            deploy_api
            deploy_dags
            deploy_dbt
            ;;
        *)
            echo "Usage: $0 {infra|api|dags|dbt|all}"
            echo
            echo "Commands:"
            echo "  infra  - Deploy Terraform infrastructure"
            echo "  api    - Build and deploy API to Cloud Run"
            echo "  dags   - Upload DAGs to Cloud Composer"
            echo "  dbt    - Run dbt models"
            echo "  all    - Deploy everything"
            exit 1
            ;;
    esac

    log_info "Deployment complete!"
}

main "$@"
