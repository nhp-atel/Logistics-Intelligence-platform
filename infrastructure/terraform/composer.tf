# Cloud Composer Environment (Managed Airflow)

resource "google_composer_environment" "main" {
  count = var.enable_composer ? 1 : 0

  name   = "logistics-composer-${var.environment}"
  region = var.region

  labels = local.labels

  config {
    software_config {
      image_version = "composer-2.5.0-airflow-2.6.3"

      airflow_config_overrides = {
        core-dags_are_paused_at_creation = "true"
        core-max_active_runs_per_dag     = "3"
        scheduler-dag_dir_list_interval  = "60"
      }

      pypi_packages = {
        dbt-bigquery         = ">=1.7.0"
        great-expectations   = ">=0.18.0"
        apache-airflow-providers-google = ">=10.0.0"
      }

      env_variables = {
        GCP_PROJECT_ID     = var.project_id
        ENVIRONMENT        = var.environment
        BQ_DATASET_RAW     = google_bigquery_dataset.raw.dataset_id
        BQ_DATASET_STAGING = google_bigquery_dataset.staging.dataset_id
        BQ_DATASET_WAREHOUSE = google_bigquery_dataset.warehouse.dataset_id
        BQ_DATASET_FEATURES = google_bigquery_dataset.features.dataset_id
        GCS_BUCKET_RAW     = google_storage_bucket.raw_data.name
        GCS_BUCKET_STAGING = google_storage_bucket.staging_data.name
        GCS_BUCKET_PROCESSED = google_storage_bucket.processed_data.name
      }
    }

    workloads_config {
      scheduler {
        cpu        = 0.5
        memory_gb  = 2
        storage_gb = 1
        count      = 1
      }
      web_server {
        cpu        = 0.5
        memory_gb  = 2
        storage_gb = 1
      }
      worker {
        cpu        = 1
        memory_gb  = 4
        storage_gb = 2
        min_count  = 1
        max_count  = 3
      }
    }

    environment_size = "ENVIRONMENT_SIZE_SMALL"

    node_config {
      service_account = google_service_account.airflow.email
    }
  }

  depends_on = [
    google_project_service.services,
    google_service_account.airflow,
  ]
}

# Output the DAGs bucket for Composer
output "composer_dags_bucket" {
  description = "Cloud Composer DAGs bucket"
  value       = var.enable_composer ? google_composer_environment.main[0].config[0].dag_gcs_prefix : null
}
