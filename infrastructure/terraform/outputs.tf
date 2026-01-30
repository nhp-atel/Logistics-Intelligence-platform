output "project_id" {
  description = "GCP project ID"
  value       = var.project_id
}

output "region" {
  description = "GCP region"
  value       = var.region
}

# BigQuery outputs
output "bigquery_datasets" {
  description = "BigQuery dataset IDs"
  value = {
    raw       = google_bigquery_dataset.raw.dataset_id
    staging   = google_bigquery_dataset.staging.dataset_id
    warehouse = google_bigquery_dataset.warehouse.dataset_id
    features  = google_bigquery_dataset.features.dataset_id
  }
}

# Cloud Storage outputs
output "storage_buckets" {
  description = "GCS bucket names"
  value = {
    raw_data       = google_storage_bucket.raw_data.name
    staging_data   = google_storage_bucket.staging_data.name
    processed_data = google_storage_bucket.processed_data.name
    airflow_dags   = google_storage_bucket.airflow_dags.name
  }
}

# Pub/Sub outputs
output "pubsub_topics" {
  description = "Pub/Sub topic names"
  value = {
    tracking_events = google_pubsub_topic.tracking_events.name
    data_quality    = google_pubsub_topic.data_quality_alerts.name
  }
}

output "pubsub_subscriptions" {
  description = "Pub/Sub subscription names"
  value = {
    tracking_events_bq = google_pubsub_subscription.tracking_events_bq.name
  }
}

# IAM outputs
output "service_accounts" {
  description = "Service account emails"
  value = {
    airflow     = google_service_account.airflow.email
    api         = google_service_account.api.email
    data_pipeline = google_service_account.data_pipeline.email
  }
}

# Cloud Run outputs
output "api_url" {
  description = "Cloud Run API URL"
  value       = google_cloud_run_v2_service.api.uri
}

# Composer outputs (conditional)
output "composer_airflow_uri" {
  description = "Cloud Composer Airflow web UI URI"
  value       = var.enable_composer ? google_composer_environment.main[0].config[0].airflow_uri : null
}

output "composer_dag_gcs_prefix" {
  description = "Cloud Composer DAG GCS prefix"
  value       = var.enable_composer ? google_composer_environment.main[0].config[0].dag_gcs_prefix : null
}
