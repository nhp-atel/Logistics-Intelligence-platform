# Service Accounts and IAM

# Airflow service account
resource "google_service_account" "airflow" {
  account_id   = "airflow-sa"
  display_name = "Airflow Service Account"
  description  = "Service account for Cloud Composer/Airflow"
}

# API service account
resource "google_service_account" "api" {
  account_id   = "api-sa"
  display_name = "API Service Account"
  description  = "Service account for Cloud Run API"
}

# Data pipeline service account
resource "google_service_account" "data_pipeline" {
  account_id   = "data-pipeline-sa"
  display_name = "Data Pipeline Service Account"
  description  = "Service account for data pipelines and Cloud Functions"
}

# Airflow IAM roles
resource "google_project_iam_member" "airflow_bigquery_admin" {
  project = var.project_id
  role    = "roles/bigquery.admin"
  member  = "serviceAccount:${google_service_account.airflow.email}"
}

resource "google_project_iam_member" "airflow_storage_admin" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.airflow.email}"
}

resource "google_project_iam_member" "airflow_pubsub_publisher" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.airflow.email}"
}

resource "google_project_iam_member" "airflow_composer_worker" {
  project = var.project_id
  role    = "roles/composer.worker"
  member  = "serviceAccount:${google_service_account.airflow.email}"
}

resource "google_project_iam_member" "airflow_logging_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.airflow.email}"
}

resource "google_project_iam_member" "airflow_monitoring_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.airflow.email}"
}

# API IAM roles
resource "google_project_iam_member" "api_bigquery_viewer" {
  project = var.project_id
  role    = "roles/bigquery.dataViewer"
  member  = "serviceAccount:${google_service_account.api.email}"
}

resource "google_project_iam_member" "api_bigquery_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.api.email}"
}

resource "google_project_iam_member" "api_logging_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.api.email}"
}

# Data pipeline IAM roles
resource "google_project_iam_member" "pipeline_bigquery_editor" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.data_pipeline.email}"
}

resource "google_project_iam_member" "pipeline_bigquery_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.data_pipeline.email}"
}

resource "google_project_iam_member" "pipeline_storage_object_admin" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.data_pipeline.email}"
}

resource "google_project_iam_member" "pipeline_pubsub_publisher" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.data_pipeline.email}"
}

resource "google_project_iam_member" "pipeline_pubsub_subscriber" {
  project = var.project_id
  role    = "roles/pubsub.subscriber"
  member  = "serviceAccount:${google_service_account.data_pipeline.email}"
}

resource "google_project_iam_member" "pipeline_logging_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.data_pipeline.email}"
}

# Service account key for local development (dev only)
resource "google_service_account_key" "data_pipeline_key" {
  count = var.environment == "dev" ? 1 : 0

  service_account_id = google_service_account.data_pipeline.name
}

# Output the key for local development
output "data_pipeline_sa_key" {
  description = "Service account key for local development (base64 encoded)"
  value       = var.environment == "dev" ? google_service_account_key.data_pipeline_key[0].private_key : null
  sensitive   = true
}
