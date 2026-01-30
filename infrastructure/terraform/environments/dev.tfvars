# Development Environment Configuration

project_id = "your-dev-project-id"
region     = "us-central1"
environment = "dev"

# BigQuery
bigquery_location = "US"

# Composer (disabled for cost savings in dev)
enable_composer     = false
composer_node_count = 3

# Vertex AI Feature Store (disabled for cost savings)
enable_vertex_ai = false

# Cloud Run API
api_min_instances = 0
api_max_instances = 2

# Data retention
data_retention_days = 90

# Access
allowed_ingress = "all"
