# Production Environment Configuration

project_id = "your-prod-project-id"
region     = "us-central1"
environment = "prod"

# BigQuery
bigquery_location = "US"

# Composer
enable_composer     = true
composer_node_count = 3

# Vertex AI Feature Store
enable_vertex_ai = true

# Cloud Run API
api_min_instances = 1
api_max_instances = 10

# Data retention
data_retention_days = 365

# Access
allowed_ingress = "internal-and-cloud-load-balancing"
