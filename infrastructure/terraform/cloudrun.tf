# Cloud Run API Service

resource "google_cloud_run_v2_service" "api" {
  name     = "logistics-api"
  location = var.region

  labels = local.labels

  template {
    service_account = google_service_account.api.email

    scaling {
      min_instance_count = var.api_min_instances
      max_instance_count = var.api_max_instances
    }

    containers {
      image = "gcr.io/${var.project_id}/logistics-api:latest"

      ports {
        container_port = 8000
      }

      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }

      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }

      env {
        name  = "BQ_DATASET_WAREHOUSE"
        value = google_bigquery_dataset.warehouse.dataset_id
      }

      env {
        name  = "BQ_DATASET_FEATURES"
        value = google_bigquery_dataset.features.dataset_id
      }

      env {
        name = "API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.api_key.secret_id
            version = "latest"
          }
        }
      }

      resources {
        limits = {
          cpu    = "1000m"
          memory = "512Mi"
        }
        cpu_idle = true
      }

      startup_probe {
        http_get {
          path = "/health"
          port = 8000
        }
        initial_delay_seconds = 5
        timeout_seconds       = 3
        period_seconds        = 10
        failure_threshold     = 3
      }

      liveness_probe {
        http_get {
          path = "/health"
          port = 8000
        }
        initial_delay_seconds = 10
        timeout_seconds       = 3
        period_seconds        = 30
      }
    }

    timeout = "300s"
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  depends_on = [
    google_project_service.services,
    google_secret_manager_secret_version.api_key,
  ]
}

# Allow unauthenticated access (or configure IAM as needed)
resource "google_cloud_run_v2_service_iam_member" "api_public" {
  count = var.allowed_ingress == "all" ? 1 : 0

  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Secret Manager for API key
resource "google_secret_manager_secret" "api_key" {
  secret_id = "logistics-api-key"

  labels = local.labels

  replication {
    auto {}
  }

  depends_on = [google_project_service.services]
}

resource "google_secret_manager_secret_version" "api_key" {
  secret      = google_secret_manager_secret.api_key.id
  secret_data = var.environment == "prod" ? "" : "dev-api-key-${var.environment}"

  lifecycle {
    ignore_changes = [secret_data]
  }
}

# Grant API service account access to secret
resource "google_secret_manager_secret_iam_member" "api_secret_access" {
  secret_id = google_secret_manager_secret.api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.api.email}"
}

# Artifact Registry for container images
resource "google_artifact_registry_repository" "containers" {
  location      = var.region
  repository_id = "logistics-containers"
  description   = "Docker container images for logistics platform"
  format        = "DOCKER"

  labels = local.labels

  depends_on = [google_project_service.services]
}
